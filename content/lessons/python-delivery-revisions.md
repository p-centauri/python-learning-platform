## The idea in plain language

A migration is a recorded change to the database. The revision tells the next tool which changes have already committed. Keeping a file named schema.sql is useful for a fresh experiment, but it does not record an upgrade path for an existing service.

This lab keeps service_001 and service_002 unchanged. delivery_003 adds outbox, inbox and effect tables. delivery_004 adds policy, jobs and the ready-job index. One chain has one expected head: delivery_004. The same installed package supports an empty disposable schema and an existing service_002 schema.

Call upgrade explicitly outside requests and imports. It owns a PostgreSQL transaction and updates the revision with the DDL. A repeated upgrade at head has nothing to apply. That does not compare every table with the expected design or repair drift.

Do not stamp an existing one-time setup as migrated. Stamping writes a revision without executing the changes. This exercise rejects an existing delivery_outbox collision instead of guessing whether its columns, rows and constraints match. Rehearse from a fresh schema or a known service_002 history.

The fixed wrapper accepts only documented target strings. It cannot downgrade to base or service_001, which would destroy service tables or timestamp metadata. Caller configuration selects the owned disposable schema; a namespace argument is not permission to migrate a shared database.

## Worked example

This local illustration explains the idea. It does not run a database migration; actual store evidence comes from the lab.

```python
chain = ("service_001", "service_002", "delivery_003", "delivery_004")
print(chain[-1])
```

## Guided practice

A service_002 database already contains two facts. How should delivery tables be added? Explain why the documented boundary matters, then check the matching lab case.

## Independent practice

One-time SQL already created delivery_outbox, but the revision is service_002. What should this lab do? Write your decision before checking the answer. Reproduce the relevant boundary in the disposable lab and save the observed revision, fields and error or result.

## Check your work

Apply the recorded additive revisions, preserving the existing service facts. A revision stamp cannot prove an existing unversioned schema matches the migration history. Keep head, drift, data validity and application compatibility separate. Label skipped store work as unevaluated; reported output and manual judgment do not award mastery.

Open the [Delivery migration lab](/projects#python-delivery-schema), download the starter after signing in, then [submit evidence for review](/projects/python-delivery-schema).

Next: [Preserve existing facts without inventing deliveries](/lessons/python-migration-data).
