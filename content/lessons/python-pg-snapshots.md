## The idea in plain language

A transaction is a unit of database work. Its snapshot is the committed data a statement can see. Two connections can look at the same table and see different rows because their statements started at different times. A writer can see its own uncommitted work; that does not show another reader can see it.

In PostgreSQL READ COMMITTED, an ordinary SELECT gets a new committed view for each statement. Two SELECTs in one transaction can therefore return different counts after another writer commits. REPEATABLE READ keeps the view established by the transaction's first ordinary statement. A new transaction can then see newer committed data. Calling begin alone does not establish that first data snapshot.

Neither mode reads another transaction's uncommitted rows. PostgreSQL's READ UNCOMMITTED behaves like READ COMMITTED. These are PostgreSQL rules, not universal claims about every database. An INSERT with ON CONFLICT may wait for an uncommitted competing key even though a normal SELECT cannot yet see that row. Visibility and uniqueness checks solve different problems.

The supplied lab uses separate connections to read, commit a new fact, read again and start a fresh transaction. READ COMMITTED observes counts 0, 1, 1; REPEATABLE READ observes 0, 0, 1 in that fixture. The installed run must produce those observations; the small Python example below merely compares two named views.

Changing isolation is not a repair for every business rule. A stable snapshot can still permit inconsistent multi-row decisions. Keep the existing ingestion service on its explicit READ COMMITTED contract; use dedicated experimental connections for stronger modes. These tests do not measure load or query plans.

## Worked example

This local Python illustration explains one idea. The PostgreSQL lab supplies the actual database observations.

```python
before, after_commit = 0, 1
print(before != after_commit)
```

## Guided practice

Explain statement snapshots, transaction snapshots and a fresh transaction using two connections.

## Independent practice

Run both snapshot experiments. Record the three real counts and explain why own uncommitted reads are insufficient.

## Check your work

Visibility, key arbitration and business invariants are separate; the engine default must remain READ COMMITTED.

Continue to [Observe lock waits and bound blocked statements](/lessons/python-pg-lock-waits).
