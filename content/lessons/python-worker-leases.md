## The idea in plain language

A lease is a reservation that expires. The previous publisher held a database row lock while sending an event. The new worker instead saves a reservation, commits it, releases its database connection, then calls publication. Slow publication no longer holds the claim transaction open.

The saved job has the event's complete key, a generation number, a state and a deadline. The first claim changes ready to leased and increases generation from zero to one. The returned Lease contains a copied Event and the deadline. Another worker cannot claim that job before its lease and retry delay allow it.

Expiry does not stop the original Python process. That worker might still be running while a replacement starts. A lease creates a recovery opportunity, not proof that only one callback exists. The next lesson protects settlement against the older worker.

Use the database clock for shared deadlines. A laptop's clock may differ from the server. PostgreSQL clock_timestamp changes as time passes; a transaction-start timestamp can stay old while a lock wait happens. This lab checks the current database time at the settlement write. Server wall-clock changes remain an operational limitation.

A claim adopts at most 64 missing pending jobs, closes at most 64 expired final attempts, and returns at most one lease. SKIP LOCKED skips rows held by other workers. No returned lease means none was available in that statement; pending or future work may remain. This is a count limit, with no promise of fairness or a total time limit.

Keep the older row-lock publisher separate from this lease publisher for the same jobs. Concurrently mixing both paths is outside this lab's contract.

## Worked example

This small local illustration explains one idea. It does not evaluate the database or process boundary; use the lab for that evidence.

```python
from datetime import datetime, timedelta, timezone
now = datetime.now(timezone.utc)
expiry = now + timedelta(seconds=1)
print(expiry > now)
```

## Guided practice

Commit one job generation and its deadline. Publish after the claim transaction finishes. Expiry does not prove the old worker stopped.

## Independent practice

Implement or inspect the matching lab contract. Save an actual before/after observation, name the owner and time boundary, and explain one failure.

## Check your work

A deadline cannot terminate the publisher. SKIP LOCKED can hide pending jobs from this statement. Label controlled timestamp fixtures and actual process observations separately.

Continue to [Reject settlement from an older worker](/lessons/python-worker-fencing).
