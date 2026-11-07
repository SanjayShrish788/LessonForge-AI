"""Print keyword contexts from a saved lesson JSON for manual factual review."""
import json
import sys

path = sys.argv[1]
keywords = sys.argv[2:]
lesson = json.load(open(path, encoding="utf-8"))
print(f"lesson: {lesson['title']} | total_core_minutes={sum(s['minutes'] for s in lesson['sections'])}")
for section in lesson["sections"]:
    for keyword in keywords:
        start = 0
        while True:
            index = section["content"].find(keyword, start)
            if index < 0:
                break
            snippet = section["content"][max(0, index - 130): index + 150].replace("\n", " ")
            print(f"[{section['kind']}] ...{snippet}...")
            start = index + len(keyword)
