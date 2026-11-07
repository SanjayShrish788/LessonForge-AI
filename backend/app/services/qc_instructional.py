"""QC 2: independently evaluates pedagogy; never reads the factual QC output."""
import math
from . import llm_service
from .audit_common import AuditOutput, issue, normalize_report, section_dicts
from .lesson_generator import REQUIRED_KINDS

SYSTEM = """You are QC Layer 2, an independent instructional-design reviewer. Review only educational effectiveness, not factual verification or source reliability. You have no output from the factual reviewer.
Evaluate alignment to every verb/concept in the learning objective; beginner accessibility; prerequisite fit; clarity; logical sequence; difficulty; worked-example quality; useful real-world applications; engagement and active practice; knowledge checks with correct-answer explanations; completeness; and realistic 45-minute pacing, including reading, activities, examples and answers.
Read the complete supplied lesson before alleging that an example, answer rationale, or objective is absent. Distinguish an existing element that could be clearer from a missing element; state the specific remaining gap. Reserve critical severity for a genuinely obstructed objective, not an optional enhancement.
Provide an explicit objective-alignment assessment. Identify concrete weaknesses with affected section IDs, severity and actionable recommendations. proposed_content may be a COMPLETE replacement Markdown section to improve pedagogy while preserving accurate content and its existing citations, or null if unsuitable. Do not introduce new external factual claims or sources; preserve source_ids. Avoid changes unrelated to the issue. If a timing allocation needs editing, propose it in recommendation text and leave proposed_content null because the instructor must edit minutes separately.
Return claims as an empty array: this layer does not assign factual verification labels. evidence_source_ids should normally be empty. Make no claim that an AI audit proves teaching effectiveness. Include limitations.
"""


async def audit(title, objective, sections, sources, settings):
    sections = section_dicts(sections)
    output = await llm_service.complete(SYSTEM, {"title": title, "learning_objective": objective, "sections": sections,
        "core_minutes": sum(s["minutes"] for s in sections), "maximum_core_minutes": 45}, AuditOutput, settings)
    report = normalize_report(output, sections, sources)
    report["claims"] = []
    if sections:
        missing = REQUIRED_KINDS - {s["kind"] for s in sections}
        if missing:
            report["issues"].append(issue(sections[0], "High", "Required learning components are missing: " + ", ".join(sorted(missing)), "Restore or add the missing learning components through section editing before publishing."))
        total = sum(s["minutes"] for s in sections)
        if total > 45:
            report["issues"].append(issue(sections[0], "Critical", f"The allocated lesson duration is {total} minutes, exceeding 45.", "Reduce the core lesson to 45 minutes or less, including activities and checks."))
        # Conservative readability flag, explicitly a heuristic rather than a claim
        # that users all read at one fixed speed.
        for section in sections:
            words = len(section["content"].split())
            minimum_reading = math.ceil(words / 180)
            if minimum_reading > section["minutes"]:
                report["issues"].append(issue(section, "Medium", f"About {words} words are allocated {section['minutes']} minutes. A 180 words/minute reading heuristic alone estimates {minimum_reading} minutes, before practice.", "Shorten this section or revise its time allocation while keeping the total at or below 45 minutes."))
    report["overall_assessment"] = "Independent instructional review. " + report["overall_assessment"]
    report["limitations"] = list(dict.fromkeys(report["limitations"] + [
        "Pedagogical judgments are AI-assisted; teaching effectiveness has not been tested with learners.",
        "Time allocations are estimates. Optional supplementary videos are outside the core lesson and cannot be prerequisites for its objective.",
        "This layer does not verify factual correctness and does not consume the factual audit report."]))
    return report
