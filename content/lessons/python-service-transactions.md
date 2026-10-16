## The idea in plain language

Keep routing thin: validate/authenticate/authorize, create domain values, call a service and map explicit outcomes. The service owns database behavior. This avoids duplicating transaction decisions across HTTP endpoints, command-line jobs and future workers.

The lab receives immutable Datum values and a borrowed idle Session. It validates the whole bounded list/tuple, then owns one session.begin transaction. SQLAlchemy expressions bind caller values separately. PostgreSQL ON CONFLICT RETURNING identifies an insertion, including a returned zero; a missing returned row requires full-key stored-value comparison. Exact repeat counts; changed value raises a domain conflict.

Return Receipt only after the transaction context successfully exits. A commit-boundary error must prevent HTTP success. A late conflict or CHECK failure rolls back the whole batch, including new sources, while earlier committed rows remain. Healthy sessions become idle/reusable; broken connection/rollback paths retain native error chains.

The route maps the expected domain conflict to 409. Database errors get a generic private 503 without SQL, credentials or row values. Do not present every 503 as retryable or a known rollback. Lost commit acknowledgment can leave an unknown outcome; future recovery needs reconnect/reconciliation and a specific retry policy. Input/remote effects are not rolled back by the database.

For reads, the service also owns one transaction and produces DTO values before closing its Session. The dependency then releases resources at function scope. Committing in background work or after sending 200 would make a failed write appear successful.

The local illustration explains zero versus no returned value. PostgreSQL cases prove first/repeated receipts, late rollback and observer visibility. A modeled pre-commit fault verifies response ordering but does not reproduce every real network commit failure.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
returned_values: list[int | None] = [0, None, 5]
for value in returned_values:
    print("inserted" if value is not None else "inspect duplicate")
```

## Guided practice

Trace validation, insertion/duplicate comparison, commit and response in order. Explain why zero is not an ignored conflict.

## Independent practice

Implement ingest with explicit transaction ownership and bound statements. Add a late failure and inspect state from a separate connection.

## Check your work

No partial receipt or early success; private storage errors do not establish a safe automatic retry.

Continue to [Alembic migrations & explicit schema evolution](/lessons/python-alembic-evolution).
