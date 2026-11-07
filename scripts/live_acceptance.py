"""Run the two assignment lessons against REAL configured providers.

No provider mocks or fixture content are used here. Successful execution checks
the technical workflow, not the factual truth of an AI-generated lesson.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx


CASES = [
    (
        "http-requests-and-responses",
        "HTTP Requests and Responses",
        "Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.",
    ),
    (
        "java-inheritance-and-polymorphism",
        "Object-Oriented Programming: Inheritance and Polymorphism in Java",
        "Explain inheritance and polymorphism in Java, demonstrate their differences through practical code examples, and identify situations where each concept is useful.",
    ),
]


def checked(response: httpx.Response):
    response.raise_for_status()
    return response.json()


def wait_for_lesson(client, lesson_id, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        lesson = checked(client.get(f"lessons/{lesson_id}"))
        if lesson["status"] != "running":
            return lesson
        time.sleep(1.5)
    raise TimeoutError(f"Lesson job did not finish within {timeout} seconds")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api")
    parser.add_argument("--output", type=Path, default=Path("artifacts/live-acceptance"))
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    receipt = {
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "provider_mode": "live",
        "status": "running",
        "cases": [],
        "limitations": [
            "Technical workflow assertions do not establish factual accuracy.",
            "Review both lessons and their evidence manually using docs/ACCEPTANCE_CHECKLIST.md.",
        ],
    }
    exit_code = 1
    try:
        with httpx.Client(base_url=args.base_url.rstrip("/") + "/", timeout=30) as client:
            health = checked(client.get("health"))
            receipt["provider_configuration"] = health.get("providers", {})
            missing = [
                name for name in ("llm", "web", "youtube")
                if not health.get("providers", {}).get(name, {}).get("configured")
            ]
            if missing:
                receipt["status"] = "blocked"
                receipt["reason"] = "Missing provider configuration: " + ", ".join(missing)
                print(receipt["reason"])
                return 2

            for slug, title, objective in CASES:
                case = {"title": title, "status": "running", "checks": {}}
                receipt["cases"].append(case)
                try:
                    lesson = checked(client.post("lessons", json={"title": title, "learning_objective": objective}))
                    lesson_id = lesson["id"]
                    case["lesson_id"] = lesson_id
                    checked(client.post(f"lessons/{lesson_id}/run", json={"stage": "all"}))
                    lesson = wait_for_lesson(client, lesson_id, args.timeout)
                    case["stages"] = lesson.get("stages")
                    case["research_warnings"] = lesson.get("research_warnings", [])
                    (args.output / f"{slug}.json").write_text(json.dumps(lesson, indent=2, ensure_ascii=False), encoding="utf-8")
                    assert lesson["status"] != "error", "A pipeline stage failed; inspect stages in the saved JSON"
                    assert lesson["sections"], "No generated content"
                    assert 0 < sum(s["minutes"] for s in lesson["sections"]) <= 45
                    kinds = {s["kind"] for s in lesson["sections"]}
                    assert {"overview", "objectives", "prerequisites", "introduction", "concepts", "examples", "applications", "activity", "knowledge_check", "summary"} <= kinds
                    source_ids = {s["id"] for s in lesson["sources"]}
                    assert all(set(s["source_ids"]) <= source_ids for s in lesson["sections"])
                    assert {"website", "book", "youtube"} <= {s["source_type"] for s in lesson["sources"]}, "One or more source types returned no usable results"
                    assert lesson["reports"]["research"] and lesson["reports"]["instructional"]
                    assert lesson["reports"]["research"]["id"] != lesson["reports"]["instructional"]["id"]
                    case["checks"]["generated_structure_sources_time_and_audits"] = "passed"

                    # Make a transparent instructor note, persist it, then restore
                    # the original content to avoid contaminating audit evidence.
                    original_sections = lesson["sections"]
                    edited = json.loads(json.dumps(original_sections))
                    edited[0]["content"] += "\n\nInstructor note: reviewed during the live persistence check."
                    saved = checked(client.patch(f"lessons/{lesson_id}", json={"expected_version": lesson["version"], "sections": edited}))
                    reloaded = checked(client.get(f"lessons/{lesson_id}"))
                    assert reloaded["sections"][0]["content"] == edited[0]["content"]
                    lesson = checked(client.patch(f"lessons/{lesson_id}", json={"expected_version": saved["version"], "sections": original_sections}))
                    case["checks"]["manual_edit_save_reload"] = "passed"
                    # Audits must correspond to the latest content version.
                    checked(client.post(f"lessons/{lesson_id}/run", json={"stage": "qc_both"}))
                    lesson = wait_for_lesson(client, lesson_id, args.timeout)
                    assert lesson["status"] != "error", "Audit rerun failed"
                    assert all(lesson["reports"][layer] and not lesson["reports"][layer]["stale"] for layer in ("research", "instructional"))
                    for format_name, suffix in (("pdf", "pdf"), ("markdown", "md"), ("json", "json"), ("zip", "zip")):
                        scope = "package" if format_name == "zip" else "lesson"
                        response = client.get(f"lessons/{lesson_id}/export", params={"format": format_name, "scope": scope})
                        response.raise_for_status()
                        assert response.content, "Empty export"
                        (args.output / f"{slug}.{suffix}").write_bytes(response.content)
                    for layer in ("research", "instructional"):
                        response = client.get(f"lessons/{lesson_id}/export", params={"format": "json", "scope": layer})
                        response.raise_for_status()
                        (args.output / f"{slug}-qc-{layer}.json").write_bytes(response.content)
                    case["checks"]["independent_audit_rerun_and_exports"] = "passed"
                    case["status"] = "technical_checks_passed_manual_review_required"
                    case["total_minutes"] = sum(s["minutes"] for s in lesson["sections"])
                    print(f"{title}: technical checks passed; manual factual review remains required")
                except Exception as exc:
                    case["status"] = "failed"
                    case["error"] = str(exc)
                    print(f"{title}: {exc}", file=sys.stderr)
                finally:
                    if case.get("lesson_id"):
                        latest = checked(client.get(f"lessons/{case['lesson_id']}"))
                        case["stages"] = latest.get("stages")
                        (args.output / f"{slug}.json").write_text(json.dumps(latest, indent=2, ensure_ascii=False), encoding="utf-8")
            failed = any(c["status"] == "failed" for c in receipt["cases"])
            receipt["status"] = "failed" if failed else "technical_checks_passed_manual_review_required"
            exit_code = 1 if failed else 0
    except Exception as exc:
        receipt["status"] = "blocked"
        receipt["reason"] = str(exc)
        print(str(exc), file=sys.stderr)
    finally:
        (args.output / "results.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

