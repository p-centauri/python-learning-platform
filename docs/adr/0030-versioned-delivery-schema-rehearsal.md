# ADR 0030: Versioned delivery schema and explicit rollback rehearsal

Date: 2026-10-04
Status: Accepted

## Context

Earlier fixed service revisions stop at service_002. Outbox/leased-worker labs add tables through explicit one-time SQL without updating the version chain; the old drift checker sees extra tables. The next bounded learning unit needs a real installed upgrade path with existing facts and honest readiness/loss boundaries. The academy database and runner are separate.

## Decision

Publish six simple lessons and a separate academy-delivery-schema-lab 0.1.0 depending on the completed stream package. Preserve service_001/002 bytes, then add delivery_003 (outbox/inbox/effect) and delivery_004 (policy/job/index) through ordinary transactional DDL. Copy service MetaData into a separate combined model without mutating the old Base. Explicit migration commands run outside imports/requests, without stamp/create_all/automatic fact enqueue or unversioned setup adoption.

Own one non-autocommit READ COMMITTED connection/transaction, local lock/statement limits and a database-wide cooperating advisory lock. Busy clients fail immediately; errors propagate after rollback/release. Other tools, producers and consumers must be paused separately. Fixed upgrade targets and exact allow_loss=True permit only delivery downgrade targets service_002/delivery_003; base/service_001 are refused.

inspect_state reports exact head only. check requires that head and runs combined Alembic autogenerate with type/server-default comparison. This catches supported table/column/index/default/FK differences but does not prove CHECK expressions/data invariants. A live negative example demonstrates the blind spot. The unchanged old service /ready expects service_002 and returns 503 at the new head; a compatible application/readiness release must be selected before traffic resumes. Business permission/output contracts remain unchanged.

Rollback to delivery_003 deletes worker policy/jobs; rollback to service_002 also deletes intents/inbox/aggregate. All original key/value/timestamp fields remain, but delivery history is lost. Re-upgrade has empty history and permits a retained event key to apply again. Consent is not recovery safety, deduplication permanence or a backup policy.

## Evidence and assessment

The installed verifier builds six real source archives/wheels, installs freshly outside source, verifies resources/types/quiet imports and runs 44 cases (25 offline/19 live) on owned PostgreSQL/Redis. Actual late upgrade/downgrade failure, advisory/DDL contention, local settings/pool reset, unknown/legacy revision rejection, timestamped data preservation, drift limits, broker composition and explicit history loss are observed. The demo saves actual JSON and prior API 401/403/200 plus old readiness 503. Owned schemas/stream keys/store resources are removed. No learner code runs in the academy API.

Four manual criteria separate versioned preservation, head/drift/compatibility, transactional failure/loss and installed observations. Reading, checklists, reported tests and manual review do not award mastery. Earlier scenario denominators, exams and frozen evidence remain unchanged.

## Limits and next action

Finite transactional migration rehearsal is not zero-downtime rollout, a total elapsed deadline, power-loss/backup recovery, hostile code isolation or full academy PostgreSQL Compose verification. Legacy unversioned delivery setup is rejected, not adopted. PostgreSQL remains running; Redis keys are not migrated or trimmed. Step 6 remains open; bounded retention/explicit redrive is next, then release/deployment, broader SQL/API and applied AI.

## Primary references

- [Alembic connection sharing](https://alembic.sqlalchemy.org/en/latest/cookbook.html#sharing-a-connection-with-a-series-of-migration-commands-and-environments)
- [Alembic autogenerate scope and limits](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [PostgreSQL table changes](https://www.postgresql.org/docs/17/sql-altertable.html)
- [PostgreSQL explicit locking](https://www.postgresql.org/docs/17/explicit-locking.html)
