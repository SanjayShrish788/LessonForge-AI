"""Portable, escaped exports from the persisted lesson and audit snapshots."""
import io
import json
import re
import textwrap
import zipfile
from html import escape
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, PageBreak, LongTable, TableStyle, KeepTogether


def report_markdown(report, layer):
    if not report:
        return f"# QC: {layer}\n\nThis layer has not completed.\n"
    lines = [f"# QC: {layer.replace('_', ' ').title()}", "", f"Lesson version: {report['lesson_version']}",
             f"Audit date: {report['created_at']}", f"Current status: {'STALE - rerun required' if report['stale'] else 'current'}", "",
             "## Overall assessment", report["overall_assessment"], "", "## Objective alignment", report.get("alignment", "Not assessed"), "",
             "## Limitations"]
    lines += [f"- {s}" for s in report.get("limitations", [])] or ["No additional limitations reported."]
    lines += ["", "## Issues and recommendations"]
    for i, issue in enumerate(report["issues"], 1):
        lines += [f"### {i}. {issue['severity']} - {issue.get('section_id', 'Lesson')}",
                  f"Decision: {issue['status']}", issue["explanation"], f"Recommendation: {issue['recommendation']}",
                  "Evidence references: " + (", ".join(issue.get("evidence_source_ids", [])) or "None supplied")]
        if issue.get("proposed_content"):
            lines += ["", "Suggested replacement (requires instructor review):", issue["proposed_content"]]
        lines += [""]
    if not report["issues"]:
        lines += ["No issues were identified by this audit; this is not a guarantee of correctness."]
    if report.get("claims"):
        lines += ["", "## Claim evidence"]
        for claim in report["claims"]:
            lines += [f"### {claim['status'].title()} - {claim['section_id']}", claim["claim"], claim["explanation"],
                      "Source IDs: " + (", ".join(claim.get("source_ids", [])) or "None")]
            if claim.get("evidence_quote"):
                lines += [f"> {claim['evidence_quote']}"]
    return "\n\n".join(lines)


def references_markdown(lesson):
    used = {sid for s in lesson["sections"] for sid in s["source_ids"]}
    lines = ["## References and research provenance", "Sources marked cited were referenced in the lesson. Retrieval or citation does not establish factual verification."]
    for source in lesson["sources"]:
        label = "CITED" if source["id"] in used else "DISCOVERED, NOT CITED"
        lines += [f"### [{source['id']}] {source['title']}",
                  f"{label} | {source['source_type']} | Evidence: {source.get('evidence_kind', 'metadata')}",
                  f"Author / publisher: {source.get('author') or 'Not provided'}",
                  f"Publication date: {source.get('published_date') or 'Not provided'}",
                  source["url"], f"Relevance: {source.get('relevance', '')}",
                  f"Retrieved: {source.get('retrieved_at', 'Not recorded')}"]
    if lesson.get("research_warnings"):
        lines += ["## Research limitations"] + [f"- {s}" for s in lesson["research_warnings"]]
    return "\n\n".join(lines)


def lesson_markdown(lesson):
    lines = [f"# {lesson['title']}", f"**Learning objective:** {lesson['learning_objective']}",
             f"**Core lesson:** {lesson['total_minutes']} minutes | **Version:** {lesson['version']}",
             "Time allocations are estimates; instructors should adapt the pace to their learners."]
    for section in lesson["sections"]:
        lines += [f"## {section['title']} ({section['minutes']} min)", section["content"]]
        if section["source_ids"]:
            lines += ["Section references: " + ", ".join(f"[{s}]" for s in section["source_ids"])]
    lines += ["## Supplementary YouTube resources", "Optional extension after the core lesson; video viewing is not required within the 45-minute session."]
    videos = [s for s in lesson["sources"] if s["source_type"] == "youtube"]
    lines += [f"- [{s['title']}]({s['url']}) — {s.get('author') or 'Channel not provided'}" for s in videos] or ["No videos were retrieved. See research limitations below."]
    lines += [references_markdown(lesson)]
    return "\n\n".join(lines) + "\n"


def markdown_blocks(markdown):
    """Group Markdown tables outside fenced code; leave other lines intact."""
    lines = markdown.splitlines()
    index, in_code = 0, False
    while index < len(lines):
        line = lines[index]
        if line.startswith('```'):
            in_code = not in_code
        if (not in_code and line.strip().startswith('|') and index + 1 < len(lines)
                and re.fullmatch(r'\s*\|?[\s:|\-]+\|?\s*', lines[index + 1])
                and '-' in lines[index + 1]):
            rows = [line]
            index += 2
            while index < len(lines) and lines[index].strip().startswith('|'):
                rows.append(lines[index])
                index += 1
            yield rows
            continue
        yield line
        index += 1


def pdf_bytes(markdown, title):
    stream = io.BytesIO()
    # System fonts cover common Unicode lesson text. Fall back to core PDF fonts.
    regular, bold, mono = "Helvetica", "Helvetica-Bold", "Courier"
    candidates = [("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/consola.ttf"),
                  ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")]
    for paths in candidates:
        if all(Path(p).exists() for p in paths):
            for name, path in zip(("LFBody", "LFBold", "LFMono"), paths):
                if name not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(name, path))
            regular, bold, mono = "LFBody", "LFBold", "LFMono"
            break
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("LFBody", fontName=regular, fontSize=10, leading=15, textColor=colors.HexColor("#26363a"), spaceAfter=8, splitLongWords=True))
    styles.add(ParagraphStyle("LFCode", fontName=mono, fontSize=8, leading=11, backColor=colors.HexColor("#f2f5f5"), leftIndent=10, rightIndent=8, spaceAfter=10))
    for name, size in (("Title", 23), ("Heading1", 16), ("Heading2", 12)):
        styles[name].fontName = bold
        styles[name].fontSize = size
        styles[name].leading = size * 1.35
        styles[name].textColor = colors.HexColor("#176b59")
        styles[name].spaceBefore = 13
        styles[name].spaceAfter = 8
        styles[name].keepWithNext = True
    story, code = [], None
    for line in markdown_blocks(markdown):
        if isinstance(line, list):
            rows = [[cell.strip() for cell in row.strip().strip('|').split('|')] for row in line]
            count = len(rows[0])
            if all(len(row) == count for row in rows):
                data = [[Paragraph(escape(cell), styles['LFBody']) for cell in row] for row in rows]
                available = 8.27 * inch - 100
                widths = ([available * .17, available * .83] if count == 2 else
                          [available * .22, available * .39, available * .39] if count == 3 else
                          [available / count] * count)
                table = LongTable(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
                table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eaf2ee')),
                    ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#cbdcd2')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6)]))
                story.extend([table, Spacer(1, 8)])
            else:
                for row in line:
                    story.append(Paragraph(escape(row), styles['LFBody']))
            continue
        if line.startswith("```"):
            if code is None:
                code = []
            else:
                # Break long lines to avoid horizontal clipping; split large code blocks across pages.
                wrapped = "\n".join("\n".join(textwrap.wrap(row, 87, replace_whitespace=False, drop_whitespace=False)) if len(row) > 87 else row for row in code)
                block = Preformatted(wrapped, styles["LFCode"])
                story.append(KeepTogether(block) if len(wrapped.splitlines()) <= 45 else block)
                code = None
            continue
        if code is not None:
            code.append(line)
            continue
        if not line.strip():
            story.append(Spacer(1, 4))
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading:
            if len(heading[1]) == 1 and story:
                story.append(PageBreak())
            style = "Title" if len(heading[1]) == 1 else "Heading1" if len(heading[1]) == 2 else "Heading2"
            story.append(Paragraph(escape(heading[2]), styles[style]))
        else:
            # Escape all user/model text before enabling minimal Markdown emphasis.
            body = escape(line)
            # Only HTTP(S) destinations are made clickable. Display the URL as
            # well so printed copies retain the reference.
            body = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',
                          lambda match: f'<link href="{match[2]}" color="#176b59">{match[1]}</link> ({match[2]})', body)
            if re.fullmatch(r'https?://\S+', body):
                body = f'<link href="{body}" color="#176b59">{body}</link>'
            body = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", body)
            body = re.sub(r"`([^`]+)`", r'<font name="' + mono + r'">\1</font>', body)
            story.append(Paragraph(body, styles["LFBody"]))
    if code is not None:
        story.append(Preformatted("\n".join(code), styles["LFCode"]))
    # A heading followed by a short code block must travel with that block.
    # Heading.keepWithNext alone does not cross a nested KeepTogether flowable.
    grouped, index = [], 0
    while index < len(story):
        item = story[index]
        next_index = index + 1
        if isinstance(item, Paragraph) and item.style.name.startswith("Heading"):
            while next_index < len(story) and isinstance(story[next_index], Spacer):
                next_index += 1
            if next_index < len(story) and isinstance(story[next_index], KeepTogether):
                grouped.append(KeepTogether([item, *story[index + 1:next_index], *story[next_index]._content]))
                index = next_index + 1
                continue
            for spacer in story[index + 1:next_index]:
                spacer.keepWithNext = True
        grouped.append(item)
        index += 1
    story = grouped
    doc = SimpleDocTemplate(stream, pagesize=(8.27 * inch, 11.69 * inch), rightMargin=50, leftMargin=50,
                            topMargin=55, bottomMargin=48, title=title, author="LessonForge AI")

    def footer(canvas, document):
        canvas.setFont(regular, 8)
        canvas.setFillColor(colors.HexColor("#687b7c"))
        canvas.drawString(50, 27, "LessonForge AI | Instructor review copy")
        canvas.drawRightString(document.pagesize[0] - 50, 27, f"Page {document.page}")

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return stream.getvalue()


def export(lesson, format, scope):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", lesson["title"]).strip("-").lower()[:70] or "lesson"
    content = lesson_markdown(lesson) if scope in ("lesson", "package") else report_markdown(lesson["reports"].get(scope), scope)
    if scope == "package":
        content += "\n\n" + "\n\n".join(report_markdown(lesson["reports"].get(layer), layer) for layer in ("research", "instructional"))
    elif scope != "lesson":
        content += "\n\n" + references_markdown(lesson)
    data = lesson if scope in ("lesson", "package") else {"lesson_id": lesson["id"], "title": lesson["title"], "report": lesson["reports"].get(scope), "sources": lesson["sources"]}
    if format == "json":
        return json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"), "application/json", f"{slug}-{scope}.json"
    if format == "markdown":
        return content.encode("utf-8"), "text/markdown; charset=utf-8", f"{slug}-{scope}.md"
    if format == "pdf":
        return pdf_bytes(content, lesson["title"]), "application/pdf", f"{slug}-{scope}.pdf"
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("lesson.md", lesson_markdown(lesson))
        archive.writestr("lesson.pdf", pdf_bytes(lesson_markdown(lesson), lesson["title"]))
        archive.writestr("lesson.json", json.dumps(lesson, indent=2, ensure_ascii=False))
        archive.writestr("references.md", references_markdown(lesson))
        for layer in ("research", "instructional"):
            report_text = report_markdown(lesson["reports"].get(layer), layer) + "\n\n" + references_markdown(lesson)
            archive.writestr(f"qc-{layer}.md", report_text)
            archive.writestr(f"qc-{layer}.json", json.dumps(lesson["reports"].get(layer), indent=2, ensure_ascii=False))
            archive.writestr(f"qc-{layer}.pdf", pdf_bytes(report_text, f"QC {layer}"))
    return stream.getvalue(), "application/zip", f"{slug}-package.zip"
