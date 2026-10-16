import asyncio
import httpx
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from academy_ingestion_service import Datum, Receipt, create_app, ingest
from academy_ingestion_service.models import RecordRow
from academy_competing_ingestion import Delivery, RetryPolicy, UnknownOutcome, reconcile, retry_ingest
from academy_competing_ingestion.experiments import (
    competing_insert,
    deadlock_retry,
    lock_timeout,
    serializable_gate,
    snapshot_visibility,
    source,
)
import academy_competing_ingestion.retry as module

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize(
    "commit,value,status,stored",
    [
        (True, 5, "duplicate", 5),
        (True, 9, "conflict", 5),
        (False, 5, "inserted", 5),
        (False, 9, "inserted", 9),
    ],
)
def test_competing_insert_observes_wait_and_winner(engine, commit, value, status, stored):
    report = competing_insert(engine, commit_holder=commit, challenger_value=value)
    assert report == {
        "wait_observed": True,
        "holder": "committed" if commit else "rolled-back",
        "challenger": status,
        "stored_value": stored,
    }
    assert engine.pool.checkedout() == 0


@pytest.mark.parametrize("isolation,during", [("READ COMMITTED", 1), ("REPEATABLE READ", 0)])
def test_real_snapshot_visibility(engine, isolation, during):
    assert snapshot_visibility(engine, isolation) == {
        "isolation": isolation,
        "before": 0,
        "during": during,
        "after": 1,
    }
    with engine.connect() as connection:
        assert connection.get_isolation_level() == "READ COMMITTED"
    assert engine.pool.checkedout() == 0


def test_serializable_invariant_restarts_whole_decision(engine):
    report = serializable_gate(engine)
    assert sorted(report["outcomes"]) == ["40001", "committed"]
    assert report["fresh_count"] == 1 and report["fresh_decision"] == "skip-already-admitted"
    assert engine.pool.checkedout() == 0


def test_real_deadlock_retries_fresh_owned_transaction(engine):
    report = deadlock_retry(engine)
    assert report["observed_sqlstates"] == ["40P01"]
    assert report["attempts"] == [1, 2] and report["inserted"] == [0, 2] and report["duplicates"] == [0, 2]
    assert report["stored"] == [("a", 5), ("b", 10)]
    assert engine.pool.checkedout() == 0


def test_actual_lock_timeout_is_not_automatic_retry(engine):
    assert lock_timeout(engine) == {
        "sqlstate": "55P03",
        "stored_count": 0,
        "attempts": 1,
        "automatic_retry": False,
    }
    assert engine.pool.checkedout() == 0


def test_scoped_full_keys_unique_counts_and_read_only(engine):
    rows = (Datum("a", 1, 0), Datum("a", 2, 7), Datum("b", 1, 9))
    retry_ingest(engine, "feed", rows)
    retry_ingest(engine, "other", (Datum("a", 1, 99),))
    report = reconcile(engine, "feed", [rows[0], rows[0], Datum("a", 2, 8), Datum("missing", 1, 4)])
    assert (
        report.matched_keys == 1
        and report.missing == (Datum("missing", 1, 4),)
        and report.conflicts == (Datum("a", 2, 8),)
    )
    assert report.state == "conflict"
    assert reconcile(engine, "feed", rows).state == "complete"
    assert reconcile(engine, "unknown", rows).missing == rows
    with engine.connect() as connection:
        stored = (
            connection.execute(
                select(RecordRow.value)
                .where(RecordRow.namespace == "feed")
                .order_by(RecordRow.id, RecordRow.revision)
            )
            .scalars()
            .all()
        )
    assert stored == [0, 7, 9] and engine.pool.checkedout() == 0


def test_missing_does_not_prove_rollback_of_inflight_writer(engine):
    source(engine, "pending")
    with Session(engine) as writer, writer.begin():
        writer.execute(RecordRow.__table__.insert().values(namespace="pending", id="a", revision=1, value=0))
        assert reconcile(engine, "pending", [Datum("a", 1, 0)]).state == "missing"
    assert reconcile(engine, "pending", [Datum("a", 1, 0)]).state == "complete"
    assert engine.pool.checkedout() == 0


def test_actual_commit_then_modeled_ack_loss_reconciles_without_replay(engine, monkeypatch):
    calls = []

    def missing_ack(session, namespace, rows):
        calls.append(1)
        ingest(session, namespace, rows)  # Actual commit precedes the modeled lost response.
        raise DBAPIError(
            "private statement", {}, RuntimeError("modeled response loss"), connection_invalidated=True
        )

    monkeypatch.setattr(module, "ingest", missing_ack)
    with pytest.raises(UnknownOutcome) as caught:
        retry_ingest(engine, "feed", [Datum("a", 1, 0)], sleep=lambda d: pytest.fail("unknown replayed"))
    assert caught.value.attempts == 1 and calls == [1]
    assert reconcile(engine, "feed", [Datum("a", 1, 0)]).state == "complete"
    assert engine.pool.checkedout() == 0


def test_local_timeouts_reset_and_sleeper_has_no_connection(engine, monkeypatch):
    calls = []
    original = ingest

    def first_fails(session, namespace, rows):
        calls.append(session)
        if len(calls) == 1:
            with session.begin():
                assert session.execute(text("SHOW lock_timeout")).scalar_one() == "50ms"
                assert session.execute(text("SHOW statement_timeout")).scalar_one() == "5s"
                raise DBAPIError("statement", {}, type("Failed", (Exception,), {"pgcode": "40001"})())
        return original(session, namespace, rows)

    monkeypatch.setattr(module, "ingest", first_fails)

    def sleep(delay):
        assert engine.pool.checkedout() == 0

    result = retry_ingest(
        engine, "feed", [Datum("a", 1, 1)], policy=RetryPolicy(lock_timeout_ms=50), sleep=sleep
    )
    assert result == Delivery(Receipt(1, 1, 0), 2) and calls[0] is not calls[1]
    with engine.connect() as connection:
        assert connection.execute(text("SHOW lock_timeout")).scalar_one() == "0"
        assert connection.execute(text("SHOW statement_timeout")).scalar_one() == "0"


def test_wrong_isolation_rejected_without_rows(engine):
    stronger = engine.execution_options(isolation_level="REPEATABLE READ")
    with pytest.raises(ValueError):
        retry_ingest(stronger, "feed", [Datum("a", 1, 1)])
    assert reconcile(engine, "feed", [Datum("a", 1, 1)]).state == "missing"
    assert engine.pool.checkedout() == 0


def test_empty_and_maximum_bound_and_repeats(engine):
    assert retry_ingest(engine, "feed", []) == Delivery(Receipt(0, 0, 0), 1)
    assert reconcile(engine, "feed", []).matched_keys == 0
    rows = tuple(Datum("r" + str(n), 1, n) for n in range(64))
    assert retry_ingest(engine, "feed", rows).receipt.inserted == 64
    assert reconcile(engine, "feed", rows).matched_keys == 64
    assert retry_ingest(engine, "feed", rows).receipt.duplicates == 64
    assert engine.pool.checkedout() == 0


def test_existing_api_keeps_permission_after_retry_and_reconcile(engine):
    retry_ingest(engine, "feed", [Datum("a", 1, 0)])
    assert reconcile(engine, "feed", [Datum("a", 1, 0)]).state == "complete"
    app = create_app(engine, {"q" * 24: "feed"})

    async def requests():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://local"
        ) as client:
            assert (await client.get("/namespaces/feed/readings")).status_code == 401
            client.headers["Authorization"] = "Bearer " + "q" * 24
            assert (await client.get("/namespaces/other/readings")).status_code == 403
            response = await client.get("/namespaces/feed/readings")
            assert response.status_code == 200 and response.json()["items"] == [
                {"id": "a", "revision": 1, "value": 0}
            ]

    asyncio.run(requests())
    assert engine.pool.checkedout() == 0


def test_actual_statement_timeout_does_not_retry(engine, monkeypatch):
    calls = []

    def slow(session, namespace, rows):
        calls.append(session)
        with session.begin():
            session.execute(text("SELECT pg_sleep(0.2)"))
        raise AssertionError("statement deadline did not fire")

    monkeypatch.setattr(module, "ingest", slow)
    with pytest.raises(DBAPIError) as caught:
        retry_ingest(
            engine,
            "feed",
            [],
            policy=RetryPolicy(lock_timeout_ms=50, statement_timeout_ms=100),
            sleep=lambda d: pytest.fail("statement timeout replayed"),
        )
    assert caught.value.orig.pgcode == "57014" and len(calls) == 1
    assert engine.pool.checkedout() == 0
