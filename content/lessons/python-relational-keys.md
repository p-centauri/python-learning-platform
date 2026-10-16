## The idea in plain language

A relational database stores rows in tables. A row represents one fact with named columns. Start by asking what makes that fact distinct and what relationship it has to another fact. Avoid storing unrelated facts in one changing text blob just because JSON is convenient.

For ingestion, one source has many readings. feed_source has a namespace key. feed_record stores namespace, id, revision and value. Its primary key is the combination (namespace, id, revision). The value belongs to that identity. A different revision or namespace represents a different reading even when the id is the same.

A primary key identifies one row and disallows missing key parts. A foreign key requires a matching parent: a reading cannot name a source that does not exist. The application can insert a source first in the same transaction. An automatically assigned row number can identify storage, but it does not by itself identify the same upstream event on a repeated delivery.

The worked Python tuple shows the identity choice only. It does not prove database enforcement. The downloadable lab uses PostgreSQL constraints and verifies them through direct SQL and a separate observing connection. Namespaces separate application keys; they do not check whether a user has permission to read those rows. Authorization belongs to the later service boundary.

Write down which fields may change. This lab uses an append-only key/value protocol: the same key must retain the same value; a changed observation needs an explicit new revision. This is a stated application rule, not a universal rule for every database. External updates/deletes and automatic latest-version selection are outside this bounded exercise.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
keys = [("feed", "a", 1), ("feed", "a", 2), ("other", "a", 1)]
print(len(set(keys)))
print(keys[0] == ("feed", "a", 1))
```

## Apply it in the PostgreSQL lab

This small DDL sketch shows relationships only. Use the packaged schema.sql for the complete named range/identity checks, in a newly owned disposable schema.

```sql
-- The packaged schema includes these relationships:
CREATE TABLE feed_source (namespace text PRIMARY KEY);
CREATE TABLE feed_record (
    namespace text NOT NULL REFERENCES feed_source(namespace),
    id text NOT NULL,
    revision integer NOT NULL,
    value integer NOT NULL,
    PRIMARY KEY (namespace, id, revision)
);
```

## Guided practice

Identify the parent, child and complete key. Explain why upstream identity differs from an automatically assigned database row number.

## Independent practice

Draw the two tables and map an earlier ingestion Record into a Reading with caller-chosen namespace/revision. Preserve the earlier package API.

## Check your work

Test key differences for namespace and revision. A namespace is not authorization.

Continue to [Database constraints protect every writer](/lessons/python-database-constraints).
