# Instructor review checklist

AI-generated lessons and QC reports do not replace instructor approval. See [the claim and QC audit](CLAIM_AND_QC_AUDIT.md) for individual findings and source limitations. The checkboxes below are intentionally unchecked. Verify the current saved versions in the application; the historical `artifacts/openai-acceptance/` files represent earlier versions.

## HTTP Requests and Responses — version 8, 42 minutes

- [ ] Check safe and idempotent semantics and the distinction between intended effects and incidental side effects. [RFC 9110 §9.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2)
- [ ] Check POST, query parameters, request content, limits and caching. [RFC 9110 §9.3.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.3)
- [ ] Check 2xx, 4xx, 5xx and individual codes, especially 401/403 and nondisclosing 404. [RFC 9110 §15](https://www.rfc-editor.org/rfc/rfc9110.html#section-15)
- [ ] Review the examples, Node/Express exercise, timing and knowledge-check answers for the intended learners. The sample server has not been executed in this review.
- [ ] Review the current three factual and four instructional findings, including the critical clarity finding. Decide whether further examples, measurable objectives and assessment guidance are needed.
- [ ] Check claim-level citations. RFC links in lesson prose are direct links, not retrieved source records; factual QC only assesses supplied source excerpts. Older RFC 2616 records remain as historical research, but were removed from section source lists.

Comments: ________________________________________________
Decision: [ ] Approve  [ ] Reject / revise   Reviewer: __________ Date: __________

## Java inheritance and polymorphism — version 8, 43 minutes

- [ ] Verify superclass/subclass direction, single class inheritance, multiple interfaces, overriding, overloading, dynamic dispatch and covariant returns. [Java Language Specification, classes](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html); [Oracle overriding guidance](https://docs.oracle.com/javase/tutorial/java/IandI/override.html)
- [ ] Inspect all four code blocks and compare expected results. They compiled and ran in this workspace; an instructor should assess clarity and pacing.
- [ ] Review seven factual findings and one instructional finding in the current reports. In particular, confirm the single-superclass/multiple-interface explanation and decide whether examples need further teaching commentary.
- [ ] Check whether each cited section source actually supports its claims; some citations are general secondary sources, and source discovery is not claim verification.

Comments: ________________________________________________
Decision: [ ] Approve  [ ] Reject / revise   Reviewer: __________ Date: __________

## Final sign-off

[ ] Both lessons and current reports reviewed   [ ] Timing suitable for learners   [ ] Sources and exports checked

Instructor signature: _________________________ Date: __________
