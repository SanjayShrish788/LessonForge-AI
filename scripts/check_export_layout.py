"""Create visibly synthetic content to inspect PDF typography, wrapping and pagination."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.export_service import export

lesson = {
    "id": "layout-qa", "title": "Export layout QA - synthetic content", "version": 1,
    "learning_objective": "Inspect document formatting only. This is not an AI-generated assignment lesson.",
    "total_minutes": 8, "sources": [{"id": "qa-source", "title": "Synthetic reference for formatting only",
    "author": "Test fixture", "url": "https://example.org/formatting-test", "source_type": "website", "evidence_kind": "snippet",
    "published_date": None, "relevance": "Layout test only", "retrieved_at": "2026-11-07"}],
    "research_warnings": ["Synthetic layout fixture. No live generation or factual verification was performed."],
    "sections": [{"id": "example", "title": "Worked example and readable code", "kind": "examples", "minutes": 4,
        "content": "**Formatting fixture:** readable prose, emphasis, and Unicode symbols such as →, ≤, and café.\n\n"
        "```python\nclass Example:\n    def show(self):\n        return 'This is synthetic layout-test content'\n```\n\n"
        "- First step: inspect the example.\n- Second step: check page boundaries.\n\n"
        + "This paragraph checks long-form text wrapping and spacing without claiming to be an actual generated lesson. " * 30,
        "source_ids": ["qa-source"]},
        {"id": "activity", "title": "Formatting inspection", "kind": "activity", "minutes": 4,
         "content": "Review header, footer, code indentation, bullets, references, and the audit report on subsequent pages.", "source_ids": []}],
    "reports": {}
}
for layer in ("research", "instructional"):
    lesson["reports"][layer] = {"id": "layout-" + layer, "layer": layer, "lesson_version": 1, "created_at": "2026-11-07", "stale": False,
        "overall_assessment": "Synthetic report for layout inspection only.", "alignment": "Not evaluated in this formatting test.",
        "limitations": ["Not a live audit."], "claims": [], "issues": [{"id": "layout-issue", "severity": "Medium", "section_id": "example",
        "explanation": "This is synthetic issue text.", "recommendation": "Inspect the rendered document for clipping.",
        "evidence_source_ids": ["qa-source"], "proposed_content": None, "status": "pending"}]}
target = Path(__file__).resolve().parents[1] / "artifacts" / "export-layout-qa.pdf"
target.write_bytes(export(lesson, "pdf", "package")[0])
print(target)
