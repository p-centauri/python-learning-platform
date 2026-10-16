## The idea in plain language

A read has a resource and transaction contract too. In non-autocommit Psycopg, a SELECT can start a transaction. The lab load_namespace owns that read transaction and cursor, then leaves a healthy borrowed connection idle/open. A read does not install a missing source or mutate rows.

SQL rows have no promised application order without ORDER BY. The lab chooses id COLLATE "C", then revision, with a fixed schema and validated ASCII ids. This gives reproducible result order for the bounded contract. An index may help this query, but query plans and production costs need representative data and measurement; a toy result cannot prove performance.

To return at most 64 rows and detect overflow, select LIMIT 65. Exactly 64 can succeed. The 65th observed row establishes too many and raises ValueError, returning no partial tuple. LIMIT 64 alone cannot distinguish exactly 64 from a larger matching set.

Batch size and stored namespace size are different. Repeated valid batches can accumulate more than 64 stored rows; load_namespace then reports overflow. LIMIT bounds returned observations, not all scanning/planning work, database storage, network buffering or elapsed query time. Counts are not a total operation deadline.

Pagination needs a separate contract: stable ordering keys, a continuation cursor, changing data rules and authorization. This first lab chooses explicit overflow rather than a pretend complete result. The later service path will choose pagination and indexes with actual query evidence. A namespace filter and value parameters do not authorize a user to see that namespace.

The local example shows the extra observation needed for overflow. PostgreSQL tests prove ordering, absence, exact bounds, failed-read cleanup and idle reuse.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
rows = tuple(range(65))
observed = rows[:65]
print(len(observed) > 64)
print(len(rows[:64]) == 64)
```

## Apply it in the PostgreSQL lab

Bind the namespace in Python rather than interpolate it. Exactly 64 rows can succeed; observing 65 raises overflow and returns no tuple. This is a complete-or-error contract, not pagination or a database storage limit.

```sql
SELECT namespace, id, revision, value
FROM feed_record
WHERE namespace = 'feed'
ORDER BY id COLLATE "C", revision
LIMIT 65;
```

## Guided practice

Explain why ORDER BY and LIMIT 65 are separate requirements. Distinguish batch bounds from stored rows and query work.

## Independent practice

Implement the read with validated bound namespace, fixed ordering and overflow rollback. Accumulate 65 rows across batches and verify no partial result.

## Check your work

Deterministic finite output does not establish pagination, authorization or query performance.

Continue to [Persistence evidence & the reviewed ingestion lab](/lessons/python-persistence-contracts).
