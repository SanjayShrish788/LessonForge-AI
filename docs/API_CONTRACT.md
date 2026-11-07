# Internal contract

Gemini receives a structural JSON schema. All original Pydantic bounds, duration checks, and citation checks remain enforced locally. Model changes require backend restart; model-unavailable errors preserve research.

All routes begin `/api`. JSON field names are snake_case. API errors use `{"detail":"readable message"}`.

`GET /health` returns `{status, providers:{llm:{configured,provider,model},web:{configured},books:{configured},youtube:{configured}}}`. No secrets.
`GET /lessons` returns an array of full lesson objects, newest first.
`POST /lessons` body `{title,learning_objective}` returns a saved draft (201).
`GET /lessons/{id}` returns lesson.
`PATCH /lessons/{id}` body `{expected_version,sections:[...]}` saves full section list, marks audits stale and increments content version. Must preserve max 45 minutes.
`POST /lessons/{id}/run` body `{stage:"all"|"research"|"generation"|"qc_research"|"qc_instructional"|"qc_both"}` returns 202 `{job_id}`. Poll GET lesson every 1.5 sec while status running. One job per lesson. Retries skip successful research/generation in all; generation never overwrites existing sections. QC reruns replace current report, history retained.
`GET /lessons/{id}/versions` returns `[{id,version,reason,created_at,sections}]`.
`POST /lessons/{id}/restore/{version_id}` body `{expected_version}` restores saved sections as new content version.
`POST /lessons/{id}/recommendations/{layer}/{issue_id}` body `{action:"apply"|"reject",expected_version}` returns lesson. layer is `research` or `instructional`. Apply requires proposed_content and unchanged original section content; no silent overwrite. Changes can be reviewed via issue fields before call.
`GET /lessons/{id}/export?format=pdf|markdown|json|zip&scope=lesson|research|instructional|package` returns download (zip package contains PDF, MD, JSON and reports).

Lesson shape:
```
{id,title,learning_objective,version,status:"draft"|"running"|"review"|"error",created_at,updated_at,
 sections:[{id,title,kind,content,minutes,source_ids:[]}],
 sources:[{id,title,author,url,source_type:"website"|"book"|"youtube",published_date,description,relevance,excerpt,evidence_kind:"full_text"|"snippet"|"metadata",retrieved_at}],
 research_warnings:[], provider_status:{},
 stages:{research:{status,error},generation:{status,error},qc_research:{status,error},qc_instructional:{status,error}},
 reports:{research:null|Report,instructional:null|Report},
 activity:[{at,message}], total_minutes:number}
```
Section kinds: overview, objectives, prerequisites, introduction, concepts, examples, applications, activity, knowledge_check, summary. References and supplementary videos rendered from sources (actual used IDs collected from sections); supplemental videos optional outside 45 minute core.
```
Report={id,layer,overall_assessment,alignment,limitations:[],issues:[Issue],claims:[Claim],lesson_version,created_at,stale}
Issue={id,severity:"Critical"|"High"|"Medium"|"Low",section_id,explanation,recommendation,evidence_source_ids:[],proposed_content:null|string,original_content:null|string,status:"pending"|"applied"|"rejected"}
Claim={section_id,claim,status:"verified"|"unsupported"|"uncertain",source_ids:[],evidence_quote,explanation}
```
`verified` must NEVER be assigned on model opinion alone. Prefer uncertain even with matched evidence unless actual verification is defensible.

Service interface owned by service agent:
`async research_service.research(title, objective, settings) -> dict {sources:list[dict],warnings:list[str],provider_status:dict}`
`async lesson_generator.generate(title, objective, sources, settings) -> list[Section]`
`async qc_research.audit(title, objective, sections, sources, settings) -> dict` (overall_assessment,alignment,limitations,issues,claims)
`async qc_instructional.audit(title, objective, sections, sources, settings) -> dict` same shape, different independent rubric.
Services raise `ServiceError` from app.services.errors with safe message; routes manage persistence, reports metadata, ids and jobs.
Root owns app/schemas.py, config.py, database.py, main.py, models.py, workflow.py, export_service.py. Agent owns remaining services. Settings fields: llm_provider,openai_api_key,openai_model,gemini_api_key,gemini_model,tavily_api_key,google_books_api_key,youtube_api_key,request_timeout, llm_timeout, max_sources_per_provider.
