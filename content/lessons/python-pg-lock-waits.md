## The idea in plain language

A database lock makes another operation wait while an incompatible owner still holds it. It does not mean every read stops: PostgreSQL can often read a committed row version while another transaction writes. Which operation waits depends on the lock modes, row/key and transaction boundaries.

Use a real observation to coordinate a test. The lab starts a holder, starts a challenger on another connection and checks pg_blocking_pids for the actual waiter and holder. Only after that observation does it release the holder. A short sleep merely gives other code time to run; it cannot prove a lock was acquired or a wait occurred.

The fixture exercises one pending reading. After a holder commits, the challenger returns an exact duplicate or a domain conflict depending on its value. After the holder rolls back, the challenger can insert its own value. No overwrite is allowed. Prior insertion and RETURNING behavior remain unchanged. Each thread owns a separate Session; the observation uses a separate driver connection.

lock_timeout bounds time waiting to acquire each database lock. statement_timeout bounds an individual server statement, including its execution/waits. The lab applies both with transaction-local set_config through the Session after_begin event using its supplied Connection. This keeps the prior ingest function's idle-Session precondition. Values are bound separately; transaction exit resets local settings.

An actual lock timeout produces 55P03; the lab's long statement experiment produces 57014. This small retry policy stops on both. PostgreSQL cancels the statement, and an aborted transaction needs rollback before reuse. Neither setting bounds input parsing, pool admission, Python coordination or a whole job. Event waits, polling and future joins have separate finite experiment bounds.

## Worked example

This local Python illustration explains one idea. The PostgreSQL lab supplies the actual database observations.

```python
lock_ms, statement_ms = 50, 100
print(lock_ms < statement_ms)
```

## Guided practice

Trace holder, waiter and observer; distinguish a lock-wait limit from a statement limit.

## Independent practice

Run commit/rollback/same/different cases and the real 55P03/57014 experiments. Record pool cleanup and reset local settings.

## Check your work

Do not infer ordering from sleep or treat a cancelled statement as a reusable successful transaction.

Continue to [Deadlocks, lock order and the chosen victim](/lessons/python-pg-deadlocks).
