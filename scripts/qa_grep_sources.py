"""Show which retrieved sources contain given keywords, for accurate citation."""
import json
import re
import sys
from pathlib import Path

lesson = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
keywords = [k.lower() for k in sys.argv[2:]]
for source in lesson["sources"]:
    haystack = ((source.get("excerpt") or "") + " " + (source.get("description") or "")).lower()
    found = [k for k in keywords if k in haystack]
    if found:
        print(f"{source['id']} [{source['evidence_kind']}] {source['url']}")
        print(f"   matches: {found}")
