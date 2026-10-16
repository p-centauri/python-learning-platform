## The idea in plain language

Repeated delivery is normal in ingestion. State what the same delivery means: the lab uses namespace, id and revision. Same key and same value is a duplicate, so it makes no new row. Same key and a different value is a conflicting fact, so the whole batch must fail. A new revision is a distinct row.

PostgreSQL's unique key arbiters are stronger than application SELECT-before-INSERT. Two callers can both see no row before either inserts. Instead attempt INSERT ... ON CONFLICT (namespace,id,revision) DO NOTHING RETURNING value. RETURNING yields a row for an insertion; an ignored conflict yields no inserted row. It does not prove the existing value equals the attempted value.

After an ignored conflict, select the full key FOR SHARE and compare the stored value. In this append-only READ COMMITTED protocol an identical value counts as a duplicate; a different/missing value raises ConflictingReading. Never use blind DO UPDATE to overwrite a stored fact merely to silence a duplicate. FOR SHARE prevents selected rows being updated/deleted until transaction end, but external mutations between statements are excluded by this bounded protocol.

Count every observed input, including repeats within the same batch: observed equals inserted plus duplicates on success. If a later reading conflicts, rollback includes any earlier inserts in that batch and no BatchResult is returned. Previously committed rows remain unchanged.

Unique keys plus reconciliation do not automatically solve authorization, current revision selection, durable worker acknowledgment or distributed exactly-once delivery. This unit does not claim multi-writer stress verification. A later concurrency/worker unit must test competing transactions, lock waits, deadlocks and retry/recovery. The local set example explains identity collapse only; it is not a replacement for the database arbiter.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
keys = [("feed", "a", 1), ("feed", "a", 1), ("feed", "a", 2)]
observed = len(keys)
unique = len(set(keys))
print(observed, unique, observed - unique)
```

## Apply it in the PostgreSQL lab

These literal trusted example values illustrate SQL. In Python use separate bound parameters for all caller values. An ignored key conflict does not prove value equality; a changed value must raise and roll back the entire batch.

```sql
INSERT INTO feed_record(namespace, id, revision, value)
VALUES ('feed', 'a', 1, 5)
ON CONFLICT (namespace, id, revision) DO NOTHING
RETURNING value;

-- If no row was returned, compare the existing full key in the same transaction:
SELECT value FROM feed_record
WHERE namespace = 'feed' AND id = 'a' AND revision = 1
FOR SHARE;
```

## Guided practice

Explain why DO NOTHING is insufficient to classify a changed value as safe. Trace within-batch and cross-batch repeats.

## Independent practice

Implement RETURNING-based insertion counts and full-key stored-value comparison. Test zero values, revision/source distinction and late rollback.

## Check your work

Duplicates preserve the stored fact; conflicts do not overwrite. No result is returned before commit.

Continue to [Bounded reads & deterministic results](/lessons/python-database-read-bounds).
