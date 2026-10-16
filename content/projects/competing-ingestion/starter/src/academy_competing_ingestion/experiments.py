"""Supplied bounded experiments for an explicitly disposable, already migrated schema.

These use trusted fixture writes, not production endpoints or hostile learner execution.
Each thread owns its Session. Events/pg_blocking_pids observe ordering; no sleep asserts a race.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, Lock, get_ident
import time
from typing import Any
import psycopg2
from psycopg2.extensions import connection as PgConnection
from sqlalchemy import Connection, Engine, event, func, insert, select, text
from sqlalchemy.engine import ExceptionContext
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, SessionTransaction
from academy_ingestion_service import Datum, ingest, read_page
from academy_ingestion_service.contracts import ConflictingDatum
from academy_ingestion_service.models import RecordRow, SourceRow
from .contracts import RetryPolicy
from .retry import retry_ingest


def source(engine: Engine, namespace: str) -> None:
    with engine.begin() as connection:
        connection.execute(insert(SourceRow).values(namespace=namespace))


def observer(engine: Engine) -> PgConnection:
    url = engine.url
    result = psycopg2.connect(
        host=url.host,
        port=url.port or 5432,
        dbname=url.database,
        user=url.username,
        password=url.password,
        options=url.query.get("options", ""),
        connect_timeout=5,
    )
    result.autocommit = True
    return result


def wait_for_block(observer: PgConnection, waiter: int, holder: int) -> None:
    until = time.monotonic() + 1.5
    while time.monotonic() < until:
        with observer.cursor() as cursor:
            cursor.execute("SELECT pg_blocking_pids(%s)", (waiter,))
            row = cursor.fetchone()
        if row is not None and holder in row[0]:
            return
        time.sleep(0.005)  # Poll pacing only, never establishes ordering by itself.
    raise RuntimeError("database wait was not observed within the experiment bound")


def competing_insert(engine: Engine, *, commit_holder: bool, challenger_value: int = 5) -> dict[str, object]:
    namespace = (
        "race-"
        + ("commit" if commit_holder else "rollback")
        + ("-same" if challenger_value == 5 else "-different")
    )
    source(engine, namespace)
    written, challenger_started, release = Event(), Event(), Event()
    pids: dict[str, int] = {}

    class RollbackFixture(Exception):
        pass

    def holder() -> str:
        try:
            with Session(engine) as session, session.begin():
                session.execute(text("SELECT set_config('statement_timeout', '5000', true)"))
                pids["holder"] = session.execute(text("SELECT pg_backend_pid()")).scalar_one()
                session.execute(
                    insert(RecordRow).values(namespace=namespace, id="raced", revision=1, value=5)
                )
                written.set()
                if not release.wait(5):
                    raise RuntimeError("fixture release was not received")
                if not commit_holder:
                    raise RollbackFixture()
            return "committed"
        except RollbackFixture:
            return "rolled-back"

    def challenger() -> str:
        with Session(engine) as session:

            def started(session: Session, transaction: SessionTransaction, connection: Connection) -> None:
                connection.execute(
                    text(
                        "SELECT set_config('lock_timeout', '2000', true), set_config('statement_timeout', '5000', true)"
                    )
                )
                pids["challenger"] = connection.execute(text("SELECT pg_backend_pid()")).scalar_one()
                challenger_started.set()

            event.listen(session, "after_begin", started)
            try:
                receipt = ingest(session, namespace, (Datum("raced", 1, challenger_value),))
            except ConflictingDatum:
                return "conflict"
            return "inserted" if receipt.inserted == 1 else "duplicate"

    watch = observer(engine)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(holder)
            try:
                if not written.wait(5):
                    first.result(timeout=1)
                    raise RuntimeError("holder did not reach its write")
                second = pool.submit(challenger)
                if not challenger_started.wait(5):
                    raise RuntimeError("challenger did not begin")
                wait_for_block(watch, pids["challenger"], pids["holder"])
            finally:
                release.set()
            outcome = first.result(timeout=6)
            second_outcome = second.result(timeout=6)
        with Session(engine) as session:
            values = read_page(session, namespace).items
        return {
            "wait_observed": True,
            "holder": outcome,
            "challenger": second_outcome,
            "stored_value": values[0].value,
        }
    finally:
        release.set()
        watch.close()


def snapshot_visibility(engine: Engine, isolation: str) -> dict[str, object]:
    if isolation not in {"READ COMMITTED", "REPEATABLE READ"}:
        raise ValueError("unsupported snapshot experiment")
    namespace = "snapshot-" + ("rc" if isolation == "READ COMMITTED" else "rr")
    source(engine, namespace)
    query = select(func.count()).select_from(RecordRow).where(RecordRow.namespace == namespace)
    with engine.connect().execution_options(isolation_level=isolation) as reader:
        with reader.begin():
            before = reader.execute(query).scalar_one()
            with Session(engine) as writer:
                ingest(writer, namespace, (Datum("new", 1, 10),))
            during = reader.execute(query).scalar_one()
        with reader.begin():
            after = reader.execute(query).scalar_one()
    return {"isolation": isolation, "before": before, "during": during, "after": after}


def serializable_gate(engine: Engine) -> dict[str, object]:
    # A deliberately tiny append-only invariant: at most one admission in this namespace.
    namespace = "serial-gate"
    source(engine, namespace)
    query = select(func.count()).select_from(RecordRow).where(RecordRow.namespace == namespace)
    outcomes: list[str] = []
    with (
        engine.connect().execution_options(isolation_level="SERIALIZABLE") as first,
        engine.connect().execution_options(isolation_level="SERIALIZABLE") as second,
    ):
        left, right = first.begin(), second.begin()
        try:
            for connection in (first, second):
                connection.execute(text("SELECT set_config('statement_timeout', '5000', true)"))
                assert connection.execute(query).scalar_one() == 0
            for connection, transaction, identity in ((first, left, "a"), (second, right, "b")):
                try:
                    connection.execute(
                        insert(RecordRow).values(namespace=namespace, id=identity, revision=1, value=1)
                    )
                    transaction.commit()
                    outcomes.append("committed")
                except DBAPIError as error:
                    transaction.rollback()
                    outcomes.append(str(getattr(error.orig, "pgcode", None)))
        finally:
            if left.is_active:
                left.rollback()
            if right.is_active:
                right.rollback()
    # A new complete transaction must read the invariant again, not replay the failed INSERT.
    with engine.connect().execution_options(isolation_level="SERIALIZABLE") as fresh, fresh.begin():
        count = fresh.execute(query).scalar_one()
        retry_action = "skip-already-admitted" if count else "admit"
    return {"outcomes": outcomes, "fresh_count": count, "fresh_decision": retry_action}


def deadlock_retry(engine: Engine) -> dict[str, object]:
    source(engine, "deadlock")
    with engine.connect() as connection:
        configured = int(
            connection.execute(
                text("SELECT setting FROM pg_settings WHERE name='deadlock_timeout'")
            ).scalar_one()
        )
    if configured >= 2000:
        raise RuntimeError("the disposable experiment requires deadlock_timeout below 2000 milliseconds")
    gate = Barrier(2, timeout=4)
    lock = Lock()
    seen: set[int] = set()
    states: list[str] = []

    def coordinate(
        connection: Connection, cursor: Any, statement: str, parameters: Any, context: Any, executemany: bool
    ) -> None:
        if statement.startswith("INSERT INTO feed_record"):
            with lock:
                first = get_ident() not in seen
                seen.add(get_ident())
            if first:
                gate.wait()

    def observed(error: ExceptionContext) -> None:
        code = getattr(error.original_exception, "pgcode", None)
        if code is not None:
            with lock:
                states.append(code)

    event.listen(engine, "after_cursor_execute", coordinate)
    event.listen(engine, "handle_error", observed)
    try:
        rows = (Datum("a", 1, 5), Datum("b", 1, 10))
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(retry_ingest, engine, "deadlock", rows)
            second = pool.submit(retry_ingest, engine, "deadlock", tuple(reversed(rows)))
            deliveries = [first.result(timeout=12), second.result(timeout=12)]
    finally:
        event.remove(engine, "after_cursor_execute", coordinate)
        event.remove(engine, "handle_error", observed)
    with Session(engine) as session:
        final = read_page(session, "deadlock").items
    return {
        "observed_sqlstates": states,
        "attempts": sorted(item.attempts for item in deliveries),
        "inserted": sorted(item.receipt.inserted for item in deliveries),
        "duplicates": sorted(item.receipt.duplicates for item in deliveries),
        "stored": [(item.id, item.value) for item in final],
    }


def lock_timeout(engine: Engine) -> dict[str, object]:
    source(engine, "locked")
    states: list[str] = []

    def observe(error: ExceptionContext) -> None:
        code = getattr(error.original_exception, "pgcode", None)
        if code is not None:
            states.append(code)

    event.listen(engine, "handle_error", observe)
    try:
        return _lock_timeout(engine, states)
    finally:
        event.remove(engine, "handle_error", observe)


def _lock_timeout(engine: Engine, states: list[str]) -> dict[str, object]:
    with Session(engine) as holder, holder.begin():
        holder.execute(
            select(SourceRow).where(SourceRow.namespace == "locked").with_for_update()
        ).scalar_one()
        with ThreadPoolExecutor(max_workers=1) as pool:
            failed = pool.submit(
                retry_ingest,
                engine,
                "locked",
                (Datum("waiting", 1, 5),),
                policy=RetryPolicy(lock_timeout_ms=50),
            )
            try:
                failed.result(timeout=6)
            except DBAPIError as error:
                state = str(getattr(error.orig, "pgcode", None))
            else:
                raise AssertionError("held lock unexpectedly permitted delivery")
    with Session(engine) as session:
        page = read_page(session, "locked")
    return {
        "sqlstate": state,
        "stored_count": len(page.items),
        "attempts": len(states),
        "automatic_retry": len(states) > 1,
    }
