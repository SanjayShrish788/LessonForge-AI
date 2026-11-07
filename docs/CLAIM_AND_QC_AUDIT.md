# Lesson claim and QC review — 7 November 2026

Historical scope: HTTP v6 and Java v7. The latest locally saved lessons are HTTP v8 and Java v8; earlier version-specific findings below are retained as history. Current reports contain HTTP 3 factual / 2 instructional and Java 7 factual / 1 instructional findings; review these in the application. This is a targeted review of consequential claims and every current QC issue, not a claim that every cited third-party source was fully accessible or every teaching benefit proven. Source presence, topical relevance and support are distinct. Books/videos were not read or viewed; discovery metadata is not evidence.

## HTTP claims

| Claim / section | Evidence and decision |
| --- | --- |
| Message method, target, fields, optional content; response status | [RFC 9110 §6](https://www.rfc-editor.org/rfc/rfc9110.html#section-6) exists and is authoritative for the HTTP message abstraction. The lesson's direct link is relevant and supports this claim. The separately listed Medium section source could not be fetched during this review; its support is unverified. |
| GET safe and idempotent, logging and incidental side effects | [RFC 9110 §9.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2) supports the intended semantics and allows incidental effects. The RFC link is attached in concepts; it is not a retrieved source record for the AI auditor. |
| POST processing, query versus content, repeat safety, body limits and cache conditions | [RFC 9110 §9.3.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.3) supports POST processing and cache qualifications. URI query and content are distinct parts of HTTP; no universal method-level payload limit is stated. The assertion that reuse is rare is contextual and should be retained as a qualified observation, not a guarantee. |
| 2xx/4xx/5xx, 200, 201, 400, 401, 403, 404, 500, 503 | [RFC 9110 §15](https://www.rfc-editor.org/rfc/rfc9110.html#section-15) and the linked [MDN status reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status) are relevant and support the listed meanings. 403 does not require proof of valid credentials; 404 can conceal existence. |
| GET/POST examples and Express exercise | These are illustrative application-specific examples; response status selection is consistent with RFC 9110. The Express code was not executed here and its eight-minute feasibility requires instructor judgment. The Medium citation could not be retrieved to establish exact support. |
| 404 and success examples in applications; knowledge check; summary | RFC 9110 supports status semantics. The Shine Solutions page listed in applications could not be fetched in this review; its support is unverified. A status response does not itself guarantee a smooth user experience. The section-level source is broad, not a claim-specific citation. |

## Java claims

| Claim / section | Evidence and decision |
| --- | --- |
| Subclass, superclass, single class inheritance and multiple interfaces | [JLS §8.1.4–8.1.5](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html#jls-8.1.4) exists and supports one direct superclass and multiple superinterfaces. The lesson states this in concepts; Java does not support multiple inheritance of classes. Inheritance may enable reuse; it does not guarantee reduced redundancy. The absolute benefits wording should be reviewed by the instructor. |
| Overload selection and dynamic dispatch | [JLS §15.12](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.12) distinguishes compile-time method selection and runtime invocation. Existing compiled examples support their stated output. |
| Overrides, static hiding and covariant return | [Oracle overriding guidance](https://docs.oracle.com/javase/tutorial/java/IandI/override.html) exists and supports these distinctions. It is explicitly labeled JDK 8-era; the JLS is the preferred normative reference. |
| Polymorphic parent reference | [Oracle polymorphism tutorial](https://docs.oracle.com/javase/tutorial/java/IandI/polymorphism.html) supports dynamic instance-method dispatch and is cited in concepts/summary. It is JDK 8-era. |
| Swing, `GameObject` and interfaces in applications | `GameObject` is a hypothetical example, not a claim of an existing implementation. Swing's common component hierarchy is plausible, but the exact rendering claim and AlgoCademy support were not independently verified; that page could not be fetched. Review or replace the section-level citation before sign-off. |
| Reuse, efficiency and maintainability benefits | Benefits are context-dependent design judgments, not consequences guaranteed by the language specification. Overview qualifies the claim; concepts still says “reduces redundancy” categorically. Instructor review needed. |
| Section references | Scribd page exists and is topically relevant, but is not an authoritative language specification. The Medium page was reachable as a rewritten summary and is topically relevant; that does not establish support for every cited section. Oracle source is authoritative but not attached to all relevant example sections. Citation completeness remains open. |

## Disposition of current QC findings

### HTTP

1. **Factual, introduction unassessed:** manually checked against RFC §6 above; the report remains unchanged as history.
2. **Instructional critical, concepts clarity:** the status table does separate families and the examples/activity show GET/200 and POST/201. The finding overstates their absence, but its suggestion for more explicit scenarios is reasonable; retain for instructor pacing judgment rather than blindly replace the section.
3. **Objectives measurable:** existing verbs and examples are observable, although a scenario-based criterion could improve assessment. Retain for instructor judgment.
4. **Knowledge-check rationale:** five answers include explanations, but no grading rubric or distractor analysis. Retain as a genuine optional instructional improvement.

### Java

1. **High, multiple inheritance/reuse:** one superclass and multiple interfaces are already explicitly stated. The categorical benefit sentence could be softened; retain as a real clarification for instructor review.
2. **Examples lack overloading:** an actual `Printer.show(int)` / `show(String)` example is present and has been compiled; this part of the finding is not supported by the current section. More discussion of implications may still help.
3. **Applications need detail:** a valid instructional depth suggestion, not proof of a factual error; support of the cited third-party source remains unverified.
4. **Concepts claim unassessed:** manually checked core language claims against JLS and Oracle links above; benefits remain qualified as noted.
5. **Applications claim unassessed:** source and Swing-specific rendering claim remain unverified as above.
6. **Instructional example commentary:** key points and overload explanation exist. Additional beginner commentary is a defensible suggestion, not an established factual error.

No report findings were silently deleted or applied. Instructor approval and full citation-to-claim verification remain pending.

## Latest content changes

HTTP v7 adds explicit scenario objectives and makes running the Express server an optional extension to the timed activity. Java v8 qualifies reuse benefits and adds constructor and access notes. The original primary-source links above remain relevant; exact support of each section-level source and the new direct JLS reference in structured QC evidence still require verification. Current report findings were not suppressed.

## Focused verification of HTTP v7 and Java v8

- The latest PDF link annotations were enumerated and queried: 20 unique HTTP links and 18 unique Java links. All RFC 9110, MDN and Oracle/JLS URLs returned HTTP 200 or 206; three Medium URLs returned 403 to the automated client, so availability and claim support there remain unverified. Other URLs returned 200/206; YouTube/Books HTTP responses establish reachability only, not video/book contents or factual support. URL fragments were not individually checked for every link.
- HTTP v7: RFC 9110 sections 6, 9.2, 9.3.3 and 15 support the central message, method and status claims. The application section's implication that a successful status ensures a smooth experience is stronger than the evidence; the cited Shine Solutions source was reachable but its support for that assertion has not been established. The Medium source returned 403. Instructor should qualify or remove the broad user-experience claim.
- Java v8: JLS §8.1.4–8.1.5 and §8.8 support the one-superclass, interfaces and non-inherited constructor claims; Oracle's overriding documentation supports instance overriding, static hiding and covariant returns. The application section's Swing rendering claim and its AlgoCademy source have not been fully matched claim-to-source; the `GameObject` example is hypothetical. Scribd is a weak secondary source and Medium returned 403. The benefits wording is now qualified in v8; older concerns above refer to v7.
- These checks do not establish claim-level support for every existing section reference. Books and videos were not reviewed as content. The direct RFC/JLS links in lesson prose are not structured source records available as retrieved evidence to factual QC.

## Follow-up: HTTP v8 and keyboard QA

HTTP v8 replaces the unsupported assertion that status codes ensure a smooth user experience with the narrower statement that they provide useful information for clients and debugging. RFC 9110 section 15.3 defines successful responses; it does not guarantee user experience. The edit used the versioned workflow and preserves prior snapshots. The v8 factual and instructional reports independently assess v8 and are not stale (3 and 2 findings respectively); findings remain recommendations for review, not verified errors.

Oracle's [JComponent documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/javax/swing/JComponent.html) describes the paint method calling paintComponent, paintBorder and paintChildren; it supports the general Swing rendering mechanism, but the existing section-level AlgoCademy citation was not verified for every claim. Weak and inaccessible citations, claim-to-section attribution, unreviewed videos/books and the limitations above remain open.

HTTP v8 exports were generated from the local API into artifacts/qa-http-v8. JSON parsed and the ZIP integrity check passed; the PDF was generated but its current annotations and page layout were not individually re-inspected. Earlier PDF URL checks apply to the earlier versions described above, not automatically to this new PDF.

At tablet width, keyboard ArrowRight, End and Home were executed on the workspace tabs and focus and selection followed. A full screen-reader, all-controls contrast, and reduced-motion behavioral audit remain unverified.
