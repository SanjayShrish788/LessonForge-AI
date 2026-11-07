# Demo video script (approximately 6–8 minutes)

Prepare real API credentials privately, run the two live acceptance lessons, and inspect their output before recording. Keep `.env`, terminals containing secrets, billing details, and private browser tabs out of view. If live generation is unavailable, describe that limitation accurately; fixture tests do not satisfy the two-lesson demonstration.

## 0:00–0:40 — Problem and dashboard

“LessonForge AI helps an instructor turn a lesson title and learning objective into a researched lesson that fits within 45 minutes. The workflow separates content generation, factual review, instructional review, and instructor approval.”

Show saved lessons, activity, provider configuration, and the New Lesson form. Briefly demonstrate empty-input validation.

## 0:40–1:30 — Generate the mandatory HTTP lesson

Use the exact required title and objective from the checklist. Start generation and explain the visible stages. If editing the recording to skip waiting, label the cut; do not imply a faster actual runtime.

“Website research uses Tavily, book discovery uses Google Books, and video discovery uses YouTube Data API v3. These are actual API results. Partial provider failures are displayed, and successful stages are saved.”

## 1:30–2:20 — Research and timed lesson

Show a website, book, and video result. Open relevant links and inspect author/channel metadata, excerpts, and retrieved-versus-used status.

“A search result is not a verified claim. The app distinguishes retrieved text from snippets and metadata. It does not claim to have read a complete book or watched a video.”

Preview the lesson, GET/POST examples, status categories, activity, and knowledge checks. Show section timing and the total. Explain that supplementary videos are optional beyond the timed core.

## 2:20–3:20 — QC 1: factual and evidence review

Show overall assessment, issue severity, affected sections, evidence links/quotes, and limitations. Select an actual issue and explain why it matters. If there are no suitable correction proposals, show the report honestly; do not inject an error into a live result merely to pretend the model found it.

“This pipeline checks factual support, source relevance and reliability, contradictions, misleading explanations, citation gaps, and missing information. A model opinion alone never proves a claim is verified.”

Preview a proposed change before applying it. Show the resulting saved revision. Reject another unsuitable suggestion if available.

## 3:20–4:10 — QC 2: instructional review

Show the independent instructional report and its alignment, sequence, clarity, example, activity, question, and timing evaluation.

“The instructional auditor uses its own prompt and evaluation call. It does not copy or read QC 1’s report. Both can use the same model provider, so this is logical independence, not independent human verification.”

Run one layer individually to demonstrate independent reruns.

## 4:10–5:00 — Edit, save, recover, and preview

Make a small meaningful instructor edit, save, refresh, and confirm persistence. Show stale audit status after the edit and rerun both audits against the new revision. Open version history and explain restore behavior.

“Every save checks the expected content version. A stale recommendation cannot silently overwrite a section I have changed. Failed jobs preserve saved work.”

## 5:00–5:40 — Exports

Download and open a PDF and Markdown file. Show JSON, both separate audit exports, and the combined ZIP containing lesson content, references, and reports. Check document layout and that sources remain readable.

## 5:40–6:30 — Second real lesson

Open the generated Java inheritance and polymorphism lesson. Show its practical code, comparison of the concepts, source library, time budget, and both audit reports. State the actual result of compiling/running code examples if performed; do not imply code execution when it was only visually reviewed.

## 6:30–7:30 — Engineering and validation

“The frontend uses React, Vite, Tailwind, and Lucide. FastAPI and Pydantic validate requests and structured model output. SQLAlchemy stores lessons and versions in SQLite. The modular LLM adapter supports Gemini or OpenAI, and ReportLab produces PDF exports.”

Show the repository structure, test command/result, and verification report without exposing credentials. Explain the difference between mocked integration tests and live acceptance evidence. Mention any outstanding live verification or provider limitations.

## Recording checklist

- [ ] Two genuinely generated lessons shown.
- [ ] Research from all three source categories visible.
- [ ] 45-minute core budget and required content visible.
- [ ] Both independent audit reports demonstrated.
- [ ] Recommendation preview/apply/reject shown where available.
- [ ] Manual editing, save persistence, and stale audit handling shown.
- [ ] Final preview and exports opened.
- [ ] Failure/retry and version recovery explained or demonstrated.
- [ ] Stack and research integrity explained accurately.
- [ ] Actual results stated; untested behavior not presented as successful.
- [ ] Video and repository links accessible to evaluators.
