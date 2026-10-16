## The idea in plain language

Python validation gives callers an early useful error. PostgreSQL constraints protect stored facts when another script or application writes directly. Keep both layers: a frozen Python object does not protect rows written by SQL.

NOT NULL rejects missing values. CHECK rejects a row when its expression is false. A CHECK expression that evaluates to unknown because of NULL does not reject that row; combine CHECK with NOT NULL when a value is required. PRIMARY KEY combines uniqueness and non-null key parts. FOREIGN KEY ensures a referenced parent exists.

The lab supplies schema.sql with named checks: ASCII namespace/id, revision 1..8 and value 0..1000000. Zero is valid. The runtime accepts exact Python integers and rejects booleans/floats; database integer columns have their own adaptation and storage rules. Do not claim the database enforces every Python object-type distinction.

A UNIQUE or primary-key conflict reports SQLSTATE 23505, a foreign-key violation 23503, a CHECK violation 23514 and a NOT NULL violation 23502. Tests should inspect the driver's exception type/code rather than depend on a machine-specific English error message. Driver exceptions can include sensitive data: preserve useful type/cause in code, but do not publish raw connection strings or production row dumps.

Try each invalid direct SQL write in its own owned transaction. A failure aborts that transaction until rollback. The lab fixture owns schema installation separately from each batch. schema.sql is an initial teaching baseline; production schema evolution needs explicit migration history and rollback/compatibility planning later.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
values: list[int | None] = [0, None, -1]
for value in values:
    required = value is not None
    in_range = value is not None and 0 <= value <= 1000000
    print(required, in_range)
```

## Apply it in the PostgreSQL lab

In psql these errors remain visible, then ROLLBACK ends each aborted transaction. In Psycopg let the error escape the owned context and catch it outside, as the lab tests do.

```sql
-- Run each deliberate failure in its own transaction after fixture setup.
BEGIN;
INSERT INTO feed_record(namespace, id, revision, value)
VALUES ('missing-source', 'a', 1, 5); -- foreign key rejects missing parent
ROLLBACK;

BEGIN;
INSERT INTO feed_source(namespace) VALUES ('probe');
INSERT INTO feed_record(namespace, id, revision, value)
VALUES ('probe', 'a', 1, NULL); -- NOT NULL rejects missing value
ROLLBACK;
```

## Guided practice

Explain CHECK versus NOT NULL. Compare early Python validation with a direct SQL writer bypassing the constructor.

## Independent practice

Run direct CHECK, NOT NULL, foreign-key and duplicate violations in the disposable lab database. Record actual SQLSTATE and retained earlier rows.

## Check your work

Use real PostgreSQL failures; a Python condition or SQLite run does not establish the PostgreSQL constraint contract.

Continue to [SQL parameters keep values separate](/lessons/python-sql-parameters).
