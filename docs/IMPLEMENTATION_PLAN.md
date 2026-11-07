# LessonForge AI implementation plan

Build a local React/Vite/Tailwind interface and FastAPI/SQLAlchemy/SQLite service. No external deployment is required.

1. Define validated shared data shapes and API contract.
2. Implement configurable real Gemini/OpenAI, Tavily, Google Books, and YouTube adapters; record partial research failures without inventing sources.
3. Persist staged research, generation, independent factual/instructional audits, versions, and instructor decisions.
4. Build dashboard, creation, editor/preview, source library, audits with proposed changes, history, and exports.
5. Test core workflows with explicitly mocked providers, then attempt the two specified live lessons when credentials permit. Report blocked live checks accurately.
6. Produce README, demo script, evidence, and submission packaging instructions.

Integrity constraints: retrieved metadata is not verified evidence; AI assessments are not factual verification; a matched source quote only confirms textual evidence. Manual edits require optimistic version checks. Retrying a stage must preserve successful prior work.
