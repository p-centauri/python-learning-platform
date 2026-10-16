## The idea in plain language

A retry is a new attempt, not permission to repeat everything that failed. Classify a documented database error code, not an exception's words. The lab permits complete transaction retries for 40001 and 40P01 only. It stops on lock/statement cancellation, constraints, domain conflicts, ordinary programming errors and pool exhaustion. A different application may choose a reviewed policy; this one is deliberately small.

A missing SQLSTATE, a connection-class 08 error or server shutdown 57P01/57P02 is classified conservatively as requiring reconciliation. A broken response around commit can leave the caller unsure whether data was stored. UnknownOutcome stops immediately; no automatic replay or delay follows. Read the state separately before choosing a later action.

retry_ingest validates and copies at most 64 exact immutable Datum values once before database work. A caller clearing its list or bypassing a frozen input object's field later cannot change the copied retry values. Conflicting values for one key within the supplied batch fail before SQL. Input is an exact list/tuple; arbitrary iterators/remote acquisition are not replayed.

Each attempt owns a fresh Session on the borrowed PostgreSQL Engine. The existing ingest service owns its explicit transaction and commits before returning counts. On a permitted failure, rollback and Session closure finish before the borrowed sleeper runs. Return Delivery containing only the successfully committed receipt and actual attempt count. Do not add failed-prefix counts.

The frozen policy allows one to three attempts, bounded transaction-local lock/statement limits and one finite 0..1-second float delay per possible retry. Caller-chosen jitter can reduce synchronized retries; the lab supplies an explicit deterministic schedule for reproducible cases, not fairness or throughput guarantees. Exhaustion raises a fixed RetryExhausted with attempts/code and native cause. Other failures keep their original identity; sleeper failures stop after cleanup.

The wrapper does not modify existing HTTP routes, perform authentication, execute remote side effects or create a durable job. Call it only after your application's permission boundary. Attempt/statement bounds do not establish a hard whole-operation deadline.

## Worked example

This local Python illustration explains one idea. The PostgreSQL lab supplies the actual database observations.

```python
permitted = {"40001", "40P01"}
print("55P03" in permitted)
```

## Guided practice

Trace classification, full transaction rollback, Session closure, bounded delay and the next new Session.

## Independent practice

Implement classify_sqlstate and retry_ingest. Run offline failure traces and actual deadlock/pool/timeout cleanup evidence.

## Check your work

Unknown outcome is never replayed automatically; count only a committed final receipt.

Continue to [Reconcile uncertain outcomes using complete facts](/lessons/python-pg-reconciliation).
