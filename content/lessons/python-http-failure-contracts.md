A useful API contract describes failures as clearly as success. For the private snapshot, no accepted bearer gives 401 with a Bearer challenge. A valid bearer for another namespace gives 403. After permission succeeds, invalid limit fields give 422 and malformed bounded conditional headers give 400. Authentication precedes those checks. A forbidden request must not become a 304 or reveal the selected ETag. Hashes can reveal whether data changed, so an error response should not publish one.

For the webhook, unknown route signing authority, missing or duplicate authentication headers, bad signature and stale timestamp all give generic 401. Unsupported media type or content encoding gives 415; a body exceeding 4096 bytes gives 413 while streaming. An authenticated invalid event gives 422. Delivery identity or reading identity conflicts give 409. A database or connection-pool failure gives generic 503. All error and webhook replies use no-store. The application logs a generated request ID and status, never tokens, signing keys, raw SQL exceptions or payloads.

A 503 does not prove that a commit never happened. The response can fail after storage accepted the transaction. The sender should retry the same identity and bytes with a fresh signature, then reconcile the committed receipt. Blindly generating a new delivery identity weakens that protection. A 409 signals conflicting meaning and should be investigated; repeatedly changing identity to bypass it is not recovery. The lab does not automatically retry failures or promise a hard total deadline.

The new /v1 routes mount the earlier ingestion service unchanged. Its strict items envelope, exact zero values, authorization, keyset output and no-store behavior remain. The parent supplies compatible delivery_004 readiness plus a receipt-table shape check; old standalone readiness still expects service_002. An application factory borrows the configured engine and copies token/key maps. It does not connect, migrate or dispose the engine. Explicit fixture setup owns DDL and cleanup outside requests. Broader public API release/versioning, key rotation and proxy enforcement remain separate work.

## Guided practice

Predict the printed value before running this small illustration. Then explain which part requires a real request or database observation.

```python
statuses = {"missing_identity": 401, "wrong_scope": 403, "conflict": 409, "store_failure": 503}
print(statuses["store_failure"])
```

## Independent practice

Build a request/status matrix for both new routes and the old service. Use a real locked receipt table to observe 503 and a later successful retry. Verify absence of ETag and private fields on failures, and connection release after each case.

## Check your work

Distinguish an actual observed request from a status lookup. Preserve original readiness/business expectations rather than rewriting them to satisfy the new path.

Continue with the [API depth lab](/projects#python-api-depth). Record commands and outcomes; keep private credentials out of submitted evidence.
