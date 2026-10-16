## The idea in plain language

SQLAlchemy's Engine coordinates database connections and a connection pool. A Session tracks ORM state and a transaction. Neither is a row itself. A Session may not acquire a connection until it executes SQL, but SELECT can start a transaction through autobegin.

The local server owns its Engine until shutdown; the app factory borrows it. A dependency creates one Session per request and closes it at function scope. It does not commit in late dependency cleanup. Pool closure means a checked-out connection returns to the pool, not that every underlying socket is destroyed. Engine disposal is the caller's separate responsibility.

Do not share a Session between independent requests, threads or tasks. Sharing an engine/pool is normal, while each unit of work needs its own Session and transaction boundary. If a caller transaction is already active, the lab service rejects it without commit, rollback or close. Otherwise a service method owns one session.begin block.

Use synchronous FastAPI route functions for the synchronous ORM work in this lab. Calling a blocking driver inside async def still blocks the event loop; the syntax alone cannot change I/O. Choosing an asynchronous driver/session later requires deliberate ownership and failure testing, not merely renaming the route.

Materialize public values before session closure. An ORM attribute can trigger lazy SQL; sending ORM objects into later serialization makes query/lifetime behavior harder to reason about and risks exposing private fields. Tests verify the pool has zero checked-out connections after handled success/failure requests.

The worked example creates a Session without touching PostgreSQL to demonstrate lazy ownership only. The public cases evaluate actual transactions, read cleanup, caller work and pooled connection release on PostgreSQL.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session
engine = create_engine(URL.create("postgresql+psycopg2", host="127.0.0.1", port=1))
with Session(engine) as session:
    print(session.in_transaction())
engine.dispose()
```

## Guided practice

Distinguish engine, pool, connection, Session, transaction and ORM object. Explain why one Session should not be shared between requests.

## Independent practice

Run active-caller rejection and pool-return cases. Explain which owner closes the Session versus disposes the Engine.

## Check your work

Lazy acquisition is not proof of database readiness. Synchronous drivers remain blocking I/O.

Continue to [Service transactions finish before success](/lessons/python-service-transactions).
