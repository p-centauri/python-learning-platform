# ADR 0024: explicit PostgreSQL transaction and identity contracts

Date: 2026-10-04
Status: Accepted

## Context

Step 6 needs persistence after local ingestion, typing and measurement units. Python validation alone does not protect direct database writers. Repeated delivery requires a stable key and a changed-value rule; transaction ownership must not commit/rollback unrelated caller work. The full academy deployment is a separate operational concern.

## Decision

Publish eight ordered lessons from python-relational-keys to python-persistence-contracts, sixteen original scenarios under Python persistence contracts and complete guided/diagram/glossary/recall layers. Catalog is 2026.10-persistence-v1; interactive/recall/rubric are v10. Preserve earlier skill denominators, exam definitions and frozen histories.

Provide academy-ingestion-persistence-lab 0.1.0, Python 3.13+, psycopg2-binary 2.9.10 (the existing academy driver). types-psycopg2 2.9.21.20260911 is development-only. The eleven-file authenticated allowlist excludes maintained references and private answers. schema.sql/py.typed are packaged resources. The API serves bytes/stores manual evidence and never imports/executes learner packages or controls this lab database.

The supplied frozen Reading uses exact bounded ASCII namespace/id, exact revision 1..8 and value 0..1000000. The schema independently enforces primary/composite keys, parent foreign key, NOT NULL and named CHECK constraints. Python type distinctions are not assumed to be identical to SQL storage/adaptation rules. Provisioning is separate from request functions; SQLAlchemy/Alembic integration is a later unit.

Three unfinished functions specify ownership and limits:

- snapshot_batch borrows one input, preserves references/order/duplicates and accepts at most 64 exact revalidated Readings. Observe the 65th to establish overflow; never close input. Iterator errors remain original.
- persist_batch validates before database access, requires open idle non-autocommit explicit READ COMMITTED and owns one new transaction/cursor on a caller-owned connection. Rejected active/failed/wrong-mode state is untouched. Fixed statements bind values separately. Source insertion is conflict-safe; reading INSERT ... DO NOTHING RETURNING determines insertion, then a full-key FOR SHARE value comparison distinguishes exact repeat from conflict. A changed/missing fact raises ConflictingReading. Whole-batch rollback includes new sources; only after successful commit return observed/inserted/duplicates.
- load_namespace uses the same owner/preconditions, fixed parameterized ORDER BY id COLLATE "C", revision LIMIT 65 and returns at most 64 complete Readings. Overflow fails with rollback; read does not provision a source.

This is a dedicated append-only protocol: no concurrent use of one connection or external update/delete/truncate/DDL/search-path substitution. Database constraints arbitrate keys but finite serial evidence is not multi-writer stress proof. Namespaces/parameters are not authorization. Count bounds are not operation deadlines, storage/memory/query-work budgets. Input/remote effects are not database rollback. Broken rollback preserves native chains; lost commit acknowledgment may have unknown outcome and requires reconciliation rather than automatic retry/exactly-once claims.

Trusted maintainer subprocesses build four source archives/wheels (prior ingestion/object/typing and persistence), install freshly, run 57 public cases outside source against one owned digest-pinned PostgreSQL 17 container, check resources/quiet import/types and compose Record/Row into persisted Readings and Snapshot without changing earlier packages. The helper owns a unique container/network and tmpfs database; loopback publishes an ephemeral port and credentials stay in mode-0600 temporary configuration, never printed. It removes only its own resources. Learners explicitly configure a disposable database; absent DSN causes labelled skips, never a fabricated result. Existing isolated coding runner is unchanged.

Four criteria separate model/constraints, owner/failure evidence, duplicate/read contracts and actual installed integration. Manual submissions, reported output and finite checks do not award mastery or certify expertise.

## Consequences and next unit

The first persistence contract is independently reviewable, and prior packages remain stable. Service sessions, Pydantic/FastAPI permissions/errors/pagination, SQLAlchemy/Alembic migrations, competing-transaction/retry/recovery, workers/outbox, indexes/EXPLAIN and deployment/backup evidence remain open. Step 6 remains in progress; full academy Compose/PostgreSQL operations remain later work.

## Primary references

- [Psycopg parameters and transaction control](https://www.psycopg.org/docs/usage.html)
- [Psycopg connection contexts](https://www.psycopg.org/docs/connection.html)
- [PostgreSQL 17 constraints](https://www.postgresql.org/docs/17/ddl-constraints.html)
- [PostgreSQL 17 INSERT/ON CONFLICT](https://www.postgresql.org/docs/17/sql-insert.html)
- [PostgreSQL 17 READ COMMITTED](https://www.postgresql.org/docs/17/transaction-iso.html#XACT-READ-COMMITTED)
- [PostgreSQL 17 LIMIT and ordering](https://www.postgresql.org/docs/17/queries-limit.html)
