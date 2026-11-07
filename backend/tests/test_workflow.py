"""Offline integration tests. Providers below are deliberate test doubles.

These tests verify orchestration and persistence; they are not evidence that
either assignment lesson has been generated or fact-checked by live providers.
"""
from __future__ import annotations

import copy
import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


SOURCE = {
    "id": "test-source",
    "title": "Synthetic integration-test source",
    "author": "Test fixture",
    "url": "https://example.org/fixture",
    "source_type": "website",
    "published_date": None,
    "description": "Test data, never a live research result.",
    "relevance": "Used to verify source reference persistence.",
    "excerpt": "A fixture supports deterministic workflow testing.",
    "evidence_kind": "snippet",
    "retrieved_at": "2026-01-01T00:00:00+00:00",
}
KINDS = ["overview", "objectives", "prerequisites", "introduction", "concepts", "examples", "applications", "activity", "knowledge_check", "summary"]
SECTIONS = [
    {"id": kind, "title": kind.replace("_", " ").title(), "kind": kind,
     "content": f"Synthetic {kind} content for persistence tests.", "minutes": 3,
     "source_ids": ["test-source"] if kind in ("concepts", "examples") else []}
    for kind in KINDS
]


def report(layer, sections):
    return {
        "overall_assessment": f"Synthetic {layer} assessment; test double only.",
        "alignment": "Test alignment" if layer == "instructional" else "Not an instructional evaluation",
        "limitations": ["Offline test fixture; no live verification."],
        "claims": [],
        "issues": [{
            "id": f"{layer}-issue", "severity": "Medium", "section_id": "concepts",
            "explanation": f"Synthetic {layer} issue.",
            "recommendation": "Review the proposed fixture correction.",
            "evidence_source_ids": ["test-source"] if layer == "research" else [],
            "proposed_content": f"Corrected by {layer} test recommendation.",
            "original_content": next(s["content"] for s in sections if s["id"] == "concepts"),
            "status": "pending",
        }],
    }


@pytest.fixture
def harness(tmp_path, monkeypatch):
    from app import database, main, workflow
    from app.schemas import Section

    engine = create_engine(f"sqlite:///{(tmp_path / 'workflow.sqlite3').as_posix()}", connect_args={"check_same_thread": False})
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", session_factory)
    # Workflows may keep an imported factory; patch it only when present.
    for module in (main, workflow):
        if hasattr(module, "SessionLocal"):
            monkeypatch.setattr(module, "SessionLocal", session_factory)
    calls = {"research": 0, "generation": 0, "research_audit": 0, "instructional_audit": 0}
    switches = {"fail_generation": False, "fail_research_qc": False}

    async def research(*args, **kwargs):
        calls["research"] += 1
        return {"sources": [copy.deepcopy(SOURCE)], "warnings": ["Synthetic partial provider warning"], "provider_status": {"web": "completed", "books": "failed", "youtube": "failed"}}

    async def generate(*args, **kwargs):
        calls["generation"] += 1
        if switches["fail_generation"]:
            raise RuntimeError("Simulated model failure")
        return [Section(**copy.deepcopy(s)) for s in SECTIONS]

    async def research_audit(title, objective, sections, sources, settings):
        calls["research_audit"] += 1
        if switches["fail_research_qc"]:
            raise RuntimeError("Simulated factual audit failure")
        return report("research", sections)

    async def instructional_audit(title, objective, sections, sources, settings):
        calls["instructional_audit"] += 1
        return report("instructional", sections)

    monkeypatch.setattr(workflow.research_service, "research", research)
    monkeypatch.setattr(workflow.lesson_generator, "generate", generate)
    monkeypatch.setattr(workflow.qc_research, "audit", research_audit)
    monkeypatch.setattr(workflow.qc_instructional, "audit", instructional_audit)
    with TestClient(main.app) as client:
        yield client, calls, switches
    engine.dispose()


def create(client):
    response = client.post("/api/lessons", json={"title": "Integration test lesson", "learning_objective": "Demonstrate reliable state persistence and review."})
    assert response.status_code == 201, response.text
    return response.json()


def run(client, lesson, stage="all"):
    response = client.post(f"/api/lessons/{lesson['id']}/run", json={"stage": stage})
    assert response.status_code == 202, response.text
    return client.get(f"/api/lessons/{lesson['id']}").json()


def generated(harness):
    client, _, _ = harness
    return run(client, create(client))


def test_input_validation_and_saved_draft(harness):
    client, calls, _ = harness
    for payload in ({"title": "", "learning_objective": ""}, {"title": "   ", "learning_objective": " "}, {"title": "Valid title", "learning_objective": "short"}):
        assert client.post("/api/lessons", json=payload).status_code == 422
    lesson = create(client)
    assert lesson["sections"] == []
    assert client.get(f"/api/lessons/{lesson['id']}").json()["title"] == lesson["title"]
    assert len(client.get("/api/lessons").json()) == 1
    assert sum(calls.values()) == 0


def test_full_pipeline_persists_distinct_audits(harness):
    client, calls, _ = harness
    lesson = generated(harness)
    assert lesson["status"] == "review"
    assert lesson["total_minutes"] == 30
    assert lesson["sources"][0]["id"] == "test-source"
    assert lesson["research_warnings"]
    assert lesson["reports"]["research"]["overall_assessment"] != lesson["reports"]["instructional"]["overall_assessment"]
    assert all(value == 1 for value in calls.values())
    assert client.get(f"/api/lessons/{lesson['id']}/versions").json()


def test_retry_generation_preserves_successful_research(harness):
    client, calls, switches = harness
    switches["fail_generation"] = True
    failed = run(client, create(client))
    assert failed["status"] == "error"
    assert failed["sources"]
    assert failed["stages"]["research"]["status"] == "completed"
    assert failed["stages"]["generation"]["status"] == "failed"
    switches["fail_generation"] = False
    retried = run(client, failed)
    assert retried["status"] == "review"
    assert calls["research"] == 1
    assert calls["generation"] == 2


def test_qc_layers_run_independently_and_preserve_content(harness):
    client, calls, _ = harness
    lesson = generated(harness)
    original = copy.deepcopy(lesson["sections"])
    rerun = run(client, lesson, "qc_research")
    assert calls["research_audit"] == 2
    assert calls["instructional_audit"] == 1
    assert rerun["sections"] == original
    run(client, rerun, "qc_instructional")
    assert calls["research_audit"] == 2
    assert calls["instructional_audit"] == 2


def test_qc_failure_does_not_destroy_successful_other_layer(harness):
    client, _, switches = harness
    lesson = generated(harness)
    preserved = lesson["reports"]["instructional"]
    switches["fail_research_qc"] = True
    failed = run(client, lesson, "qc_research")
    assert failed["status"] == "error"
    assert failed["sections"] == lesson["sections"]
    assert failed["reports"]["instructional"] == preserved
    switches["fail_research_qc"] = False
    assert run(client, failed, "qc_research")["status"] == "review"


def test_manual_edit_save_stales_audits_and_rejects_lost_updates(harness):
    client, _, _ = harness
    lesson = generated(harness)
    edited = copy.deepcopy(lesson["sections"])
    edited[0]["content"] = "Instructor's deliberate manual edit."
    response = client.patch(f"/api/lessons/{lesson['id']}", json={"expected_version": lesson["version"], "sections": edited})
    assert response.status_code == 200, response.text
    saved = response.json()
    assert saved["version"] > lesson["version"]
    assert all(saved["reports"][layer]["stale"] for layer in ("research", "instructional"))
    assert client.patch(f"/api/lessons/{lesson['id']}", json={"expected_version": lesson["version"], "sections": lesson["sections"]}).status_code == 409
    assert client.get(f"/api/lessons/{lesson['id']}").json()["sections"][0]["content"] == edited[0]["content"]


def test_time_limit_duplicate_sections_and_unknown_citations(harness):
    client, _, _ = harness
    lesson = generated(harness)
    overlong = copy.deepcopy(lesson["sections"])
    overlong[0]["minutes"] = 45
    assert client.patch(f"/api/lessons/{lesson['id']}", json={"expected_version": lesson["version"], "sections": overlong}).status_code == 422
    duplicate = copy.deepcopy(lesson["sections"])
    duplicate[1]["id"] = duplicate[0]["id"]
    assert client.patch(f"/api/lessons/{lesson['id']}", json={"expected_version": lesson["version"], "sections": duplicate}).status_code == 422
    unknown = copy.deepcopy(lesson["sections"])
    unknown[0]["source_ids"] = ["invented-source"]
    assert client.patch(f"/api/lessons/{lesson['id']}", json={"expected_version": lesson["version"], "sections": unknown}).status_code == 422


def test_apply_recommendation_is_versioned_and_not_repeatable(harness):
    client, _, _ = harness
    lesson = generated(harness)
    issue = lesson["reports"]["research"]["issues"][0]
    url = f"/api/lessons/{lesson['id']}/recommendations/research/{issue['id']}"
    response = client.post(url, json={"action": "apply", "expected_version": lesson["version"]})
    assert response.status_code == 200, response.text
    updated = response.json()
    assert next(s for s in updated["sections"] if s["id"] == "concepts")["content"] == issue["proposed_content"]
    assert updated["version"] > lesson["version"]
    assert updated["reports"]["research"]["issues"][0]["status"] == "applied"
    assert client.post(url, json={"action": "apply", "expected_version": updated["version"]}).status_code == 409


def test_reject_recommendation_does_not_edit_content(harness):
    client, _, _ = harness
    lesson = generated(harness)
    issue = lesson["reports"]["instructional"]["issues"][0]
    response = client.post(f"/api/lessons/{lesson['id']}/recommendations/instructional/{issue['id']}", json={"action": "reject", "expected_version": lesson["version"]})
    assert response.status_code == 200
    assert response.json()["sections"] == lesson["sections"]
    assert response.json()["reports"]["instructional"]["issues"][0]["status"] == "rejected"


def test_stale_recommendation_cannot_overwrite_instructor_edit(harness):
    client, _, _ = harness
    lesson = generated(harness)
    issue = lesson["reports"]["research"]["issues"][0]
    edited = copy.deepcopy(lesson["sections"])
    next(s for s in edited if s["id"] == "concepts")["content"] = "Human corrected this section."
    saved = client.patch(f"/api/lessons/{lesson['id']}", json={"expected_version": lesson["version"], "sections": edited}).json()
    assert client.post(f"/api/lessons/{lesson['id']}/recommendations/research/{issue['id']}", json={"action": "apply", "expected_version": saved["version"]}).status_code == 409
    assert client.get(f"/api/lessons/{lesson['id']}").json()["sections"] == edited


def test_versions_restore_previous_content_as_new_version(harness):
    client, _, _ = harness
    lesson = generated(harness)
    versions = client.get(f"/api/lessons/{lesson['id']}/versions").json()
    original = next(v for v in versions if v["sections"] == lesson["sections"])
    edited = copy.deepcopy(lesson["sections"])
    edited[0]["content"] = "Temporary manual edit."
    saved = client.patch(f"/api/lessons/{lesson['id']}", json={"expected_version": lesson["version"], "sections": edited}).json()
    response = client.post(f"/api/lessons/{lesson['id']}/restore/{original['id']}", json={"expected_version": saved["version"]})
    assert response.status_code == 200, response.text
    assert response.json()["sections"] == lesson["sections"]
    assert response.json()["version"] > saved["version"]


def test_exports_have_real_download_content_and_reports(harness):
    client, _, _ = harness
    lesson = generated(harness)
    url = f"/api/lessons/{lesson['id']}/export"
    pdf = client.get(url, params={"format": "pdf", "scope": "lesson"})
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    md = client.get(url, params={"format": "markdown", "scope": "lesson"})
    assert md.status_code == 200 and lesson["title"] in md.text
    data = client.get(url, params={"format": "json", "scope": "lesson"})
    assert data.status_code == 200 and data.json()["title"] == lesson["title"]
    for layer in ("research", "instructional"):
        audit = client.get(url, params={"format": "json", "scope": layer})
        assert audit.status_code == 200
        assert layer in json.dumps(audit.json())
    package = client.get(url, params={"format": "zip", "scope": "package"})
    assert package.status_code == 200
    with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
        names = archive.namelist()
        assert any(name.endswith(".pdf") for name in names)
        assert any(name.endswith(".md") for name in names)
        assert any("research" in name for name in names)
        assert any("instructional" in name for name in names)


def test_generation_retry_never_silently_replaces_existing_lesson(harness):
    client, calls, _ = harness
    lesson = generated(harness)
    edited = copy.deepcopy(lesson["sections"])
    edited[0]["content"] = "Keep this instructor edit across retries."
    saved = client.patch(f"/api/lessons/{lesson['id']}", json={"expected_version": lesson["version"], "sections": edited}).json()
    response = client.post(f"/api/lessons/{lesson['id']}/run", json={"stage": "generation"})
    assert response.status_code in (202, 409)
    assert client.get(f"/api/lessons/{lesson['id']}").json()["sections"] == saved["sections"]
    assert calls["generation"] == 1


def test_starting_job_cannot_overwrite_a_concurrent_manual_save(harness, monkeypatch):
    """Insert a real committed edit between the run endpoint's read and update."""
    from app import database, main
    from app.models import Lesson

    client, _, _ = harness
    lesson = generated(harness)
    original_update = main.update
    edited = copy.deepcopy(lesson["sections"])
    edited[0]["content"] = "An instructor saved this while another tab started QC."
    inserted = False

    def update_after_concurrent_save(*args, **kwargs):
        nonlocal inserted
        if not inserted:
            inserted = True
            with database.SessionLocal() as session:
                stored = session.get(Lesson, lesson["id"])
                main.save_content(session, stored, edited, "Concurrent instructor save")
                session.commit()
        return original_update(*args, **kwargs)

    monkeypatch.setattr(main, "update", update_after_concurrent_save)
    response = client.post(f"/api/lessons/{lesson['id']}/run", json={"stage": "qc_both"})
    assert response.status_code == 409, response.text
    latest = client.get(f"/api/lessons/{lesson['id']}").json()
    assert latest["sections"] == edited
    assert latest["status"] == "review"
