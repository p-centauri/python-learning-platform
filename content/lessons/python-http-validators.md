An ETag is a label for a selected representation. In this lab a strong tag is the SHA-256 digest of the exact JSON response bytes, wrapped in quotes. Sorting JSON keys and using fixed separators makes those bytes repeatable. Zero is a real value. The representation includes its version, namespace, limit, ordered items and next cursor. Changing one selected value changes its bytes and tag. A record outside this bounded page may leave its tag unchanged; that is correct because this tag describes the page, not the whole database.

The client first receives 200 and saves the body plus tag. Later it sends If-None-Match. For GET, a matching tag means 304 with no body. The client reuses the saved body. Weak tags beginning W/ also compare for this condition. A quoted tag may contain a comma, so splitting every comma is incorrect. The lab accepts bounded quoted lists or a lone wildcard, and rejects malformed, excessive or mixed wildcard lists with 400. Its bounded policy is narrower than a general HTTP parser.

Private data needs private caching. The new endpoint sends Cache-Control: private, no-cache and Vary: Authorization on both 200 and 304. Here no-cache permits storage but requires validation before reuse; it does not mean no-store. Authentication and namespace permission run before conditional validation and database reads. A stolen tag or wildcard cannot bypass them. A failed authorized database read returns 503 rather than a guessed 304. This reduces response transfer, not necessarily query work; each request still selects current bytes.

## Guided practice

Predict the printed value before running this small illustration. Then explain which part requires a real request or database observation.

```python
from hashlib import sha256
body = b'{"value":0}'
tag = "\"" + sha256(body).hexdigest() + "\""
print(tag == "\"" + sha256(body).hexdigest() + "\"")
```

## Independent practice

Implement matches in the downloaded API depth lab. Include weak/list/wildcard cases, commas inside quotes, empty tags and rejection of a seventeenth tag. Compare the exact body digest before and after inserting value zero.

## Check your work

Show a real 200 → bodyless 304 → changed 200 sequence. Show 401/403 with no ETag even when a wildcard is supplied. Reading this example alone does not observe a database or HTTP cache.

Continue with the [API depth lab](/projects#python-api-depth). Record commands and outcomes; keep private credentials out of submitted evidence.
