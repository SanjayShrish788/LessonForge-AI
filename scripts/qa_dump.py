"""Dump a saved lesson and its QC reports compactly for QA review."""
import json
import sys
from pathlib import Path

base = Path(sys.argv[1])
slug = sys.argv[2]
lesson = json.loads((base / f"{slug}.json").read_text(encoding="utf-8"))
print(f"=== LESSON: {lesson['title']} ===")
print(f"status={lesson['status']} version={lesson['version']} total_minutes={sum(s['minutes'] for s in lesson['sections'])}")
print(f"sources={len(lesson['sources'])} kinds={[s['source_type'] for s in lesson['sources']]}")
print("--- sections ---")
for s in lesson["sections"]:
    print(f"  [{s['kind']}] {s['minutes']}m cite={s['source_ids']} words={len(s['content'].split())}")
for layer in ("research", "instructional"):
    report = lesson["reports"].get(layer)
    print(f"=== QC {layer} ===")
    if not report:
        print("  (none)")
        continue
    print(f"  stale={report['stale']} lesson_version={report['lesson_version']} issues={len(report['issues'])} claims={len(report.get('claims') or [])}")
    print("  overall:", (report["overall_assessment"] or "")[:400])
    for i in report["issues"]:
        print(f"    - {i['severity']} [{i['section_id']}] {i['explanation'][:170]}")
        print(f"      rec: {i['recommendation'][:150]}")
