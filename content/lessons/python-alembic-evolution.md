## The idea in plain language

ORM metadata describes the schema expected by current code. A migration records a transition between schema versions. create_all can create missing tables but is not a history of safe changes to existing data. Do not run ad-hoc schema creation in every API request.

The lab packages two revisions. service_001 creates the source/reading keys and constraints. service_002 adds required timezone-aware ingested_at with a server default. Existing key/value rows survive the upgrade and receive metadata. The application readiness endpoint expects the head revision; liveness alone says only that the process can answer.

A downgrade is not a backup. Reverting service_002 drops ingestion-time metadata while retaining original keys/values; re-upgrade creates new timestamps. Reverting to base destroys the lab tables. Tests rehearse that only in uniquely owned disposable schemas. Never infer that a production downgrade preserves all data or allows old/new services to run together safely.

Alembic autogeneration compares metadata with a database and proposes changes; review the proposal. Names, defaults, data conversions, locks and compatibility need judgment. The lab check_migrations compares its actual migrated PostgreSQL schema to ORM metadata and reports drift separately. A version row at head does not by itself prove every column is correct.

The app does not migrate at request/startup time. A separate caller-owned connection/engine scope applies changes before serving writes. The local server then checks /ready. Later release units need deploy ordering, backups, concurrent readers/writers, lock budgets and rollback/recovery evidence; these two tiny migrations do not establish zero-downtime operations.

The local Python example shows version order only. Actual upgrade/downgrade/re-upgrade tests preserve baseline facts and verify timestamp loss, constraints, readiness and metadata checks on PostgreSQL.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
revisions = ["service_001", "service_002"]
print(revisions[-1])
print("downgrade is not a backup")
```

## Guided practice

Compare current ORM metadata with migration history, readiness and backups. Explain exactly what the second downgrade loses.

## Independent practice

Apply revision 1, save a fact, upgrade/head-check, downgrade and re-upgrade. Record values/timestamps and read readiness at each stage.

## Check your work

Migration rehearsals use disposable schemas. Head readiness and metadata drift are separate checks.

Continue to [Scoped keyset pages & changing data](/lessons/python-api-pagination).
