## The idea in plain language

An API is an agreement about requests, responses and failures. State the method, path, headers, input shape, output fields and error statuses before writing a route. HTTP is more than calling a Python function: clients may retry, lose a response or use intermediaries.

The lab uses POST /namespaces/{namespace}/readings for one bounded batch and GET the same path for a page. JSON is the documented representation. POST returns 200 with observed/inserted/duplicates after commit, whether a first delivery or exact repeat. A bulk receipt is not a single newly created resource, so this API does not invent a Location header or promise 201 for every call. Other APIs can choose different explicit contracts.

GET should not create a source or write a reading. Missing/invalid credential is 401 with a Bearer challenge; a known credential without namespace permission is 403; invalid input is 422; a changed fact under the same key is 409. Storage failure is a private 503. A 503 or lost response does not guarantee the server stored nothing: reconcile using stable identities before a later retry policy.

Return an explicit public DTO (data transfer object), not the database entity. The lab receipt contains counts; its page contains id/revision/value and a continuation position. Internal ingestion timestamp, tenant discriminator and credentials are omitted. Each handled response uses no-store, and a generated request ID helps match a response to a safe fixed log event.

The Python illustration names this public result; it does not perform HTTP. The installed lab verifies real ASGI requests against PostgreSQL and separately a local TCP server. DNS, TLS, proxies, cache revalidation, public ingress controls and webhook delivery are later connected units. An accepted item count does not bound the bytes read before JSON parsing.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
receipt = {"observed": 3, "inserted": 2, "duplicates": 1}
print(receipt["observed"] == receipt["inserted"] + receipt["duplicates"])
print(sorted(receipt))
```

## Guided practice

Explain successful bulk receipts and specific failure meanings without assuming that every network error proves rollback.

## Independent practice

Run first/repeated POST, a GET and the changed-value conflict. Record actual statuses and public fields from the local lab.

## Check your work

GET stays read-only; success follows commit. Output filtering and no-store do not replace permissions.

Continue to [Strict request models & trusted output fields](/lessons/python-pydantic-boundaries).
