"""QC 1: factual reliability, evidence provenance and citation coverage."""
from . import llm_service
from .audit_common import AuditOutput, issue, normalize_report, normalized_text, section_dicts
from .lesson_generator import source_context

SYSTEM = """You are QC Layer 1, an independent research and factual-accuracy auditor. You are not the lesson author and do not review teaching style.
Evaluate factual correctness, misleading simplifications, contradictions within/across sections, missing factual information, source reliability, relevance, recency, and citation coverage. Check examples and code for factual errors too. A prestigious domain alone does not verify a claim.
Before alleging a missing example or qualification, inspect the complete supplied section and distinguish absent content from content that could be expanded. Identify the specific claim and existing context; separate demonstrable errors from optional elaboration. Do not treat benefits or hypothetical examples as universal guarantees.
Actively challenge absolute statements and categorical generalizations: distinguish intended semantics from incidental implementation behavior, typical behavior from guarantees, and temporary failures from permanent ones. Examine exceptions, retry safety, and version-specific claims. Do not issue blanket assurances of correctness when evidence is incomplete or uncertain.
Audit every factual teaching section (introduction, concepts, examples, applications, summary), extracting the consequential factual claims, especially claims directly required by the objective. For each claim state unsupported when supplied evidence does not support it; uncertain when evidence appears supportive but requires human verification. Do NOT use verified: an LLM opinion or quote match is not independent verification.
Evidence must come from supplied source excerpts, not model memory. If a quote supports a claim, include an exact short quote and its source IDs; otherwise evidence_quote is empty. Metadata-only books or videos cannot support facts about their contents. You have not watched videos, read full books or independently browsed URLs. A snippet is limited context. Do not invent quotes or references.
Produce issue severity, affected section ID, explanation, evidence IDs and specific correction. A proposed_content value must be the COMPLETE replacement Markdown section, preserving valid content/citations and using only that section's existing source_ids; null if you cannot safely correct from supplied evidence. Never rewrite unrelated instructor content. Use null for issues needing additional research. Always state limitations. alignment should say 'Not assessed in factual audit'.
"""


async def audit(title, objective, sections, sources, settings):
    sections = section_dicts(sections)
    output = await llm_service.complete(SYSTEM, {"title": title, "learning_objective": objective, "sections": sections, "sources": source_context(sources)}, AuditOutput, settings)
    report = normalize_report(output, sections, sources)
    by_id = {s["id"]: s for s in sources}
    for claim in report["claims"]:
        quote = normalized_text(claim["evidence_quote"])
        eligible = [by_id[sid] for sid in claim["source_ids"] if by_id[sid].get("evidence_kind") in ("full_text", "snippet")]
        match = len(quote) >= 15 and any(quote in normalized_text(s.get("excerpt", "")) for s in eligible)
        if match:
            # This gate verifies only that a quotation exists in the retrieved text.
            # It cannot establish entailment or the truth of that text.
            claim["status"] = "uncertain"
            claim["explanation"] += " Exact quotation found in retrieved evidence; factual truth and entailment still require instructor verification."
        else:
            claim["status"] = "unsupported" if not eligible or not quote else "uncertain"
            if quote:
                claim["evidence_quote"] = ""
                claim["explanation"] += " The proposed evidence quotation could not be matched to the retrieved text and was discarded."
            else:
                claim["explanation"] += " No matching textual evidence was supplied; this is not a verified claim."
    factual_kinds = {"introduction", "concepts", "examples", "applications", "summary"}
    for section in sections:
        if section["kind"] in factual_kinds:
            valid_ids = [sid for sid in section.get("source_ids", []) if sid in by_id and by_id[sid].get("evidence_kind") in ("full_text", "snippet")]
            if not valid_ids:
                report["issues"].append(issue(section, "High", "No substantive retrieved evidence is referenced for this factual section.", "Research authoritative evidence and add inline source citations to the specific claims before relying on this section."))
            if not any(c["section_id"] == section["id"] for c in report["claims"]):
                report["issues"].append(issue(section, "Medium", "The AI audit did not assess a claim in this factual section.", "Review this section manually or rerun factual QC for claim-level coverage."))
    report["alignment"] = "Not assessed in factual audit."
    report["overall_assessment"] = "AI-assisted evidence review; no claims independently verified. " + report["overall_assessment"]
    report["limitations"] = list(dict.fromkeys(report["limitations"] + [
        "No automatic claim is marked verified. A quote match establishes textual presence only, not truth, context or entailment.",
        "Factual review is limited to retrieved excerpts. It does not independently reproduce experiments, run code, read complete books or watch videos.",
        "Source reliability and relevance assessments are AI-assisted judgments for instructor review; the audit may miss claims or contradictions."]))
    return report
