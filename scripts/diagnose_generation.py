"""Diagnose structured lesson generation, using saved research sources.

Reuses the application's own services so the exact Pydantic and semantic
(citation / duration) validation errors are visible. Never prints the API key.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.schemas import LessonContent  # noqa: E402
from app.services import lesson_generator, llm_service  # noqa: E402
from app.services.errors import ServiceError  # noqa: E402


async def run(source_json: Path) -> int:
    data = json.loads(source_json.read_text(encoding="utf-8"))
    title, objective, sources = data["title"], data["learning_objective"], data["sources"]
    settings = get_settings()
    provider = settings.llm_provider
    print(f"provider={provider} model={getattr(settings, provider + '_model')}")
    usable = {s["id"] for s in sources if s.get("evidence_kind") in ("full_text", "snippet") and s.get("excerpt")}
    print(f"usable evidence sources: {len(usable)}")

    payload = {"title": title, "learning_objective": objective, "sources": lesson_generator.source_context(sources)}
    try:
        content = await llm_service.complete(lesson_generator.SYSTEM, payload, LessonContent, settings, adjust=lesson_generator.rebalance_minutes)
    except ServiceError as exc:
        print(f"complete() ServiceError: {exc}")
        return 1
    print(f"pydantic OK: {len(content.sections)} sections, total {sum(s.minutes for s in content.sections)} minutes")

    kinds = {s.kind for s in content.sections}
    print(f"missing kinds: {sorted(lesson_generator.REQUIRED_KINDS - kinds)}")
    try:
        validated = lesson_generator.validate_generation(content, sources)
        print("validate_generation OK")
    except ValueError as exc:
        print(f"validate_generation FAILED: {exc}")
        for section in content.sections:
            inline_ok = set(section.source_ids).issubset(usable)
            print(f"  [{section.kind}] declared={section.source_ids} usable_ok={inline_ok}")
        return 1
    for section in validated.sections:
        marks = section.content.count("[") 
        print(f"  [{section.kind}] {section.minutes}m words={len(section.content.split())} citations={section.source_ids} inline_brackets={marks}")
    out = source_json.with_name(source_json.stem + "-generated.json")
    out.write_text(json.dumps({"title": title, "sections": [s.model_dump() for s in validated.sections]}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"saved {out.name}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_json", type=Path)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.source_json)))



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_json", type=Path)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.source_json)))
