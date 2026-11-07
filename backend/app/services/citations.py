"""Constrain generated references to actual retrieved sources.

Illustrative addresses inside code blocks/inline code are not bibliography claims.
Outside code, generated links must match a retrieved source URL.
"""
import re
from .research_service import canonical_url


def validate_references(content, sources):
    known_ids = {s["id"] for s in sources}
    known_urls = {canonical_url(s["url"]) for s in sources}
    prose = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
    prose = re.sub(r"`[^`]*`", "", prose)
    links = re.findall(r"\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", prose)
    for url in links:
        if canonical_url(url.strip("<>")) not in known_urls:
            raise ValueError("Generated content contains a link that was not retrieved")
    for url in re.findall(r"https?://[^\s<>\])]+", prose):
        if canonical_url(url.rstrip(".,;:!?")) not in known_urls:
            raise ValueError("Generated content contains an address that was not retrieved; illustrative addresses must be in code")
    without_links = re.sub(r"\[[^\]]*\]\([^)]*\)", "", prose)
    references = set(re.findall(r"\[([^\[\]\s]{1,120})\]", without_links))
    if references - known_ids:
        raise ValueError("Generated content contains an unknown inline citation")
    return references
