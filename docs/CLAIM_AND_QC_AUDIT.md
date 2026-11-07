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

## Subsequent PDF and accessibility verification

- Rendered all 10 pages of HTTP v8 and all 12 pages of Java v8 to images and reviewed page overviews, including detailed views of the HTTP status table and both exercise code pages. No obvious clipping or missing section was seen in these views. Small code and reference text may require zoom; this is not a substitute for a print review.
- Enumerated and requested all 20 unique HTTP and 18 unique Java PDF link destinations. RFC 9110, MDN and Oracle/JLS links returned HTTP 200; the RFC section fragments and JLS constructor fragment occurred in their retrieved pages. Three Medium URLs returned 403, so their contents and support for claims remain unverified. Successful book/video links establish reachability only, not review of their contents.
- Current Oracle [JComponent documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/javax/swing/JComponent.html) supports common Swing component ancestry and painting infrastructure. The original section citation itself is not thereby verified. RFC 9110 and the JLS provide authoritative evidence for the central HTTP and Java language claims above; not every section-level citation has been proved to entail its associated claims.
- The lesson tab controls now expose tab-to-panel relationships. On the running application, ArrowRight moved focus and selection from Lesson to Sources and the accessibility tree named the selected panel. The lesson outline now requests non-animated scrolling when reduced motion is preferred. Actual assistive-technology testing and browser emulation of reduced motion were not performed in this follow-up; full contrast coverage remains unverified.
- Backend regression: 47 passed, one Starlette deprecation warning. Frontend Vite production build passed. These checks do not establish instructor approval or complete citation verification.

## Section-by-section citation disposition (HTTP v8 and Java v8)

This review separates source attribution from correctness. A direct primary-source link can support a claim even if the structured section source points elsewhere; it does not prove that the separately cited source supports it. The unavailable sources below remain unresolved, not verified.

| Lesson section | Claim and attribution assessment |
| --- | --- |
| HTTP overview, objectives, prerequisites | Introductory scope, objectives and prerequisites; no external factual citation assigned. |
| HTTP introduction | Message structure supported by the direct RFC 9110 §6 link. The assigned Medium source returned 403; attribution unverified. |
| HTTP concepts | GET/POST and safety supported by direct RFC 9110 §§9.2 and 9.3.3; status meanings by §15 and the assigned MDN status reference. MDN's status page does not itself substantiate every method or caching claim. |
| HTTP examples | Illustrative request/response examples; RFC method/status definitions support the examples in principle, while the assigned MDN source supports status meanings only. The assigned Medium article returned 403. |
| HTTP applications | Status meanings supported by RFC §15. The assigned Shine article is topically related to choosing status codes; the exact broad teaching claims have not been matched to it. |
| HTTP activity | An illustrative Express exercise; the assigned Medium source returned 403 and has not been shown to support the exact exercise. Running the server remains optional and was not verified here. |
| HTTP knowledge check | The assigned MDN status reference supports the status answers; GET safety and idempotency are supported separately by RFC §9.2. |
| HTTP summary | Direct RFC link supports core method and status claims. Assigned Medium citation returned 403 and is unverified. |
| Java overview, objectives, knowledge check | Core inheritance and dispatch concepts have independent Oracle/JLS support. The assigned Scribd presentation was reachable but its complete contents and claim-level support were not verified. Objectives are instructional rather than empirical claims. |
| Java prerequisites, introduction, exercise | The assigned Medium article returned 403. Prerequisites and the illustrative exercise do not establish claims about the inaccessible source. General OOP concepts are independently supported by Oracle guidance and the JLS. |
| Java key concepts | One superclass, interfaces, constructors and method selection/dispatch have JLS support; direct Oracle/JLS links are present. The assigned Oracle tutorial supports polymorphic instance dispatch but not every concept. The Medium source returned 403 and complete Scribd support is unverified. |
| Java code examples | Earlier local compilation and output checks support the sample behavior. The assigned Medium and Scribd sources were not verified as support for these exact examples; JLS §§8 and 15 provide independent language rules. |
| Java applications | The Swing component hierarchy and painting infrastructure have independent Oracle JComponent support; the GameObject case is hypothetical. The assigned AlgoCademy page was reachable but its exact support for Swing, the hypothetical game and framework claims has not been established. |
| Java summary | Assigned Oracle polymorphism tutorial supports subclass overriding and polymorphic behavior; wider inheritance and reuse claims require the independent JLS links and design judgment rather than a guaranteed benefit. |

No lesson content, version, audit report, or source record was changed for this documentation-only assessment. A teacher should replace or review weak section-level citations before relying on them as claim-specific evidence.

## Accessibility retest

Headless Chrome was exercised with reduced motion enabled at widths 390, 768 and 1440 pixels: document width did not exceed the viewport, transition duration was 0.00001 seconds, and selecting an outline link requested `auto` rather than smooth scrolling. The Connections dialog was found by its accessible name and closed with Escape. A targeted computed-color sweep of visible lesson text, links and buttons at desktop width flagged no candidates after contrast fixes; this heuristic does not cover all states, transparency, images, or every screen. Earlier keyboard tab navigation and accessibility-tree checks passed. A real screen reader was not operated, so spoken output and end-to-end assistive technology behavior remain unverified.

## Saved Medium evidence follow-up

The current Medium URLs returned 403 on direct retrieval, but the preserved lesson research snapshots include text collected earlier. The HTTP article's saved 14,000-character excerpt contains substantive discussion of HTTP, GET, POST, status codes and an Express task API. It supports those general topics and is relevant to the section examples and activity; it does not by itself substantiate every detail in the lesson. The Java article's saved 14,000-character excerpt contains substantive explanations and examples of inheritance, overriding, overloading and runtime polymorphism. It supports those general topics but does not establish support for every Java section or for the lesson's exact examples. Despite the stored `full_text` label, the fixed-length excerpts do not prove the whole articles were retrieved or reviewed. The other Java Medium discovery source contains only a 140-character snippet and is not assigned to a lesson section. These saved excerpts are not authoritative specifications; use RFC 9110 and the JLS for normative claims.

The available computer interface exposes accessibility-tree information but not Narrator's spoken output; an actual screen-reader listening test cannot be verified through it. The earlier named-dialog, keyboard, reduced-motion and targeted contrast tests remain the evidence available.
