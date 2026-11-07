"""Report shape/normalization only. The two audit rubrics run independently."""
from typing import Literal
from uuid import uuid4
from pydantic import Field
from app.schemas import StrictModel
from .errors import ServiceError
from .citations import validate_references


class AuditIssue(StrictModel):
    severity: Literal["Critical", "High", "Medium", "Low"]
    section_id: str
    explanation: str = Field(min_length=1, max_length=5000)
    recommendation: str = Field(min_length=1, max_length=5000)
    evidence_source_ids: list[str]
    proposed_content: str | None = Field(max_length=20000)


class ClaimAssessment(StrictModel):
    section_id: str
    claim: str = Field(min_length=1, max_length=3000)
    status: Literal["verified", "unsupported", "uncertain"]
    source_ids: list[str]
    evidence_quote: str = Field(max_length=1000)
    explanation: str = Field(min_length=1, max_length=3000)


class AuditOutput(StrictModel):
    overall_assessment: str = Field(min_length=1, max_length=6000)
    alignment: str = Field(max_length=4000)
    limitations: list[str]
    issues: list[AuditIssue] = Field(max_length=60)
    claims: list[ClaimAssessment] = Field(max_length=80)


def section_dicts(sections):
    return [s.model_dump() if hasattr(s, "model_dump") else dict(s) for s in sections]


def issue(section, severity, explanation, recommendation, *, evidence=None, proposal=None):
    return {"id": str(uuid4()), "severity": severity, "section_id": section["id"], "explanation": explanation,
            "recommendation": recommendation, "evidence_source_ids": evidence or [], "proposed_content": proposal,
            "original_content": section["content"], "status": "pending"}


def normalize_report(output, sections, sources):
    sections_by_id = {s["id"]: s for s in sections}
    known_sources = {s["id"] for s in sources}
    report = output.model_dump()
    issues = []
    for value in report["issues"]:
        section = sections_by_id.get(value["section_id"])
        if not section:
            raise ServiceError("AI audit referenced an unknown lesson section. Retry this QC layer.")
        if set(value["evidence_source_ids"]) - known_sources:
            raise ServiceError("AI audit referenced a source that was not retrieved. Retry this QC layer.")
        proposal = value["proposed_content"]
        if proposal:
            # Applying a proposal changes content only. Do not silently add sources
            # that would be absent from the section's saved reference IDs.
            try:
                cited = validate_references(proposal, sources)
            except ValueError:
                proposal = None
                cited = set()
            if cited != set(section.get("source_ids", [])):
                proposal = None
            if proposal == section["content"]:
                proposal = None
        issues.append(issue(section, value["severity"], value["explanation"], value["recommendation"], evidence=value["evidence_source_ids"], proposal=proposal))
    report["issues"] = issues
    for claim in report["claims"]:
        if claim["section_id"] not in sections_by_id or set(claim["source_ids"]) - known_sources:
            raise ServiceError("AI audit returned invalid claim references. Retry this QC layer.")
    return report


def normalized_text(value):
    return " ".join(value.split()).casefold()
