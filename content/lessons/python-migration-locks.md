## The idea in plain language

A migration can fail after earlier statements have succeeded. PostgreSQL lets the lab keep its ordinary table DDL and revision updates in one transaction. If delivery_004 fails, the preceding delivery_003 work in that same call rolls back too. The database must not report a later head for partially applied tables.

The supplied connection owner requires non-autocommit READ COMMITTED, sets transaction-local lock_timeout to 250 milliseconds and statement_timeout to 5000 milliseconds, and takes a cooperating advisory lock. The caller keeps ownership of the Engine; every successful or failed call releases its connection and local settings.

A second cooperating migrator gets BusyMigration immediately when the advisory lock is held. This prevents those two clients from interleaving a schema change. It does not stop an administrator using another tool or the application writing rows. Pause those processes explicitly.

DDL also needs table locks. The live suite keeps an ACCESS SHARE lock on delivery_job through another transaction, then attempts a destructive downgrade. The actual DROP waits and receives SQLSTATE 55P03 under the lock timeout. After that failure, the head and tables remain intact. A later explicit retry works after the holder releases its transaction.

These are per-statement limits, not a total migration deadline or zero-downtime promise. Some PostgreSQL operations need different transaction handling; this lab uses ordinary transactional table/index operations. Save the real error code, resulting revision and released pool count instead of assuming that every failure left the database unchanged.

## Worked example

This local illustration explains the idea. It does not run a database migration; actual store evidence comes from the lab.

```python
lock_wait_ms, statement_ms = 250, 5000
print(lock_wait_ms < statement_ms)
```

## Guided practice

delivery_003 ran, then delivery_004 failed in the same owned transaction. What should remain? Explain why the documented boundary matters, then check the matching lab case.

## Independent practice

A cooperating migration lock is held. Does it automatically stop application writers? Write your decision before checking the answer. Reproduce the relevant boundary in the disposable lab and save the observed revision, fields and error or result.

## Check your work

Transactional rollback includes earlier DDL and revision updates in the call. Advisory locks coordinate callers that explicitly follow the protocol. Keep head, drift, data validity and application compatibility separate. Label skipped store work as unevaluated; reported output and manual judgment do not award mastery.

Open the [Delivery migration lab](/projects#python-delivery-schema), download the starter after signing in, then [submit evidence for review](/projects/python-delivery-schema).

Next: [Name the history that a rollback deletes](/lessons/python-delivery-rollback).
