"""Real research adapters. Book/video descriptions are metadata, not read content."""
import asyncio
import hashlib
import html
import re
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import httpx
from .errors import ServiceError
from .http_client import request_json

STOPWORDS = {"a", "an", "the", "and", "or", "in", "of", "to", "with", "for", "explain", "demonstrate", "identify", "understand", "learning", "lesson", "between", "through", "their", "each", "where", "what", "how", "that", "this", "are", "is", "be"}


def text(value, limit=5000):
    return html.unescape(re.sub(r"<[^>]+>", " ", str(value or ""))).strip()[:limit]


def canonical_url(url):
    try:
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
            return None
        query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")]
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/") or "/", urlencode(query), ""))
    except (ValueError, TypeError):
        return None


def keywords(value):
    return {word for word in re.findall(r"[a-z0-9+#]+", value.lower()) if len(word) > 1 and word not in STOPWORDS}


def source(kind, *, title, author, url, description, published_date=None, excerpt="", evidence_kind="metadata"):
    url = canonical_url(url)
    if not url or not text(title):
        return None
    return {"id": f"{kind}-{hashlib.sha256(url.encode()).hexdigest()[:12]}", "title": text(title, 400),
            "author": text(author, 300) or "Not supplied", "url": url, "source_type": kind,
            "published_date": text(published_date, 80) or None, "description": text(description, 2500),
            "relevance": "", "excerpt": text(excerpt, 14000), "evidence_kind": evidence_kind,
            "retrieved_at": datetime.now(timezone.utc).isoformat()}


async def search_web(client, title, objective, settings):
    if not settings.tavily_api_key:
        raise ServiceError("Website search unavailable: set TAVILY_API_KEY in backend/.env.")
    data = await request_json(client, "POST", "https://api.tavily.com/search", provider="Tavily",
        headers={"Authorization": f"Bearer {settings.tavily_api_key}"},
        json={"query": f"{title}: {objective[:400]} educational reference official documentation", "search_depth": "advanced",
              "max_results": min(settings.max_sources_per_provider * 2, 10), "include_raw_content": True, "include_answer": False})
    results = []
    for item in data.get("results", []):
        url = item.get("url", "")
        raw = item.get("raw_content")
        item_source = source("website", title=item.get("title"), author=urlsplit(url).hostname,
            url=url, description=item.get("content"), published_date=item.get("published_date"),
            excerpt=raw or item.get("content", ""), evidence_kind="full_text" if raw else "snippet")
        if item_source:
            results.append(item_source)
    return results


async def search_books(client, title, objective, settings):
    params = {"q": title, "printType": "books", "langRestrict": "en", "orderBy": "relevance", "maxResults": min(settings.max_sources_per_provider * 2, 20)}
    if settings.google_books_api_key:
        params["key"] = settings.google_books_api_key
    data = await request_json(client, "GET", "https://www.googleapis.com/books/v1/volumes", provider="Google Books", params=params)
    results = []
    for item in data.get("items", []):
        info = item.get("volumeInfo", {})
        item_source = source("book", title=info.get("title"), author=", ".join(info.get("authors", [])) or info.get("publisher"),
            url=info.get("infoLink") or info.get("previewLink"), description=info.get("description"), published_date=info.get("publishedDate"))
        if item_source:
            results.append(item_source)
    return results


async def search_youtube(client, title, objective, settings):
    if not settings.youtube_api_key:
        raise ServiceError("YouTube discovery unavailable: set YOUTUBE_API_KEY and enable YouTube Data API v3.")
    data = await request_json(client, "GET", "https://www.googleapis.com/youtube/v3/search", provider="YouTube",
        params={"key": settings.youtube_api_key, "part": "snippet", "type": "video", "q": f"{title} tutorial",
                "maxResults": min(settings.max_sources_per_provider * 2, 10), "relevanceLanguage": "en", "safeSearch": "strict", "videoEmbeddable": "true"})
    results = []
    for item in data.get("items", []):
        info = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            continue
        item_source = source("youtube", title=info.get("title"), author=info.get("channelTitle"),
            url=f"https://www.youtube.com/watch?v={video_id}", description=info.get("description"), published_date=info.get("publishedAt"))
        if item_source:
            results.append(item_source)
    return results


def rank_sources(results, title, objective, limit):
    terms = keywords(f"{title} {objective}")
    title_terms = keywords(title)
    ranked, seen = [], set()
    for item in results:
        if item["url"] in seen:
            continue
        matches = terms & keywords(item["title"] + " " + item["description"] + " " + item["excerpt"][:1000])
        if terms and not matches:
            continue
        seen.add(item["url"])
        hostname = urlsplit(item["url"]).hostname or ""
        education_hint = hostname.endswith(".edu") or hostname.endswith(".gov") or any(hostname == d or hostname.endswith("." + d) for d in ("w3.org", "ietf.org", "rfc-editor.org", "developer.mozilla.org", "docs.oracle.com", "docs.python.org", "dev.java"))
        score = len(matches) + 2 * len(title_terms & keywords(item["title"])) + int(education_hint)
        item["relevance"] = "Search match: " + ", ".join(sorted(matches)[:10]) + ". Relevance is a keyword heuristic; instructor review required."
        ranked.append((score, item))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in ranked[:limit]]


async def research(title, objective, settings):
    names = ["web", "books", "youtube"]
    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        outcomes = await asyncio.gather(search_web(client, title, objective, settings), search_books(client, title, objective, settings), search_youtube(client, title, objective, settings), return_exceptions=True)
    sources, warnings, statuses = [], [], {}
    for name, outcome in zip(names, outcomes):
        if isinstance(outcome, Exception):
            message = str(outcome) if isinstance(outcome, ServiceError) else f"{name.title()} returned unexpected data. Retry research."
            warnings.append(message)
            statuses[name] = {"status": "error", "count": 0, "error": message}
            continue
        selected = rank_sources(outcome, title, objective, settings.max_sources_per_provider)
        sources.extend(selected)
        statuses[name] = {"status": "complete" if selected else "empty", "count": len(selected), "error": None}
        if not selected:
            warnings.append(f"No relevant {name} results were retrieved. Try a more specific lesson title or retry research.")
    if any(s["source_type"] in ("book", "youtube") for s in sources):
        warnings.append("Books and YouTube results contain discovery metadata only. Full books and video transcripts have not been read or verified.")
    if any(s["evidence_kind"] == "snippet" for s in sources):
        warnings.append("Some website evidence is limited to search snippets; complete page text was unavailable.")
    return {"sources": sources, "warnings": warnings, "provider_status": statuses}
