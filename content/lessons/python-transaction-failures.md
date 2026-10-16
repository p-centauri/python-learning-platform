## The idea in plain language

A statement error usually leaves a PostgreSQL transaction aborted. Subsequent commands cannot continue normally until rollback (or a suitable savepoint recovery). Catching the exception and returning success would hide the failure while leaving broken transaction state.

Let the error leave the owned transaction context so rollback is attempted. Preserve the driver's original exception type and SQLSTATE. On a healthy connection, rollback clears that transaction and permits a later valid batch. If the connection itself breaks, rollback can fail too; preserve native exception chaining rather than promise recovery.

Database rollback covers database writes in that transaction. It does not undo an HTTP request, a file write, a consumed iterator or a message already sent. Keep a batch input snapshot separate from its database commit. Later worker/outbox/recovery units will address coordination with external effects; this lab makes no durable acknowledgment.

Use another connection to examine committed state. The same connection can see its own uncommitted changes, so that alone cannot prove commit visibility. The lab first commits rows, then attempts a batch that inserts a new source/row before a late conflict. After rollback, a separate observer sees the old rows and no new source/row.

An error near commit can have an unknown outcome if the server committed but the client lost the acknowledgment. Do not assert that every connection error means nothing was stored. Stable keys permit later reconciliation after reconnecting, but do not create a distributed exactly-once guarantee. There are no automatic retries here; a future policy must distinguish known rollback, uncertain commit, retryable failures and external effects.

The worked example names separate effects. Real rollback and second-connection visibility are tested against PostgreSQL, including a CHECK violation after an earlier insertion in the same batch.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
effects = {"database_transaction": "rollback scope", "consumed_input": "outside rollback", "sent_message": "outside rollback"}
print(effects["consumed_input"])
print(effects["database_transaction"])
```

## Apply it in the PostgreSQL lab

The lab uses a late CHECK failure and a changed-value conflict to prove rollback with actual second-connection observations. If rollback or commit communication fails, preserve the native chain and reconcile unknown outcomes.

```text
# Each failure is caught outside the transaction context.
try:
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO feed_source VALUES (%s)", ("rollback-probe",))
            cursor.execute("SELECT 1/0")
except psycopg2.errors.DivisionByZero as error:
    assert error.pgcode == "22012"
# On a healthy connection, the new source was rolled back.
# Check absence from another configured connection; do not infer it from a flag.
```

## Guided practice

Distinguish known rollback, failed rollback and lost commit acknowledgment. Explain why a second connection matters.

## Independent practice

Add a late CHECK failure and a changed-value conflict. Prove the earlier batch survives, the new batch vanishes and the healthy connection can be reused.

## Check your work

No partial success report or automatic retry. Input and remote effects are outside database rollback.

Continue to [Duplicates need a key and a conflict rule](/lessons/python-persistence-duplicates).
