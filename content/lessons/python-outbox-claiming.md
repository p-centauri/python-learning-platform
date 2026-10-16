## The idea in plain language

A worker first claims an event, then delivers it, then marks it acknowledged. Acknowledging before delivery risks losing work if the worker stops. Delivering before acknowledgment permits repeats if delivery succeeds but the worker stops before the acknowledgment commits.

The first worker in this lab selects one pending row with FOR UPDATE SKIP LOCKED. It keeps that row's transaction lock while calling a trusted publisher once. Another worker can skip the held row and claim a different one. Each worker owns its own Session and pool; sharing a Session across threads is outside the contract.

The publisher must return Accepted for the exact persisted Event after its durable acceptance. A return value is a trusted protocol promise, not independent proof of a remote system. None, a different payload or a different key cannot authorize acknowledgment. Only after confirmation does the worker update acknowledged and commit. It returns the delivered Event after that commit.

If the callback raises or the worker dies, its outbox transaction rolls back and the row stays pending. The callback may already have committed elsewhere. Rolling back the producer cannot undo that independent effect. This is why the consumer needs a duplicate-safe transaction.

None from publish_one means no row was available in that statement. It does not prove the queue is empty: other workers may hold every pending row. Skipping a locked earlier key also means this design does not promise global delivery order or fairness.

Holding a transaction during publication is deliberately small teaching architecture. Statement and lock limits do not interrupt a blocked publisher. Leases, fencing, backoff and graceful shutdown are later work.

## Worked example

This local Python illustration explains one idea. The lab supplies actual database/process observations.

```python
pending, available = 1, 0
print(pending > available)
```

## Guided practice

Skip currently held rows in the authorized namespace. Require exact durable acceptance for the claimed fact. Failure keeps the intent pending for later work.

## Independent practice

Implement or inspect the matching part of the lab. Run its public cases and save the actual before/after observations; explain one failure and one replay boundary.

## Check your work

SKIP LOCKED can hide held pending rows from this claim. Acknowledge only after the stated acceptance boundary. Label database skips, controlled models and limits honestly.

Continue to [Commit deduplication and the database effect together](/lessons/python-outbox-consumers).
