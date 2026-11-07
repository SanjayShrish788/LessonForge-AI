"""Apply reviewed acceptance lesson changes through the versioned local API.

Run once against the original version-5 lessons. Historical exports are not changed.
"""
import httpx

BASE = "http://127.0.0.1:8000/api/lessons/"
HTTP = "0eadb494-0ead-4735-a2fb-0bf9759ccc4e"
JAVA = "c106ae93-772a-4bef-9c68-8cc267ddc17d"

with httpx.Client(timeout=30) as client:
    for lesson_id in (HTTP, JAVA):
        response = client.get(BASE + lesson_id)
        response.raise_for_status()
        lesson = response.json()
        if lesson['version'] != 5:
            raise RuntimeError(f"Unexpected version for {lesson_id}; no edit made")
        sections = {section['kind']: section for section in lesson['sections']}
        if lesson_id == HTTP:
            sections['introduction']['content'] = ("HTTP is an application-layer protocol for requests and responses on the Web. "
                "A request has a method, target, fields (headers), and sometimes content; a response has a status, fields, and sometimes content. "
                "HTTP/1.1 examples below show a start line, headers, a blank line and, where present, a body. "
                "[RFC 9110, message abstraction](https://www.rfc-editor.org/rfc/rfc9110.html#section-6)")
            sections['concepts']['content'] = '''### Methods
- **GET** requests a representation. Its defined semantics are **safe**: the client does not request a state change. GET is also **idempotent**: repeating identical requests has the same intended effect as one. Safety concerns the intended action; idempotency concerns repetition. Servers may log requests or behave incorrectly, so neither guarantees zero side effects. [RFC 9110: safe and idempotent methods](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2)
- **POST** submits content to the target resource for processing, such as a form or creation request. The target URI can also contain query parameters; these are distinct from the request body. POST is not generally safe or idempotent. Repeating it can create duplicates. [RFC 9110: POST](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.3)
- No universal POST body-size limit is specified by HTTP; servers and intermediaries can impose their own limits. GET responses are commonly cacheable when caching rules permit. POST responses are cacheable only under explicit conditions and are rarely reused. [RFC 9110: POST caching](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.3)

### Response status categories
| Code | Meaning |
|---|---|
| 2xx | The request was successfully received, understood and accepted. |
| 200 | OK; the response meaning depends on the method. |
| 201 | Created; the request resulted in one or more new resources. |
| 4xx | The server considers the request to have a client error. |
| 400 | The server cannot or will not process the request because of a perceived client error. |
| 401 | Valid authentication credentials are missing; the response includes a challenge. |
| 403 | The server understood the request but refuses to fulfill it; authentication alone may not resolve it. |
| 404 | No current representation was found, or the server is unwilling to disclose that one exists. A server may conceal a forbidden resource with 404. |
| 5xx | The server is aware it erred or cannot perform the request. |
| 500 | An unexpected server condition prevented fulfillment. |
| 503 | The server is temporarily unable to handle the request, often due to overload or maintenance. |

[RFC 9110: status codes](https://www.rfc-editor.org/rfc/rfc9110.html#section-15)'''
            sections['knowledge_check']['content'] = '''1. What does a 404 establish? **Answer:** The server did not find a current representation or will not disclose one. It does not prove the resource never existed.
2. Which is intended for retrieval: GET or POST? **Answer:** GET. It is safe and idempotent in its defined semantics; server-side logging may still occur.
3. A request creates a resource. Which status can indicate creation? **Answer:** 201 Created. POST is one possible method; 201 is not limited to POST.
4. How do 401 and 403 differ? **Answer:** 401 indicates missing or invalid authentication credentials and provides a challenge. 403 means the server understood the request but refuses it; the cause is not necessarily authentication.
5. What distinguishes 4xx from 5xx? **Answer:** 4xx denotes a perceived client error, while 5xx denotes a server error or inability to perform the request.'''
            sections['summary']['content'] = ("GET requests a representation with safe and idempotent semantics; POST submits content for processing and is not generally idempotent. "
                "2xx indicates success, 4xx a perceived client error, and 5xx a server error. "
                "Interpret individual statuses in context, particularly authentication (401), refusal (403), and nondisclosure or no current representation (404). "
                "[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)")
            for section in lesson['sections']:
                section['source_ids'] = [sid for sid in section['source_ids'] if sid not in {'website-2815718193a1', 'website-5cbe1ace8bb9'}]
            sections['concepts']['source_ids'] = ['website-fa4eaaea98a4']
        else:
            sections['concepts']['content'] += '''

### Java details
A class has one direct superclass (except `Object`) and may implement multiple interfaces. Interfaces describe a type and can provide default methods; a class uses `implements` to provide required behavior. [Java Language Specification: classes](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html)

Overloading selects an applicable method signature at compile time using the declared types of arguments. Overriding supplies an instance-method implementation in a subclass; dynamic dispatch selects the implementation at runtime based on the actual object. Static methods are hidden, not overridden. An override may return a compatible subtype (a covariant return). [Oracle: overriding](https://docs.oracle.com/javase/tutorial/java/IandI/override.html)
'''
            sections['concepts']['content'] = sections['concepts']['content'].replace('Multiple methods with the same name but different parameters in the same class.', 'Methods with the same name and different parameter lists, including inherited overloads.')
            sections['concepts']['source_ids'] = list(dict.fromkeys(sections['concepts']['source_ids'] + ['website-8cfb6f859f4b']))
            sections['activity']['content'] += '\n\n**Self-check:** Verify that both subclasses extend `Vehicle`, each override is annotated, the variables have the parent type, and both printed lines match the expected output.'
        response = client.patch(BASE + lesson_id, json={'expected_version': lesson['version'], 'sections': lesson['sections']})
        response.raise_for_status()
        updated = response.json()
        print(updated['title'], 'version', updated['version'], 'minutes', updated['total_minutes'])
