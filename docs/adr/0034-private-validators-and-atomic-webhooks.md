# ADR 0034 — Private validators and atomic local webhook receipts

Date: 2026-10-07
Status: Accepted

## Context

The fixed third step-six milestone requires conditional HTTP/cache semantics, signed webhook replay/duplicate handling and permission/failure contracts connected to simple teaching and actual installed requests. Earlier service/release/assessment contracts and learner history must remain stable. The academy must never execute learner code.

## Decision

Publish five ordered lessons, ten original scenarios under API delivery contracts, complete private guided/diagram/glossary/recall layers, a fourteen-file authenticated starter with three unfinished functions, 51 public cases and four manual criteria. Education stays outside React. Current content layers are v20; old exams/skills/frozen snapshots remain unchanged.

Add a separate installable academy-api-depth-lab depending on the completed delivery-release chain. The extension borrows a PostgreSQL Engine and copies configured bearer/signing maps. Factory/import/request performs no DDL/connect/disposal. Declare /v1 routes and compatible source-plus-receipt readiness before mounting unchanged old service routes. Preserve old items/zero/permissions/page/no-store/no automatic outbox and standalone readiness semantics.

GET selects canonical fixed ASCII JSON for its bounded namespace/limit page. Hash exact bytes for a strong quoted ETag. Authenticate/authorize before conditional/query/header validation or store access. Use weak/list/wildcard If-None-Match comparison and bodyless 304; both 200/304 send private, no-cache and Vary Authorization. Reject malformed/oversize/excess lists under a documented narrower lab policy. Error replies have no ETag/no-store. Each validation still reads; this saves transfer rather than claiming a cached database lookup. HEAD/update preconditions are outside this unit.

The academy-webhook-v1 frame signs the fixed protocol version, requested namespace, stable delivery ID, timestamp and original <=4096 byte body with a route-configured 32..64 byte key. This is an authored protocol, not a provider's wire format. Validate single auth headers, fixed v1 lowercase-hex digest, exact field syntax and +/-300 second supplied-clock freshness, then compare_digest. Parse strict duplicate-free UTF-8 JSON with exact bounded ints/version and no tenant/extra/coercion only after authentication. Body/media policies can reject earlier without event disclosure.

Use namespace/delivery unique receipt and authenticated raw-body digest in the same READ COMMITTED transaction as source/reading. ON CONFLICT waits/observes a committed winner; same digest succeeds as duplicate, different digest conflicts. Freshly re-signed stable bytes keep identity. Equal reading/new delivery stores another receipt; conflicting reading rolls the new receipt back. Respond after commit. Individual 250ms lock/1000ms statement bounds release transactions on failure; expected DBAPI/pool errors produce generic 503 without claiming a known no-commit outcome. Never automatically retry or enqueue an outbox intent. Logs expose generated trace/status only.

Explicit disposable fixture setup creates a generated source schema at delivery_004 and adds a receipt table. Teardown removes it, compares original source metadata and removes only the generated schema. No production schema migration/receipt deletion or academy migration/runtime/runner change. The trusted maintainer verifier builds nine archives/wheels, clean-installs outside source, tests types/imports/public cases and observes actual HTTPX requests through an owned ephemeral loopback Uvicorn server. The academy serves the fixed ZIP and saves reported/manual evidence only.

## Evidence

`.local/api-depth-20261007/`: fresh installed 51 passed/no skips (3.60s), actual PostgreSQL 17.11, loopback JSON readback, real duplicate competition/conflict/rollback/table-lock 503 and later retry, compatible prior routes/metadata and zero checked-out connections. Source has 39 passed/12 explicit live skips; seven strict-typed package/demo files pass. Focused academy/browser and preservation checks are recorded in the dated PROGRESS entry.

## Consequences and limits

A validator never grants access. no-cache permits storage but requires validation; no-store prevents storage. A plain hash is not authentication. Timestamp freshness and durable duplicate receipts solve different problems. Stable raw bytes are the retry identity contract, so semantically equal reformatted bodies conflict. Key holders can authenticate, not provide third-party nonrepudiation. Lost/503 replies can hide commit and require reconciliation. Removing receipt history loses deduplication. One local transaction cannot promise external exactly-once effects.

This finite local unit does not verify arbitrary provider formats, general HTTP conformance, TLS/proxy/hostile header or body memory bounds, rate/load controls, hard deadlines, secret rotation, production migration/retention/backups, full academy Compose or expertise. The borrowed factory has scoped readiness, not the release unit's admission/engine lifecycle ownership. Those boundaries remain explicit rather than changing previous packages. Step 6 remains open; next is Advanced Python practical review, followed by the five applied-AI milestones.

Sources: [RFC 9110 conditional semantics](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.2), [RFC 9111 cache directives](https://www.rfc-editor.org/rfc/rfc9111.html#section-5.2.2), [Python HMAC](https://docs.python.org/3.13/library/hmac.html), [GitHub raw-byte example](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries), [PostgreSQL INSERT](https://www.postgresql.org/docs/17/sql-insert.html).
