import copy
from contextlib import asynccontextmanager
from uuid import uuid4
from typing import Literal
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.responses import JSONResponse
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from . import database
from .database import get_db
from .config import get_settings
from .models import Lesson, LessonVersion, AuditHistory
from .schemas import LessonCreate, LessonUpdate, LessonContent, RunRequest, RecommendationRequest, VersionRequest
from .workflow import (initial_data, now, activity, serialize, snapshot, invalidate_reports,
                       validate_references, run_workflow, recover_interrupted_jobs)
from .services.export_service import export


@asynccontextmanager
async def lifespan(app):
    database.init_db()
    recover_interrupted_jobs()
    yield


app = FastAPI(title="LessonForge AI", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins.split(","),
                   allow_methods=["GET", "POST", "PATCH"], allow_headers=["Content-Type"])


@app.exception_handler(StaleDataError)
async def concurrent_write(request, exc):
    return JSONResponse(status_code=409, content={"detail": "Another operation changed this lesson. Reload before saving; your changes were not applied."})


def find_lesson(db, lesson_id):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    return lesson


def check_edit(lesson, expected_version):
    if lesson.status == "running":
        raise HTTPException(409, "A workflow is running. Wait until it finishes before editing saved content.")
    if lesson.version != expected_version:
        raise HTTPException(409, "This lesson changed since you opened it. Reload and review before saving.")


def save_content(db, lesson, sections, reason):
    try:
        parsed = LessonContent(sections=sections)
        sections = [s.model_dump() for s in parsed.sections]
        validate_references(sections, lesson.data["sources"])
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    data = copy.deepcopy(lesson.data)
    data["sections"] = sections
    invalidate_reports(data)
    activity(data, reason)
    lesson.data = data
    lesson.version += 1
    lesson.updated_at = now()
    lesson.status = "review"
    snapshot(db, lesson, reason)


@app.get("/api/health")
def health():
    s = get_settings()
    key = s.gemini_api_key if s.llm_provider == "gemini" else s.openai_api_key
    model = s.gemini_model if s.llm_provider == "gemini" else s.openai_model
    return {"status": "ok", "providers": {"llm": {"configured": bool(key), "provider": s.llm_provider, "model": model},
            "web": {"configured": bool(s.tavily_api_key)}, "books": {"configured": True, "key_configured": bool(s.google_books_api_key)},
            "youtube": {"configured": bool(s.youtube_api_key)}}}


@app.get("/api/lessons")
def list_lessons(db: Session = Depends(get_db)):
    return [serialize(l) for l in db.scalars(select(Lesson).order_by(Lesson.updated_at.desc()))]


@app.post("/api/lessons", status_code=201)
def create_lesson(payload: LessonCreate, db: Session = Depends(get_db)):
    data = initial_data()
    activity(data, "Lesson draft created")
    lesson = Lesson(id=str(uuid4()), **payload.model_dump(), version=1, status="draft", created_at=now(), updated_at=now(), data=data)
    db.add(lesson)
    db.commit()
    return serialize(lesson)


@app.get("/api/lessons/{lesson_id}")
def get_lesson(lesson_id: str, db: Session = Depends(get_db)):
    return serialize(find_lesson(db, lesson_id))


@app.patch("/api/lessons/{lesson_id}")
def edit_lesson(lesson_id: str, payload: LessonUpdate, db: Session = Depends(get_db)):
    lesson = find_lesson(db, lesson_id)
    check_edit(lesson, payload.expected_version)
    save_content(db, lesson, payload.sections, "Instructor edits saved")
    db.commit()
    return serialize(lesson)


@app.post("/api/lessons/{lesson_id}/run", status_code=202)
def run(lesson_id: str, payload: RunRequest, background: BackgroundTasks, db: Session = Depends(get_db)):
    lesson = find_lesson(db, lesson_id)
    if lesson.status == "running":
        raise HTTPException(409, "This lesson already has a running workflow")
    if payload.stage == "generation" and lesson.data["sections"]:
        raise HTTPException(409, "Saved content cannot be regenerated. Create a new lesson instead.")
    if payload.stage.startswith("qc") and not lesson.data["sections"]:
        raise HTTPException(409, "Generate a lesson before running quality control")
    job_id = str(uuid4())
    data = copy.deepcopy(lesson.data)
    data["job_id"] = job_id
    activity(data, f"Started {payload.stage.replace('_', ' ')} workflow")
    result = db.execute(update(Lesson).where(Lesson.id == lesson_id, Lesson.status != "running", Lesson.revision == lesson.revision)
                        .values(status="running", data=data, updated_at=now(), revision=Lesson.revision + 1))
    if result.rowcount != 1:
        raise HTTPException(409, "This lesson changed or a workflow started. Reload before retrying.")
    db.commit()
    background.add_task(run_workflow, lesson_id, payload.stage)
    return {"job_id": job_id}


@app.get("/api/lessons/{lesson_id}/versions")
def versions(lesson_id: str, db: Session = Depends(get_db)):
    find_lesson(db, lesson_id)
    return [{"id": v.id, "version": v.version, "reason": v.reason, "created_at": v.created_at, "sections": v.sections}
            for v in db.scalars(select(LessonVersion).where(LessonVersion.lesson_id == lesson_id).order_by(LessonVersion.version.desc()))]


@app.post("/api/lessons/{lesson_id}/restore/{version_id}")
def restore(lesson_id: str, version_id: str, payload: VersionRequest, db: Session = Depends(get_db)):
    lesson = find_lesson(db, lesson_id)
    check_edit(lesson, payload.expected_version)
    version = db.get(LessonVersion, version_id)
    if not version or version.lesson_id != lesson_id:
        raise HTTPException(404, "Saved version not found")
    save_content(db, lesson, version.sections, f"Restored version {version.version}")
    db.commit()
    return serialize(lesson)


@app.get("/api/lessons/{lesson_id}/audit-history")
def audit_history(lesson_id: str, db: Session = Depends(get_db)):
    find_lesson(db, lesson_id)
    return [r.report for r in db.scalars(select(AuditHistory).where(AuditHistory.lesson_id == lesson_id))]


@app.post("/api/lessons/{lesson_id}/recommendations/{layer}/{issue_id}")
def recommendation(lesson_id: str, layer: Literal["research", "instructional"], issue_id: str,
                   payload: RecommendationRequest, db: Session = Depends(get_db)):
    lesson = find_lesson(db, lesson_id)
    check_edit(lesson, payload.expected_version)
    data = copy.deepcopy(lesson.data)
    report = data["reports"].get(layer)
    issue = next((i for i in report["issues"] if i["id"] == issue_id), None) if report else None
    if not issue:
        raise HTTPException(404, "Recommendation not found")
    if issue["status"] != "pending":
        raise HTTPException(409, "This recommendation already has a recorded decision")
    if payload.action == "reject":
        issue["status"] = "rejected"
        activity(data, f"Rejected {layer} recommendation")
        lesson.data = data
        lesson.updated_at = now()
    else:
        if report["stale"] or report["lesson_version"] != lesson.version:
            raise HTTPException(409, "This audit is stale. Re-run the layer to review recommendations against your latest edits.")
        target = next((s for s in data["sections"] if s["id"] == issue["section_id"]), None)
        if not target or not issue.get("proposed_content"):
            raise HTTPException(409, "This recommendation requires a manual section edit")
        if target["content"] != issue.get("original_content"):
            raise HTTPException(409, "The affected section has changed. Your manual edits were preserved.")
        target["content"] = issue["proposed_content"]
        issue["status"] = "applied"
        lesson.data = data
        save_content(db, lesson, data["sections"], f"Applied {layer} recommendation")
    history = db.get(AuditHistory, report["id"])
    if history:
        history.report = copy.deepcopy(lesson.data["reports"][layer])
    db.commit()
    return serialize(lesson)


@app.get("/api/lessons/{lesson_id}/export")
def export_lesson(lesson_id: str, format: Literal["pdf", "markdown", "json", "zip"] = "pdf",
                  scope: Literal["lesson", "research", "instructional", "package"] = "lesson", db: Session = Depends(get_db)):
    lesson = serialize(find_lesson(db, lesson_id))
    if not lesson["sections"]:
        raise HTTPException(409, "Generate lesson content before exporting")
    if scope in ("research", "instructional") and not lesson["reports"].get(scope):
        raise HTTPException(409, "Run this quality-control layer before exporting its report")
    content, media_type, filename = export(lesson, format, scope)
    return Response(content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
