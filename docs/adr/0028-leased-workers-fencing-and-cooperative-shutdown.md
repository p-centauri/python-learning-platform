# ADR 0028: Leased workers, fenced settlement and cooperative shutdown

Date: 2026-10-04. Status: accepted for this bounded local teaching unit.

## Context

ADR 0027 holds a row lock through trusted publication and demonstrates atomic intent/inbox commits and real worker replay. The next authorized step-6 unit needs to release the claim transaction before publication, reject stale owners, retain schedules/attempt limits across restarts, inspect failed jobs and observe graceful admission stop. A lease cannot terminate a stale publisher or make external effects duplicate-safe.

## Decision

Publish six ordered lessons with a separate Worker lease contracts skill, original scenarios and full guided/diagram/glossary/private recall coverage. Provide a fixed authenticated fourteen-file installable extension with three unfinished functions and four manual criteria. No React/runtime/auth/migration/runner change. Preserve previous packages, stable Event/Accepted, HTTP permission contracts and frozen learner evidence.

Persist immutable per-namespace Policy and per-complete-key delivery_job in explicit one-time teaching SQL. Claim uses a short READ COMMITTED transaction, bounded adoption/final-expiry batches (64 each), SKIP LOCKED and a generation increased for every committed attempt. Commit/release before callback publication. Use server clock_timestamp for deadlines and write-time guards. Expired claims use deadline plus saved attempt delay; explicit retries use settlement time plus that delay. The attempt cap survives process death. Final expiry/retry and explicit poison quarantine without acknowledgment or implicit redrive.

Settlement guards the current generation, state, full key/value, exact deadline and current DB time, then commits job completion and outbox acknowledgment together. Stale returns False without mutation. Accepted is a trusted durable-destination protocol promise; the reference uses the earlier inbox/aggregate sink. Tokens protect this guarded database write only. Do not run legacy row-lock and lease publishers concurrently on the same jobs.

Sequential run bounds admissions (1..64), checks a borrowed threading.Event before each new claim and finishes admitted work cooperatively. Ordinary callback/validation errors attempt finite retry settlement then re-raise the original failure; failure of that settlement relies on expiry. BaseException/abrupt death leave the lease. A signal handler exists only in the authored child main and restores the prior handler; imports never alter signal handling.

## Evidence

59 public cases: 35 offline and 24 actual PostgreSQL-dependent cases. Fresh-installed four-package verification passes all on PostgreSQL 17.11, pip consistency, source/archive/wheel construction, quiet import, packaged SQL/typing, installed strict types, actual JSON/readback and unchanged service 401/403/200 output. Real checks cover saved times/attempts, stale owner/deadline/payload rejection, separate claims, bounded adoption, poison/exhaustion and actual CHECK-triggered shared rollback/pool release.

Two real os._exit subprocess boundaries commit a claim and optionally acceptance before dying. The parent observes tagged connections vanish and actual database lease expiry, then generation-2 reclaim preserves one application. A separate actual SIGTERM check begins only after observed callback admission, completes/settles the cooperative callback and leaves a second intent pending. Some scheduling cases intentionally edit owned fixture timestamps; modeled response loss after real consumer commit remains labeled separately. Offline skips are not recovery evidence.

## Consequences and limits

Short leases release pool connections during publication, with possible overlapping old/replacement publishers. Fencing and the local inbox protect their stated database writes, not arbitrary external effects. No renewal, jitter, global capacity/fairness, total callback deadline, hard shutdown, public authorization, malicious-caller isolation, database power loss/backup or full operations claim. Persisted reasons are finite labels, with no private exception text. DDL is additive disposable teaching setup, not production migration/drift/retention/redrive integration. Checks/reported output/manual reviews do not award mastery.

Step 6 remains open. Next connect a bounded owned Redis Streams broker with versioned delivery envelopes, explicit acceptance/redelivery and local deduplication. Then operational migrations/retention/redrive, release/deployment, broader SQL/API and applied AI remain.

Primary reading: [PostgreSQL current-time semantics](https://www.postgresql.org/docs/17/functions-datetime.html#FUNCTIONS-DATETIME-CURRENT), [PostgreSQL SELECT/row locking](https://www.postgresql.org/docs/17/sql-select.html), [Python signal handling](https://docs.python.org/3.13/library/signal.html), [threading.Event](https://docs.python.org/3.13/library/threading.html#event-objects).
