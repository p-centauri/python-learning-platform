## A transaction is not automatic serialization
At PostgreSQL's default Read Committed isolation, each statement sees a snapshot of committed data as that statement starts. Two transactions can both read stock=1, decide a sale is allowed and then each record an order. Wrapping those reads and writes in transactions provides atomicity, but does not automatically make the business decision safe.

Encode a simple invariant in one conditional statement:
```sql
UPDATE inventory
SET available = available - 1
WHERE sku = :sku AND available > 0
RETURNING available;
```
An empty result means the reservation did not succeed. Record the order in the same transaction. A database constraint `CHECK (available >= 0)` remains a useful second line of defense. When a decision needs several related reads, lock the rows with `SELECT ... FOR UPDATE`, perform the checks after acquiring the lock and keep the transaction short.

## Claiming a queue item
```sql
WITH candidate AS (
  SELECT id FROM jobs
  WHERE status = 'pending'
  ORDER BY created_at, id
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
UPDATE jobs SET status = 'running', claimed_at = now()
FROM candidate WHERE jobs.id = candidate.id
RETURNING jobs.*;
```
This statement belongs in a short claim transaction. Commit before a slow external operation. A lease or reaper must recover abandoned running jobs. `SKIP LOCKED` intentionally gives an inconsistent view of available rows and is suited to work claiming, not ordinary financial reports. It neither acknowledges a broker message nor makes an external side effect exactly once.

## Deadlocks are about order
If one transaction locks account A then B while another locks B then A, a cycle can form. PostgreSQL aborts a participant. Acquire related locks in a consistent order and retry the entire aborted transaction with a bounded policy. Do not retry only its final statement or issue HTTP calls while holding locks.

## Investigate before changing isolation
Capture the actual statements, transaction boundaries, wait events and execution plans. Serializable can detect unsafe executions but requires retry handling. It is not a substitute for understanding the invariant. Use `EXPLAIN (ANALYZE, BUFFERS)` on safe representative workloads; ANALYZE executes the statement.

## Practice and mastery
Simulate two sessions reserving the last unit, then repair the race. Explain how a worker crash after claim commit is recovered and how duplicate processing is contained. You should distinguish atomicity, isolation and delivery semantics without treating any of them as interchangeable.
