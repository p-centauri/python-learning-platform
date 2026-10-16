# ADR 0026: observed PostgreSQL competition and bounded complete retries

Date: 2026-10-04
Status: Accepted

## Context

The prior local ingestion service proves serial HTTP/storage/session/migration boundaries. Step 6 also needs observed competing transactions, isolation and recovery decisions. Sleep-based scheduling cannot establish database waits; generic retries can duplicate uncertain effects or reuse an aborted transaction. A missing receipt and a missing row are different observations.

## Decision

Publish seven ordered lessons from python-pg-snapshots through python-competition-evidence, fourteen original scenarios under separate PostgreSQL competition contracts and full guided/diagram/glossary/recall layers. Catalog is 2026.10-competition-v1; interactive/recall/project-review are v12. Preserve previous denominators, exam definitions and submitted snapshots. Local runnable examples explain concepts; actual PostgreSQL experiments establish database behavior.

Provide academy-competing-ingestion-lab 0.1.0, Python 3.13+, as a thirteen-file authenticated local extension of the completed academy-ingestion-service-lab 0.1.0 wheel. These local distributions are not published on PyPI; learners finish/build/install the earlier wheel first. Keep maintained retry/reconciliation implementations outside downloads. No new academy runtime dependency, schema, API endpoint or runner contract is introduced. The academy serves authored bytes and stores reported/manual evidence, never importing/executing learner packages.

Three unfinished functions define explicit contracts:

- classify_sqlstate accepts an exact five-character uppercase ASCII SQLSTATE or None. Only 40001/40P01 permit a complete transaction restart. None, class 08 and 57P01/57P02 require reconciliation; all other valid codes stop. Malformed values raise ValueError. Messages do not choose policy. This conservative policy is local to the lab, not a universal rule.
- retry_ingest validates one namespace and at most 64 exact revalidated prior Datums in an exact list/tuple, copies fields into new frozen values once and preserves order/repeats. Contradictory full keys fail before SQL. The explicit PostgreSQL/Psycopg Engine is borrowed. Every attempt owns a fresh Session, uses the unchanged prior ingest transaction/commit contract and returns only a successfully committed Receipt plus actual attempts. Only DBAPIError is classified after Session rollback/closure; permitted delays run after cleanup. UnknownOutcome/RetryExhausted have fixed messages and native causes; stop/domain/programming/pool/sleeper failures remain original. No remote input acquisition or side effects are replayed.
- reconcile validates/copies the same bounded facts and owns one new read transaction. Bind only requested complete keys under the namespace; count matching unique keys and report expected missing/conflicting Datums in first-key order. Conflict has priority, then missing, otherwise complete. Empty input is complete without SQL. It never provisions/mutates data or grants access.

A supplied Session after_begin event uses its Connection, checks READ COMMITTED and binds transaction-local lock_timeout/statement_timeout. This preserves the earlier service's idle-Session requirement and resets settings at transaction exit. Policy has exact attempts 1..3, lock wait 50..2000 ms, a larger statement limit at most 5000 ms and one exact finite float delay 0..1 seconds per possible retry. Reproducible default delays are zero; explicit caller-selected jitter is possible without a fairness claim. Item/attempt/statement/lock bounds do not impose a hard whole-job deadline or pool/input/remote-effect budget.

Complete reconciliation observes all requested key/value facts; it does not identify a particular transaction or reconstruct lost inserted/duplicate counts. Missing is absence in one statement view, not rollback proof: a pending writer can commit after it. No observation automatically grants replay permission. Namespace arguments require the surrounding application's prior authorization; the extension adds no HTTP endpoint/auth flow and leaves existing 401/403/output fields unchanged.

Supplied disposable experiments use separate owned Sessions/connections, Events/Barrier, bounded polling of actual pg_blocking_pids and joined threads. Four pending-insert cases show exact duplicate/conflict after holder commit and challenger insertion after holder rollback. READ COMMITTED/REPEATABLE READ experiments record statement/transaction views and fresh visibility without changing the engine default. A separate SERIALIZABLE admission fixture observes actual 40001, then reads the rule afresh and skips; it does not impose that fixture rule or isolation on the original service.

Inverse-key writers generate actual 40P01 with an unspecified victim. The victim restarts fully; observations show attempts 1/2, one committed insertion receipt and one duplicate receipt, preserving both facts. Consistent complete-key acquisition can prevent this particular cycle only when all cooperating writers follow it. The fixture-specific first-insert barrier must not be reused for differently blocked writers. The existing server deadlock_timeout must be below the configured 2000 ms lock wait; the experiment checks it and never changes privileged settings. Separate experiments observe real 55P03/57014 and cleanup/local reset. Native event observers are removed after their owned experiment.

The missing-acknowledgment test actually commits, then injects a modeled response/DBAPI failure. One attempt stops and scoped reconciliation observes complete. This is modeled communication loss around real data, not a real broken-network commit incident. Another actual transaction shows missing before an in-flight commit and complete afterward.

Trusted maintainer subprocesses build two real source archives/wheels from sdists and install freshly, check quiet import/resources/types, run 70 public cases outside source on an owned digest-pinned PostgreSQL 17 container and save/parse actual demo JSON. Offline evidence is 53 passes/17 explicit database skips, never fabricated integration. Existing API permissions/public output are verified after extension writes. The shared helper owns unique container/network, tmpfs database, ephemeral loopback port and private temporary credentials; only owned resources are removed. No learner upload or academy data is executed/read by this lab.

Four pinned manual criteria distinguish visibility/wait/isolation, retry/transaction ownership, reconciliation/scope and installed evidence/limits. Reading/checklists, finite checks, reported output and self/human review do not award mastery or expertise.

## Consequences and next unit

The first bounded concurrency/retry/reconciliation unit is reviewable on the real prior service. It does not establish production load/fairness, arbitrary deadlock freedom, durable receipts, exactly-once effects, crash recovery, full public authentication or academy PostgreSQL operations. Next build a bounded durable outbox/worker unit with atomic event recording, stable identity and actual crash/replay evidence. Broader queries/indexes/API depth, worker leases/backoff/shutdown, deployment and applied AI remain open. Step 6 remains in progress.

## Primary references

- [PostgreSQL 17 isolation](https://www.postgresql.org/docs/17/transaction-iso.html)
- [PostgreSQL 17 locks and deadlocks](https://www.postgresql.org/docs/17/explicit-locking.html)
- [PostgreSQL serialization failure handling](https://www.postgresql.org/docs/17/mvcc-serialization-failure-handling.html)
- [PostgreSQL client timeout settings](https://www.postgresql.org/docs/17/runtime-config-client.html)
- [PostgreSQL pg_blocking_pids](https://www.postgresql.org/docs/17/functions-info.html)
- [SQLAlchemy after_begin Connection scope](https://docs.sqlalchemy.org/en/20/orm/events.html#sqlalchemy.orm.SessionEvents.after_begin)
