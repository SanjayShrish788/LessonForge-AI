"""Write full lesson section content to a UTF-8 file for QA review."""
import json
import sys
from pathlib import Path

lesson = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2])
lines = [f"# {lesson['title']}", f"total_minutes={sum(s['minutes'] for s in lesson['sections'])}", ""]
for s in lesson["sections"]:
    lines += [f"##### {s['kind'].upper()} ({s['minutes']}m) ids={s['id']} cite={s['source_ids']} #####", s["content"], ""]
out.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size} bytes)")
