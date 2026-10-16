## The idea in plain language

A deadlock is a cycle of waiting. Transaction A holds one key and wants a key held by B; B holds that second key and wants A's first key. Neither can finish by waiting for the other. PostgreSQL detects the cycle and aborts one transaction with 40P01. The victim is not part of the application's contract.

The ingestion lab creates that cycle with two batches containing the same immutable facts in opposite order. A bounded barrier coordinates the first successful reading insert in each thread. Each writer then needs the other key. The real database chooses a victim; an error observer records the actual SQLSTATE. This is a two-writer fixture, not a stress benchmark.

The victim's whole transaction must roll back, including its first insert. The successful writer can commit both facts. A fresh victim attempt replays the original bounded values and then reports duplicates. The installed evidence expects one writer to need one attempt and the other two; final storage holds the two original facts. Failed attempt receipts never become successful counts.

Consistent acquisition order can prevent this particular inverse-key cycle. Order complete resource identities and require every cooperating writer to follow the same rule. Sorting only a display label, ignoring tenant/revision or relying on one client's order does not establish a global protocol. Other locks, DDL and foreign-key operations still need analysis.

The maintained earlier ingest implementation keeps input order; this extension does not silently change that contract. Its experiment deliberately exposes the cycle and its bounded recovery. The barrier designed for opposite-first-key writers must not be reused blindly for writers that block before reaching it. Draw the dependencies and use appropriate observations for each experiment.

Cleanup is part of the evidence. Owned threads are joined, Sessions close and event observers are removed. Cancellation of a Python future cannot undo a database transaction already running. Count bounds and server statement limits do not grant a hard total deadline.

## Worked example

This local Python illustration explains one idea. The PostgreSQL lab supplies the actual database observations.

```python
left, right = ["a", "b"], ["b", "a"]
print(sorted(left) == sorted(right))
```

## Guided practice

Draw the wait cycle, explain why victim choice is unspecified and identify a consistent full-key order.

## Independent practice

Run the real inverse-order experiment. Save observed 40P01, attempts, committed counts, final facts and cleanup.

## Check your work

Retry the full aborted transaction after cleanup; do not keep its successful prefix or assume which writer loses.

Continue to [Serializable decisions need fresh reads](/lessons/python-pg-serializable).
