# Build contract

## Domain and invariants

Use organizations, memberships, products, stock, orders, order lines, idempotency receipts, outbox, inbox and fulfillment. Tenant is part of every business key. Store exact integer minor units plus currency. Stock is never negative. One request key cannot identify two bodies. Order, stock and intent commit together. Fulfillment is one durable effect per full event identity.

## API acceptance

POST /orders accepts {key,sku,qty}; derives tenant from a real session/token. First success returns 201 and a stable receipt; identical retry returns 200 and the same order; changed body with the same scoped key returns 409. Bad positive integer/currency fields return 422. GET /orders/{id} and /orders use current membership, scoped keys and bounded keyset pages. Foreign/unknown IDs return the same 404 shape; no private fields leak. POST webhook has a verified signature, timestamp policy and replay identity. Do not trust a supplied role/tenant.

## Database and concurrency

Create PostgreSQL migrations with full keys, constraints and indexes. Conditional reservation or an explicit lock must prevent two connections selling the last unit. Record order and outbox in the same transaction. Test simultaneous writers using a barrier and distinct connections, request conflicts, rollback and uncertain commit reconciliation. SQLite cannot substitute for this evidence.

## Worker and delivery

Use Celery/Redis with documented at-least-once behavior. Commit inbox plus protected fulfillment together. Test actual process exits before commit, after commit/before ack and stale lease settlement. Bound retries/deadlines, quarantine poison and explain redrive. External payments need destination idempotency/reconciliation; a local inbox alone is insufficient.

## Cache and HTTP

Use tenant/permission/version-aware keys. Specify invalidation and the Redis-down fallback. Define ETags/preconditions and page semantics. Check query counts and actual plans at a stated data size. Cache failure must not bypass permission or trigger unlimited retries.

## Release and operations

Ship a non-root API/worker Compose deployment, expected schema/readiness checks, migration procedure and CI with independent regression cases. Emit safe IDs, finite failure categories, latency and job age; omit tokens and private payloads. State a workload and p50/p95/p99/errors. Restore a backup to an isolated database and check invariants; record RPO/RTO and a compatible rollback. Do not call a written runbook a tested restore.

## Failure matrix

Required: foreign tenant collision; last-unit race; conflicting request key; malformed money/quantity; rollback between writes; lost HTTP response; commit-before-ack redelivery; poisoned event; worker process exit; Redis outage; webhook signature/replay; stale cache/ACL; migration mismatch; dependency timeout; restore with dangling/duplicate effects.

## Final review packet

Use the four existing rubric criteria: contract, transactions, worker, operations. Link exact commits/files and commands/output for every claim. Include a diagram, permission matrix, OpenAPI examples, schema/migrations, concurrency and crash transcripts, measured release report, restore evidence and residual risks. Invite a registered reviewer; revise separately after feedback.

## Libraries and abilities

- FastAPI and Pydantic: typed HTTP contracts and strict input/output
- SQLAlchemy and Psycopg: transaction/session ownership and PostgreSQL behavior
- Alembic: versioned upgrades and compatible rollback
- Redis and Celery: measured caching, worker delivery and failure recovery
- pytest and HTTPX: API, concurrency and regression cases
- Docker/Compose and CI: reproducible runtime and observed release

## Official references

- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy session ownership](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
