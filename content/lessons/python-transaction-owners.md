## The idea in plain language

A transaction groups database operations into one commit or rollback decision. In Psycopg 2 with autocommit disabled, ordinary statements can begin a transaction, including SELECT. Leaving an idle-in-transaction connection around can retain locks or snapshots and interfere with service operations.

A connection and its transaction have different lifetimes. The caller may own a reusable connection while a function owns one new transaction. Psycopg's with conn commits when its block succeeds and rolls back when its block raises; it does not close the connection. A with conn.cursor() block closes that cursor. The caller eventually closes the borrowed connection.

The lab chooses a strict boundary: before SQL, require open, idle, non-autocommit and explicitly configured READ COMMITTED. Reject an existing active/failed transaction without committing, rolling it back or closing the caller's work. Never assume a nested connection context creates a nested independent transaction. Savepoints are a separate mechanism, outside this lab's API.

The caller provisions the schema and configures search_path/isolation before calling. Runtime functions do not change connection settings. Input snapshot/validation happens first, before database access; effects from the iterator are not database effects and cannot be undone by rollback. A batch result is returned only after successful context exit/commit.

The local example lists distinct ownership, without simulating a database. The PostgreSQL cases leave an active caller transaction, call the API and prove it remains active and uncommitted; the caller then commits its own row. A failed transaction is also rejected and preserved. Empty batches still follow the documented preconditions.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
owners = {"connection": "caller", "transaction": "batch function", "cursor": "batch function"}
print(owners["connection"])
print(owners["transaction"] == owners["cursor"])
```

## Apply it in the PostgreSQL lab

Do not use this context inside unrelated caller work. The lab checks transaction state first and leaves rejected active/failed state untouched. The caller closes conn after all its work.

```text
# Caller setup, outside library calls:
conn.set_session(isolation_level="READ COMMITTED", autocommit=False)
# Only proceed when conn is idle and points at the trusted disposable schema.
with conn:                          # owns one new transaction
    with conn.cursor() as cursor:    # owns this cursor
        cursor.execute("SELECT count(*) FROM feed_record")
        row = cursor.fetchone()
# Success committed; a raised error would cause rollback. conn is still open.
```

## Guided practice

Trace connection, cursor and transaction ownership independently. Explain why committing an already active caller transaction would violate the API.

## Independent practice

Implement require-idle use and with-connection/cursor scopes. Test active, failed, autocommit, wrong-isolation and closed connections without altering caller state.

## Check your work

Borrowed connections stay open and reusable; rejected caller transactions stay under caller control.

Continue to [Rollback, visibility & uncertain commit outcomes](/lessons/python-transaction-failures).
