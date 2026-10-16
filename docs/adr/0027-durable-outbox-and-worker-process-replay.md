# ADR 0027: atomic outbox and observed worker process replay

Date: 2026-10-04
Status: Accepted

## Context

The prior service and competition units establish database facts and bounded retry/reconciliation. A committed fact followed by a separate event insert can lose delivery intent when the worker stops. Independent consumer acceptance and producer acknowledgment permit repeated delivery. Step 6 needs actual worker exits, stable identity and a clearly scoped durable local effect.

## Decision

Publish six lessons from python-outbox-atomicity through python-outbox-evidence, twelve original scenarios under a separate Durable outbox contracts skill and complete guided/diagram/glossary/recall layers. Catalog is 2026.10-outbox-v1; interactive/recall/project-review are v13. Preserve earlier denominators, exams and frozen history.

Provide academy-durable-outbox-lab 0.1.0, Python 3.13+, as a fourteen-file authenticated local extension of completed service/competition wheels. Those local distributions are not on PyPI. Three functions remain unfinished; maintained core stays outside downloads. No new academy runtime dependency, schema migration, endpoint/auth flow or isolated runner contract is added. The academy serves bytes and stores manual evidence only.

Event identity is the complete namespace/id/revision tuple; payload changes under that key conflict. Strict Datum rules preserve zero and revision values. Validate/copy bounded facts before SQL. Every call owns a fresh READ COMMITTED Session using the prior local-limit helper; Engines/callbacks remain borrowed. Return only after the owned transaction commits. No in-call automatic publication retry is allowed; callback/constraint/domain/programming errors propagate after cleanup.

record commits source/reading/intents in one transaction rather than calling the earlier independently committing ingest. Matching prior facts can acquire their missing intent once when explicitly requested. Counts preserve observed/repeated readings and new unique intents. Late failure rolls back all new facts/intents; prior committed state remains. Existing acknowledged intent is never reset by repeated input. Empty valid input returns zero without connecting. Existing HTTP POST remains unchanged and does not enqueue automatically.

Explicit one-time packaged schema.sql adds delivery_outbox/inbox/effect after service_002 in a disposable schema. Repeated install errors instead of hiding drift. The earlier Alembic drift check covers its own metadata and will flag extra extension tables. Production migration/version/drift/retention integration is later work; no live migration/rollback claim.

publish_one claims one scoped pending row using FOR UPDATE SKIP LOCKED, ordered id/revision, and holds the transaction row lock through one trusted publisher call. The callback must return exact Accepted for the unmodified persisted Event after its durable boundary. Keep a separate expected copy against callback identity mutation. Acknowledgment updates/commits afterward. None means no row available in that statement, not global emptiness. Later rows can be delivered first; no fairness/global order claim. Failure/exit rolls back producer acknowledgment but cannot undo a separately committed effect. Publisher confirmation is a trusted protocol promise, not a cryptographic/independent remote receipt.

consume inserts complete inbox identity/value and increments one namespace aggregate only for a new key, in one transaction. Same-value repeats confirm without applying again; changed repeats conflict. A real CHECK failure proves inbox/effect rollback. This protects the local database effect only, not email/payments/arbitrary callbacks or exactly-once transport. Namespace arguments require prior application authorization; identity/claims do not grant access.

Separate worker pools provide producer and independent consumer connections. Sessions never cross threads. Local 2000ms lock/5000ms statement limits do not interrupt a blocked publisher or impose a hard total deadline. Holding a transaction while publishing is a first teaching design; leases/fencing and graceful bounded worker lifecycle remain later work.

Trusted child processes really use os._exit before producer commit (71), after producer commit (72) and after consumer commit before producer acknowledgment (73). The parent observes tagged pg_stat_activity disappearance before reading/restarting. Before commit neither fact nor intent survives; after producer commit pending work survives; after consumer commit one effect and pending intent survive. Restart reuses identity and leaves exactly one demonstrated local application. PostgreSQL stays running; tmpfs disposable storage is not database power-loss/restart/backup evidence. A separate modeled callback response loss after actual commit is labeled distinctly.

Three real source archives/wheels build from sdists and install freshly outside source without path fallback. Quiet import, schema/typing resources, strict installed demo/crash worker, pip check, 67 cases on owned digest-pinned PostgreSQL 17 and actual JSON/readback verify maintained code. Offline evidence is 45 pass/22 explicit database skips. The shared helper removes only its unique temporary container/network; spawned authored children are owned/reaped. Existing API 401/403/output fields remain verified. No learner upload executes in the academy API.

Four manual criteria separate atomic identity/adoption, claim/confirmation, consumer replay and installed evidence/limits. Reading/checklists/reported output/self-human review do not grant mastery or expertise.

## Consequences and next unit

This first bounded durable outbox/worker unit is reviewable with actual process exits/replay and duplicate-safe local effects. It does not establish a real broker, production load/fairness, leases/fencing, arbitrary external idempotency, power-loss/backup recovery, public authentication or academy PostgreSQL operations. Next teach bounded leases/fencing, admission/backoff, poison-message policy and graceful shutdown with stale-owner rejection and actual recovery. Then broker/schema integration, operational migrations/retention, deployment, broader SQL/API and applied AI remain open. Step 6 is not complete.

## Primary references

- [PostgreSQL 17 row locking and SKIP LOCKED](https://www.postgresql.org/docs/17/sql-select.html)
- [PostgreSQL 17 INSERT and ON CONFLICT](https://www.postgresql.org/docs/17/sql-insert.html)
- [SQLAlchemy 2 Session transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
