"""Durable stage boundaries, small DB transactions, and independent audit execution."""
import copy
import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from . import database
from .config import get_settings
from .models import Lesson, LessonVersion, AuditHistory
from .schemas import LessonContent, Section
from .services import research_service, lesson_generator, qc_research, qc_instructional
from .services.errors import ServiceError

log = logging.getLogger(__name__)
STAGES = ("research", "generation", "qc_research", "qc_instructional")


def now():
    return datetime.now(timezone.utc).isoformat()


def initial_data():
    return {"sections": [], "sources": [], "research_warnings": [], "provider_status": {},
            "stages": {name: {"status": "pending", "error": None} for name in STAGES},
            "reports": {"research": None, "instructional": None}, "activity": []}


def activity(data, message):
    data["activity"] = ([{"at": now(), "message": message}] + data.get("activity", []))[:100]


def serialize(lesson):
    result = {"id": lesson.id, "title": lesson.title, "learning_objective": lesson.learning_objective,
              "version": lesson.version, "status": lesson.status, "created_at": lesson.created_at,
              "updated_at": lesson.updated_at, **copy.deepcopy(lesson.data)}
    result["total_minutes"] = sum(s["minutes"] for s in result["sections"])
    return result


def snapshot(db, lesson, reason):
    db.add(LessonVersion(id=str(uuid4()), lesson_id=lesson.id, version=lesson.version,
                         reason=reason, created_at=now(), sections=copy.deepcopy(lesson.data["sections"])))


def invalidate_reports(data):
    for report in data["reports"].values():
        if report:
            report["stale"] = True


def validate_references(sections, sources):
    known = {s["id"] for s in sources}
    if any(set(s["source_ids"]) - known for s in sections):
        raise ValueError("A section references a source that was not retrieved")


def normalize_report(raw, layer, lesson):
    result = copy.deepcopy(raw)
    result.update(id=str(uuid4()), layer=layer, lesson_version=lesson.version, created_at=now(), stale=False)
    result.setdefault("alignment", "Not assessed by this layer")
    result.setdefault("limitations", [])
    result.setdefault("claims", [])
    result.setdefault("issues", [])
    sections = {s["id"]: s for s in lesson.data["sections"]}
    known_sources = {s["id"] for s in lesson.data["sources"]}
    for issue in result["issues"]:
        issue["id"] = str(uuid4())
        issue["status"] = "pending"
        issue.setdefault("proposed_content", None)
        issue.setdefault("evidence_source_ids", [])
        issue["evidence_source_ids"] = [s for s in issue["evidence_source_ids"] if s in known_sources]
        original = sections.get(issue.get("section_id"))
        issue["original_content"] = original["content"] if original else None
        if not original:
            issue["proposed_content"] = None
    return result


def update_stage(lesson_id, stage, status, error=None):
    with database.SessionLocal() as db:
        lesson = db.get(Lesson, lesson_id)
        data = copy.deepcopy(lesson.data)
        data["stages"][stage] = {"status": status, "error": error}
        activity(data, f"{stage.replace('_', ' ').capitalize()}: {status}" + (f" — {error}" if error else ""))
        lesson.data = data
        lesson.updated_at = now()
        db.commit()


async def run_workflow(lesson_id, requested):
    settings = get_settings()
    stages = list(STAGES) if requested == "all" else (["qc_research", "qc_instructional"] if requested == "qc_both" else [requested])
    try:
        for stage in stages:
            with database.SessionLocal() as db:
                lesson = db.get(Lesson, lesson_id)
                current = serialize(lesson)
            if requested == "all":
                if stage == "research" and current["stages"][stage]["status"] == "completed" and current["sources"]:
                    continue
                if stage == "generation" and current["sections"]:
                    continue
                if stage.startswith("qc_"):
                    report = current["reports"][stage[3:]]
                    if report and not report["stale"] and current["stages"][stage]["status"] == "completed":
                        continue
            update_stage(lesson_id, stage, "running")
            try:
                if stage == "research":
                    result = await research_service.research(current["title"], current["learning_objective"], settings)
                    with database.SessionLocal() as db:
                        lesson = db.get(Lesson, lesson_id)
                        data = copy.deepcopy(lesson.data)
                        # Retain old source snapshots so references in saved lessons remain resolvable.
                        merged = {s["id"]: s for s in data["sources"]}
                        cited = {sid for section in data["sections"] for sid in section["source_ids"]}
                        for source in result["sources"]:
                            if source["id"] not in cited:
                                merged[source["id"]] = source
                        data["sources"] = list(merged.values())
                        data["research_warnings"] = result["warnings"]
                        data["provider_status"] = result["provider_status"]
                        invalidate_reports(data)
                        lesson.data = data
                        db.commit()
                    if not result["sources"]:
                        raise ServiceError("No research sources were retrieved. Check provider configuration and retry research.")
                elif stage == "generation":
                    if current["sections"]:
                        raise ServiceError("This lesson already has content. Create a new lesson to generate again; saved edits are preserved.")
                    result = await lesson_generator.generate(current["title"], current["learning_objective"], current["sources"], settings)
                    parsed = LessonContent(sections=result)
                    sections = [s.model_dump() for s in parsed.sections]
                    validate_references(sections, current["sources"])
                    with database.SessionLocal() as db:
                        lesson = db.get(Lesson, lesson_id)
                        if lesson.version != current["version"] or lesson.data["sections"]:
                            raise ServiceError("Content changed during generation. New content was not applied.")
                        data = copy.deepcopy(lesson.data)
                        data["sections"] = sections
                        invalidate_reports(data)
                        lesson.data = data
                        lesson.version += 1
                        snapshot(db, lesson, "Generated lesson")
                        db.commit()
                else:
                    if not current["sections"]:
                        raise ServiceError("Generate a lesson before running quality control.")
                    auditor = qc_research if stage == "qc_research" else qc_instructional
                    result = await auditor.audit(current["title"], current["learning_objective"], current["sections"], current["sources"], settings)
                    with database.SessionLocal() as db:
                        lesson = db.get(Lesson, lesson_id)
                        data = copy.deepcopy(lesson.data)
                        report = normalize_report(result, stage[3:], lesson)
                        report["lesson_version"] = current["version"]
                        report["stale"] = lesson.version != current["version"]
                        data["reports"][stage[3:]] = report
                        lesson.data = data
                        db.add(AuditHistory(id=report["id"], lesson_id=lesson_id, report=report))
                        db.commit()
                update_stage(lesson_id, stage, "completed")
            except Exception as exc:
                safe = str(exc) if isinstance(exc, ServiceError) else "Stage failed safely. Check configuration and retry; saved content was preserved."
                log.warning("Lesson stage %s failed (%s)", stage, type(exc).__name__)
                update_stage(lesson_id, stage, "failed", safe)
                if stage in ("research", "generation"):
                    break
    except asyncio.CancelledError:
        with database.SessionLocal() as db:
            interrupted = db.get(Lesson, lesson_id)
            data = copy.deepcopy(interrupted.data)
            for state in data["stages"].values():
                if state["status"] == "running":
                    state.update(status="failed", error="Workflow interrupted. Retry this stage.")
            interrupted.data = data
            db.commit()
        raise
    finally:
        with database.SessionLocal() as db:
            lesson = db.get(Lesson, lesson_id)
            data = copy.deepcopy(lesson.data)
            failed = any(s["status"] == "failed" for s in data["stages"].values())
            lesson.status = "error" if failed else ("review" if data["sections"] else "draft")
            data.pop("job_id", None)
            lesson.data = data
            lesson.updated_at = now()
            db.commit()


def recover_interrupted_jobs():
    with database.SessionLocal() as db:
        for lesson in db.scalars(select(Lesson).where(Lesson.status == "running")):
            data = copy.deepcopy(lesson.data)
            for stage in data["stages"].values():
                if stage["status"] == "running":
                    stage.update(status="failed", error="Server restarted during this step. Retry to continue.")
            data.pop("job_id", None)
            activity(data, "Interrupted workflow recovered; saved stages preserved")
            lesson.data = data
            lesson.status = "error"
        db.commit()
