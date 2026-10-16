# ADR 0025: permission-scoped service transactions and explicit migrations

Date: 2026-10-04
Status: Accepted

## Context

Step 6 needs to connect the earlier Python and PostgreSQL packages to an HTTP service. Validation, permissions, session ownership, commit timing and schema evolution must agree. A route that returns success before committing or trusts a body/cursor namespace can contradict the storage contract. Academy account operations, learner execution and full deployment remain separate concerns.

## Decision

Publish eight ordered lessons from python-http-api-contracts through python-service-evidence, sixteen original scenarios under the separate Python service contracts skill and complete guided/diagram/glossary/recall layers. Catalog is 2026.10-service-v1; interactive/recall/rubric revisions are v11. Preserve earlier denominators, exams and submitted snapshots. Explanations use small runnable examples while distinguishing local illustrations from actual database evidence.

Provide academy-ingestion-service-lab 0.1.0, Python 3.13+, with nineteen authenticated starter files and three unfinished functions. Maintain references separately and exclude them/private answers from downloads. Runtime pins match the installed academy: FastAPI 0.141.1, Starlette 1.6.0, Pydantic 2.13.5, SQLAlchemy 2.0.43, Alembic 1.16.5 and psycopg2-binary 2.9.10. HTTPX/Uvicorn support local tests/server; pytest/mypy/stubs/Ruff/build are development tools. No academy dependency/schema or runner contract changes are needed. The academy serves bytes and stores reported/manual evidence; it never imports or executes learner packages.

The application borrows a configured PostgreSQL Engine and snapshots one to eight explicitly generated local token-to-single-namespace entries. Authentication precedes namespace validation/authorization; permission precedes opening a request Session. Use constant-time configured-token comparison, no default credential and no secret-bearing diagnostics. This local configured policy does not implement OAuth/account management or public auth readiness.

Strict Pydantic body models reject coercion and extra fields. Supplied frozen domain values revalidate exact bounded namespace/id/revision/value fields. Public responses contain chosen immutable data/counts, never ORM objects, internal timestamps or credentials. HTTP 200 is the explicit successful bulk receipt for both first and repeated delivery; no single-created-resource Location promise is made. Missing/invalid bearer is 401, forbidden scope 403, invalid input 422, changed fact 409 and storage/pool failure private 503. Handled responses use no-store and generated request IDs; fixed request logs contain trace/status only. A 503 does not prove non-commit or authorize automatic retry.

The dependency owns/closes one Session at function scope; synchronous routes use synchronous database I/O. Services reject an already active borrowed Session without mutating caller work, then own one explicit transaction. No dependency performs a late commit. Three unfinished functions specify:

- authorize authenticates the configured credential, validates namespace and returns only its permitted scope.
- ingest validates a list/tuple of at most 64 exact Datums before SQL. Provision the parent source safely, use full-key INSERT ON CONFLICT DO NOTHING RETURNING, and compare a duplicate's stored value under FOR SHARE. A returned zero still counts as an insertion. Changed/missing facts fail the entire batch, including newly created sources. Return Receipt only after successful commit; ordinary failures roll back while preserving previous committed facts and native chains.
- read_page validates exact limit 1..32 and an optional full Cursor, filters namespace on every page, orders C-collated id/revision and observes limit+1. Materialize allowed values inside the transaction. Return at most limit items, with the last returned key as the next cursor only when an extra row was observed. An unsigned position grants no permission and does not freeze changing data.

This is a dedicated append-only READ COMMITTED protocol, with no shared Session, external mutation/DDL or hostile schema replacement. Pool size/wait and item counts do not bound request bytes, full query work, storage or total operation time. Lost commit acknowledgment may be uncertain; database rollback excludes external effects. There are no automatic retries, durable delivery or exactly-once claims.

Package two explicit Alembic revisions: service_001 creates source/reading invariants; service_002 adds required server-default timezone-aware ingested_at. Migrate outside requests through an explicit caller-owned Engine transaction. The app never uses create_all or performs migration on import/request. Readiness checks the expected head separately from metadata drift. Downgrade to service_001 preserves key/value rows but loses timestamp metadata; re-upgrade assigns new timestamps. Base destroys lab tables and is exercised only in disposable schemas. Programmatic migration stdout is captured so guarded demo JSON remains parseable; errors remain visible through exceptions.

The guarded supplied serve.py binds loopback, requires private DSN/generated tokens and an already migrated schema, and owns engine disposal. The local DSN adapter requires explicit host/database/user and rejects unsupported options rather than dropping SSL requirements. TLS/provider/proxy deployment remains a later unit.

Trusted maintainer subprocesses build five real source archives/wheels from sdists, freshly install, check resources/quiet import/types and run all 70 public cases outside source against an owned digest-pinned PostgreSQL 17 container. The 43 offline/27 PostgreSQL-dependent cases distinguish skipped work from evaluation. Real checks cover permissions/strict input, direct constraints, late rollback, separate-reader visibility, caller-state preservation, actual pool exhaustion and migration rehearsals. A modeled pre-commit fault tests success ordering without claiming a real network commit incident. Actual JSON is saved/parsed exactly. Strict installed adaptation composes prior Record/Row/Reading/Snapshot values; a separate installed loopback TCP test starts/stops the supplied server. Unique owned container/network, tmpfs database, ephemeral loopback port and private temporary credentials stay outside academy data; cleanup targets only owned resources.

Four pinned manual criteria distinguish HTTP/input/output, authentication/scope, session/transaction failure and migration/installed review evidence. Local tests, reading/checklists, reported output and self/human review do not award mastery or certify expertise.

## Consequences and next unit

The first service integration is independently usable and reviewable. Competing transactions, lock order/isolation, bounded waits, retry classification and stable-key reconciliation are the next bounded unit. Joins/windows/JSONB/index plans, outbox/workers/recovery, release/deployment and applied AI remain open. Step 6 and full academy Compose/PostgreSQL operations remain incomplete; serial local evidence is not multi-writer stress or zero-downtime/backup proof.

## Primary references

- [FastAPI yield dependencies and function scope](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/)
- [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)
- [SQLAlchemy Session transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
- [SQLAlchemy PostgreSQL ON CONFLICT](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert)
- [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [HTTPX ASGI transport](https://www.python-httpx.org/advanced/transports/#asgi-transport)
