# Verification record

> Historical record: some older lesson claims, durations, issue counts, and readiness statements below describe earlier runs or were inaccurate. The saved acceptance receipt records Java at 43 minutes and HTTP QC counts of 5 factual / 1 instructional. Current version-specific findings and verification are in [the claim and QC audit](CLAIM_AND_QC_AUDIT.md); instructor approval remains pending.


This file separates offline engineering checks from real provider acceptance. Results below were observed on 7 November 2026 in this backup workspace. No check is marked passed merely because code exists. Credentials are never printed.

## Automated checks

| Check | Status | Evidence |
| --- | --- | --- |
| Backend automated suite | Passed: 47 tests in ~3 seconds | `.\backend\.venv\Scripts\python.exe -m pytest backend\tests -q` (one upstream Starlette deprecation warning, no failing assertions) |
| Frontend production build | Passed: Vite 6.4.5, 1837 modules | `npm run build` in `frontend` |
| Live LLM connectivity (OpenAI) | Passed: structured JSON accepted | `python scripts\verify_llm.py --provider openai` -> `label=Not Found, http_status_meaning=404` |
| Live LLM connectivity (Gemini) | Intermittent: HTTP 429 rate limit | `python scripts\verify_llm.py --provider gemini`; a retry later succeeded, but quota was unstable during testing |
| Live acceptance - both required lessons | Passed: technical checks | `powershell -File scripts\run_acceptance.ps1` -> exit 0; `artifacts/openai-acceptance/results.json` |

## Live acceptance detail

The acceptance runner started the real FastAPI backend, confirmed `/api/health` reported `llm=openai/gpt-4o-mini` with `web`, `books`, and `youtube` configured, then created and ran both mandatory lessons against real provider APIs.

| Lesson | Generation | Research | Factual QC | Instructional QC | Edit & save | Exports | Core minutes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HTTP Requests and Responses | Passed | Passed | Passed | Passed | Passed | Passed | 42 |
| OOP: Inheritance and Polymorphism in Java | Passed | Passed | Passed | Passed | Passed | Passed | 43 |

- Research returned website (Tavily), book (Google Books), and video (YouTube) results for both lessons. Book/video results are discovery metadata only; the app states this explicitly.
- Both QC layers produced separate reports with different rubrics. Example HTTP factual QC raised 12 issues, including a `Critical` flag that the phrase "GET does not change server state" is an oversimplification, plus citation-coverage warnings. Instructional QC raised 2 distinct issues on example depth and activity guidance. The two reports do not read each other.
- The runner saved and reloaded a real instructor edit, confirmed persistence, then reran both audits against the saved revision and confirmed the reports were no longer stale.
- PDF, Markdown, JSON, and ZIP exports were downloaded. The ZIP archives each contain `lesson.md`, `lesson.pdf`, `lesson.json`, `references.md`, and both QC reports in md/json/pdf. All JSON files parse; both PDFs begin with `%PDF-`.

## Manual content verification (instructor)

- HTTP lesson: distinguishes GET (safe, idempotent, retrieval) from POST (submission, not safe, request body), and explains the 2xx/4xx/5xx categories accurately. A later run explained `403 Forbidden` as "the server understands the request but refuses to authorize it" and used `401 Unauthorized` for missing credentials. No fabricated URLs, books, or videos were observed; example addresses are inside code blocks.
- Java lesson: correctly separates compile-time polymorphism (method overloading) from runtime polymorphism (method overriding), uses the `extends` keyword, and demonstrates dynamic dispatch through a superclass reference. The polymorphism example was extracted and **compiled and run under Java 17**, producing exactly the stated output (`Bark`, then `Meow`).
- These checks confirm the required structural and factual points. A full line-by-line factual sign-off remains the instructor's responsibility using [the acceptance checklist](ACCEPTANCE_CHECKLIST.md).

## Offline engineering checks

Offline test fixtures are deliberately synthetic and exist only under `backend/tests`. They are not seeded into the application or represented as retrieved sources. A successful offline test verifies software behavior, not model quality, research accuracy, or fulfillment of the two real lesson requirements.

The suite exercises input validation, saved drafts, distinct QC reports, successful-stage preservation on retry, independent QC reruns, failure isolation, manual save persistence, stale audit flags, version conflicts, duration/citation validation, recommendation apply/reject, stale recommendation protection, version restoration, PDF/Markdown/JSON/ZIP exports, prevention of regeneration over manual edits, and protection of a concurrent manual save when another tab starts a job.

## Reliability fixes verified this session

1. `llm_service.complete` now returns a targeted correction hint naming the exact failed bound (for example the 45-minute total) and allows a bounded extra attempt.
2. `lesson_generator.rebalance_minutes` deterministically fits model time estimates into the 45-minute budget without touching content, so a minor overrun no longer discards an otherwise complete lesson.
3. `lesson_generator.validate_generation` reconciles each section's reference list to the sources actually cited or declared and de-duplicates repeated framing sections, while still rejecting fabricated inline citations/URLs and metadata-only citations.
4. `scripts/run_acceptance.ps1` no longer aborts the backend when the acceptance runner writes a per-case failure message to stderr.

Each of these has a corresponding automated test, and the full suite passes after the changes.

## Unperformed / outstanding

- Manual browser interaction QA (click-through of the React UI) was not performed in this session; the frontend production build passes and API integration is exercised by the acceptance runner.
- Demo recording and public GitHub publication are user-owned submission actions.
- The Gemini live path depends on account quota/model access and was unreliable during testing; OpenAI was used for the recorded acceptance run.
