"""Offline contract tests with synthetic provider data, never live lesson evidence."""
import asyncio
import json
from types import SimpleNamespace
import httpx
import pytest
from app.schemas import LessonContent
from app.services import llm_service, research_service, lesson_generator, qc_research, qc_instructional
from app.services.audit_common import AuditOutput
from app.services.errors import ServiceError
from app.services.http_client import request_json
from app.services.citations import validate_references


@pytest.fixture
def settings():
    return SimpleNamespace(llm_provider="gemini", gemini_api_key="test-key-not-real", gemini_model="gemini-2.5-flash",
        openai_api_key="test-key-not-real", openai_model="gpt-4o-mini", tavily_api_key="test-key-not-real",
        youtube_api_key="test-key-not-real", google_books_api_key="", request_timeout=1, llm_timeout=1, max_sources_per_provider=3)


@pytest.fixture
def evidence():
    return {"id": "website-abcdef123456", "title": "Test evidence", "url": "https://example.edu/topic", "source_type": "website",
            "author": "Fixture", "description": "Synthetic provider fixture", "excerpt": "A widget has a documented property for this synthetic test.", "evidence_kind": "full_text"}


@pytest.fixture
def sections(evidence):
    return [{"id": kind, "title": kind.title(), "kind": kind, "content": f"Synthetic teaching material [{evidence['id']}]", "minutes": 4, "source_ids": [evidence["id"]]} for kind in sorted(lesson_generator.REQUIRED_KINDS)]


def audit_output(**updates):
    values = {"overall_assessment": "Synthetic audit", "alignment": "Aligned to test objective", "limitations": [], "issues": [], "claims": []}
    values.update(updates)
    return AuditOutput.model_validate(values)


def test_strict_schema_requires_fields_without_mutating_model():
    schema = llm_service.strict_schema(LessonContent)
    section = schema["$defs"]["Section"]
    assert section["additionalProperties"] is False
    assert set(section["required"]) == set(section["properties"])
    assert "default" not in section["properties"]["source_ids"]


def test_gemini_schema_preserves_fields_and_local_constraints():
    schema = llm_service.gemini_schema(LessonContent)
    section = schema["$defs"]["Section"]
    assert "title" in section["properties"]
    assert set(section["required"]) == set(section["properties"])
    assert "maxLength" not in section["properties"]["content"]
    assert LessonContent.model_json_schema()["$defs"]["Section"]["properties"]["content"]["maxLength"] == 20000
    with pytest.raises(ValueError):
        LessonContent(sections=[{"id":"x","title":"x","kind":"overview","content":"x","minutes":46,"source_ids":[]}])


@pytest.mark.asyncio
async def test_missing_credentials_stop_before_network(settings, monkeypatch):
    settings.gemini_api_key = ""
    async def forbidden(*args, **kwargs):
        pytest.fail("Network should not be reached")
    monkeypatch.setattr(llm_service, "request_json", forbidden)
    with pytest.raises(ServiceError, match="GEMINI_API_KEY"):
        await llm_service.complete("test", {}, LessonContent, settings)


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["gemini", "openai"])
async def test_llm_provider_request_contract(settings, sections, monkeypatch, provider):
    settings.llm_provider = provider
    seen = []
    async def fake(client, method, url, **kwargs):
        seen.append((url, kwargs))
        content = json.dumps({"sections": sections})
        if provider == "openai":
            return {"choices": [{"finish_reason": "stop", "message": {"content": content}}]}
        return {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": content}]}}]}
    monkeypatch.setattr(llm_service, "request_json", fake)
    output = await llm_service.complete("System", {"sources": []}, LessonContent, settings)
    assert len(output.sections) == 10
    body = seen[0][1]["json"]
    if provider == "openai":
        assert body["response_format"]["json_schema"]["strict"] is True
    else:
        assert body["generationConfig"]["responseMimeType"] == "application/json"
        assert "responseJsonSchema" in body["generationConfig"]


@pytest.mark.asyncio
async def test_invalid_json_retries_and_fails_safely(settings, monkeypatch):
    calls = []
    async def fake(*args, **kwargs):
        calls.append(1)
        return {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "not-json"}]}}]}
    monkeypatch.setattr(llm_service, "request_json", fake)
    with pytest.raises(ServiceError, match="invalid structured"):
        await llm_service.complete("test", {}, LessonContent, settings)
    assert len(calls) == 3


def test_correction_hint_names_the_failed_bound(settings):
    """A failed attempt must tell the model exactly what to fix, not just 'try again'."""
    from pydantic import ValidationError
    try:
        LessonContent(sections=[{"id": "x", "title": "x", "kind": "overview", "content": "x", "minutes": 46, "source_ids": []}])
    except ValidationError as exc:
        hint = llm_service.correction_hint(exc)
    assert "45 minutes" in hint
    assert "at most 45" in hint


@pytest.mark.asyncio
async def test_retry_receives_targeted_correction_and_recovers(settings, sections, monkeypatch):
    """First response exceeds 45 minutes; the targeted hint lets attempt two succeed."""
    settings.llm_provider = "openai"
    seen_prompts = []
    too_long = [dict(s, minutes=8) for s in sections]  # 10 * 8 = 80 minutes
    async def fake(client, method, url, **kwargs):
        seen_prompts.append(kwargs["json"]["messages"][1]["content"])
        content = json.dumps({"sections": too_long if len(seen_prompts) == 1 else sections})
        return {"choices": [{"finish_reason": "stop", "message": {"content": content, "refusal": None}}]}
    monkeypatch.setattr(llm_service, "request_json", fake)
    output = await llm_service.complete("System", {"title": "t"}, LessonContent, settings)
    assert len(output.sections) == 10
    assert "45 minutes" in seen_prompts[1]


def test_rebalance_minutes_fits_budget_without_touching_content():
    from app.services.lesson_generator import rebalance_minutes
    payload = {"sections": [
        {"id": "a", "content": "keep-me", "minutes": 10},
        {"id": "b", "content": "keep-me", "minutes": 10},
        {"id": "c", "content": "keep-me", "minutes": 10},
        {"id": "d", "content": "keep-me", "minutes": 10},
        {"id": "e", "content": "keep-me", "minutes": 10},
    ]}
    rebalance_minutes(payload)
    total = sum(s["minutes"] for s in payload["sections"])
    assert total <= 45
    assert all(isinstance(s["minutes"], int) and s["minutes"] >= 1 for s in payload["sections"])
    assert all(s["content"] == "keep-me" for s in payload["sections"])


def test_rebalance_minutes_leaves_compliant_lesson_unchanged():
    from app.services.lesson_generator import rebalance_minutes
    payload = {"sections": [{"id": "a", "minutes": 5}, {"id": "b", "minutes": 5}]}
    rebalance_minutes(payload)
    assert [s["minutes"] for s in payload["sections"]] == [5, 5]


@pytest.mark.asyncio
async def test_blocked_gemini_response_is_safe(settings, monkeypatch):
    async def fake(*args, **kwargs):
        return {"promptFeedback": {"blockReason": "SAFETY"}}
    monkeypatch.setattr(llm_service, "request_json", fake)
    with pytest.raises(ServiceError, match="incomplete or blocked"):
        await llm_service.complete("test", {}, LessonContent, settings)


@pytest.mark.asyncio
async def test_http_403_does_not_expose_secret():
    def handler(request):
        return httpx.Response(403, json={"secret": "must-never-be-shown"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ServiceError) as error:
            await request_json(client, "GET", "https://example.com?key=secret", provider="Test")
    assert "must-never" not in str(error.value)
    assert "secret" not in str(error.value)


@pytest.mark.asyncio
async def test_transient_provider_failure_is_retried_once(monkeypatch):
    calls = []
    def handler(request):
        calls.append(1)
        return httpx.Response(503 if len(calls) == 1 else 200, json={"ok": True})
    async def no_delay(seconds):
        pass
    monkeypatch.setattr(asyncio, "sleep", no_delay)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await request_json(client, "GET", "https://example.com", provider="Test")
    assert result["ok"] and len(calls) == 2


def test_research_urls_and_rank_deduplicate_and_drop_irrelevant():
    first = research_service.source("website", title="Widgets guide", author="Teacher", url="https://example.edu/widgets?utm_source=x#part", description="Widget documentation", excerpt="Widget", evidence_kind="snippet")
    duplicate = dict(first)
    unrelated = research_service.source("website", title="Bananas", author="Farmer", url="https://example.org/fruit", description="Fruit")
    assert first["url"] == "https://example.edu/widgets"
    assert research_service.canonical_url("javascript:alert(1)") is None
    assert research_service.canonical_url("https://name:password@example.com/") is None
    result = research_service.rank_sources([first, duplicate, unrelated], "Widgets", "Explain widgets", 5)
    assert len(result) == 1
    assert "heuristic" in result[0]["relevance"]


@pytest.mark.asyncio
async def test_partial_research_preserves_successes(settings, monkeypatch):
    async def web(*args):
        raise ServiceError("Website search unavailable")
    async def books(*args):
        return [research_service.source("book", title="Widget Book", author="Writer", url="https://books.google.com/books?id=real-test-id", description="Widgets explained")]
    async def youtube(*args):
        raise ServiceError("YouTube unavailable")
    monkeypatch.setattr(research_service, "search_web", web)
    monkeypatch.setattr(research_service, "search_books", books)
    monkeypatch.setattr(research_service, "search_youtube", youtube)
    result = await research_service.research("Widget", "Explain widgets", settings)
    assert len(result["sources"]) == 1
    assert result["provider_status"]["web"]["status"] == "error"
    assert result["sources"][0]["evidence_kind"] == "metadata"
    assert any("not been read" in warning for warning in result["warnings"])


@pytest.mark.asyncio
async def test_google_books_only_returns_retrieved_metadata(settings, monkeypatch):
    async def fake(*args, **kwargs):
        assert "key" not in kwargs["params"]
        return {"items": [{"volumeInfo": {"title": "Widget Book", "authors": ["Actual Author"], "publishedDate": "2020", "infoLink": "https://books.google.com/books?id=abc", "description": "<b>Widgets</b> explained"}}]}
    monkeypatch.setattr(research_service, "request_json", fake)
    results = await research_service.search_books(None, "Widget", "Explain widgets", settings)
    assert results[0]["author"] == "Actual Author"
    assert results[0]["excerpt"] == ""
    assert results[0]["evidence_kind"] == "metadata"


@pytest.mark.asyncio
async def test_youtube_uses_search_ids_and_metadata(settings, monkeypatch):
    async def fake(*args, **kwargs):
        assert kwargs["params"]["type"] == "video"
        return {"items": [{"id": {"videoId": "abcdef12345"}, "snippet": {"title": "Widget lesson", "channelTitle": "Channel", "description": "Learn widgets", "publishedAt": "2020-01-01T00:00:00Z"}}, {"id": {"videoId": "bad"}, "snippet": {}}]}
    monkeypatch.setattr(research_service, "request_json", fake)
    results = await research_service.search_youtube(None, "Widget", "Explain widgets", settings)
    assert len(results) == 1 and results[0]["url"].endswith("v=abcdef12345")
    assert results[0]["excerpt"] == ""


@pytest.mark.asyncio
async def test_generation_refuses_metadata_only(settings):
    with pytest.raises(ServiceError, match="website text"):
        await lesson_generator.generate("Title", "Explain widgets", [{"evidence_kind": "metadata"}], settings)


def test_generated_lesson_semantic_gates(evidence, sections):
    result = lesson_generator.validate_generation({"sections": sections}, [evidence])
    assert len(result.sections) == 10
    # The reference list is reconciled to usable cited/declared sources, so an
    # uncited or metadata-only declaration can never appear as a reference.
    concepts = next(s for s in result.sections if s.kind == "concepts")
    assert concepts.source_ids == [evidence["id"]]
    with pytest.raises(ValueError, match="Missing required"):
        lesson_generator.validate_generation({"sections": sections[:1]}, [evidence])
    # A fabricated declared id is dropped from the reconciled references (the real
    # inline citation the fixture already contains remains), but a fabricated inline
    # citation is rejected outright by validate_references.
    sections[0]["source_ids"] = ["invented-source"]
    assert lesson_generator.validate_generation({"sections": sections}, [evidence]).sections[0].source_ids == [evidence["id"]]
    sections[0]["content"] = "Teaching claim [invented-source]"
    with pytest.raises(ValueError, match="unknown inline citation"):
        lesson_generator.validate_generation({"sections": sections}, [evidence])


def test_normalize_sections_drops_duplicate_kinds_and_orders_them(evidence):
    sid = evidence["id"]
    kinds = ["overview", "objectives", "prerequisites", "introduction", "concepts", "examples",
             "applications", "activity", "knowledge_check", "summary"]
    sections = [{"id": f"s-{k}", "title": k.title(), "kind": k, "content": f"{k.title()} [{sid}]", "minutes": 2, "source_ids": []} for k in kinds]
    # A duplicated summary plus a duplicate overview, and out-of-order placement.
    sections.append({"id": "dup", "title": "Summary again", "kind": "summary", "content": f"Duplicate [{sid}]", "minutes": 1, "source_ids": []})
    result = lesson_generator.validate_generation({"sections": sections}, [evidence])
    result_kinds = [s.kind for s in result.sections]
    assert result_kinds == kinds  # one of each, canonical order, duplicate dropped
    assert next(s for s in result.sections if s.kind == "summary").content == f"Summary [{sid}]"


def test_generated_lesson_ignores_metadata_only_citations(evidence, sections):
    metadata = {"id": "book-metadata", "title": "A book", "url": "https://books.example/1", "source_type": "book",
                "description": "Discovery metadata", "excerpt": "", "evidence_kind": "metadata"}
    for section in sections:
        section["content"] = "Teaching material [book-metadata]"
        section["source_ids"] = ["book-metadata"]
    # The only supplied source is metadata-only, so no usable citation remains.
    with pytest.raises(ValueError, match="no traceable source citations"):
        lesson_generator.validate_generation({"sections": sections}, [metadata])


def test_generated_lesson_rejects_over_45_minutes(evidence, sections):
    sections[0]["minutes"] = 20
    with pytest.raises(ValueError, match="45 minutes"):
        lesson_generator.validate_generation({"sections": sections}, [evidence])


@pytest.mark.parametrize("content", ["A claim [invented-id]", "A claim [123]", "[Reference](https://invented.example/book)", "Reference: https://invented.example/book", "[Click](javascript:alert)"])
def test_unknown_inline_citations_and_urls_are_rejected(evidence, content):
    with pytest.raises(ValueError):
        validate_references(content, [evidence])


def test_example_addresses_in_code_are_not_treated_as_references(evidence):
    validate_references("Try `https://api.example.com` then:\n```python\na[1]\n```\n[Reference](https://example.edu/topic)", [evidence])


@pytest.mark.asyncio
async def test_generation_retries_semantically_invalid_output(settings, evidence, sections, monkeypatch):
    calls = []
    async def fake(*args, **kwargs):
        calls.append(args[1])
        return LessonContent.model_validate({"sections": sections[:1] if len(calls) == 1 else sections})
    monkeypatch.setattr(llm_service, "complete", fake)
    generated = await lesson_generator.generate("Widgets", "Explain widgets", [evidence], settings)
    assert len(calls) == 2 and len(generated) == 10


@pytest.mark.asyncio
async def test_factual_qc_cannot_verify_model_claim_even_with_matching_quote(settings, evidence, sections, monkeypatch):
    async def fake(*args):
        return audit_output(claims=[{"section_id": "concepts", "claim": "A widget has a documented property", "status": "verified", "source_ids": [evidence["id"]], "evidence_quote": evidence["excerpt"], "explanation": "The model says so"}])
    monkeypatch.setattr(llm_service, "complete", fake)
    report = await qc_research.audit("Widgets", "Explain widgets", sections, [evidence], settings)
    assert report["claims"][0]["status"] == "uncertain"
    assert "textual presence" in " ".join(report["limitations"])
    assert "independently verified" in report["overall_assessment"]


@pytest.mark.asyncio
async def test_factual_qc_discards_invented_quote(settings, evidence, sections, monkeypatch):
    async def fake(*args):
        return audit_output(claims=[{"section_id": "concepts", "claim": "A test claim", "status": "verified", "source_ids": [evidence["id"]], "evidence_quote": "Completely fabricated quotation", "explanation": "Testing"}])
    monkeypatch.setattr(llm_service, "complete", fake)
    report = await qc_research.audit("Widgets", "Explain widgets", sections, [evidence], settings)
    assert report["claims"][0]["status"] != "verified"
    assert report["claims"][0]["evidence_quote"] == ""


@pytest.mark.asyncio
async def test_instructional_qc_is_independent_and_flags_pacing(settings, evidence, sections, monkeypatch):
    seen = []
    async def fake(system, payload, *args):
        seen.append((system, payload))
        return audit_output()
    monkeypatch.setattr(llm_service, "complete", fake)
    sections[0]["content"] = "word " * 1000
    sections[0]["minutes"] = 1
    report = await qc_instructional.audit("Widgets", "Explain widgets", sections, [evidence], settings)
    assert "QC Layer 2" in seen[0][0]
    assert "sources" not in seen[0][1] and "reports" not in seen[0][1]
    assert report["claims"] == []
    assert any("180 words/minute" in value["explanation"] for value in report["issues"])


@pytest.mark.asyncio
async def test_audit_rejects_invented_sources(settings, evidence, sections, monkeypatch):
    async def fake(*args):
        return audit_output(issues=[{"severity": "High", "section_id": "concepts", "explanation": "Test", "recommendation": "Test", "evidence_source_ids": ["invented"], "proposed_content": None}])
    monkeypatch.setattr(llm_service, "complete", fake)
    with pytest.raises(ServiceError, match="not retrieved"):
        await qc_research.audit("Widgets", "Explain widgets", sections, [evidence], settings)
