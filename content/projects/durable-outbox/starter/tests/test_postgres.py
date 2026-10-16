from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event as Signal
import secrets
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool
from fastapi.testclient import TestClient
import pytest
from academy_ingestion_service import Datum, create_app, ingest, make_engine
from academy_ingestion_service.contracts import ConflictingDatum
from academy_durable_outbox import Accepted, ConflictingEvent, Event, consume, install, publish_one, record
from academy_durable_outbox.evidence import crash, state

pytestmark = pytest.mark.postgres


def test_atomic_batch_duplicates_zero_revision_and_scope(engine):
    result = record(engine, "scope", [Datum("a", 1, 0), Datum("a", 1, 0), Datum("a", 2, 7)])
    assert (result.receipt.observed, result.receipt.inserted, result.receipt.duplicates, result.enqueued) == (
        3,
        2,
        1,
        2,
    )
    assert state(engine, "scope") == dict(records=2, outbox=2, pending=2, inbox=0, total=0, applied=0)
    assert record(engine, "other", [Datum("a", 1, 0)]).enqueued == 1
    assert state(engine, "scope")["outbox"] == 2


def test_late_conflict_rolls_back_prefix_and_event(engine):
    record(engine, "scope", [Datum("z", 1, 7)])
    with pytest.raises(ConflictingDatum):
        record(engine, "scope", [Datum("a", 1, 0), Datum("z", 1, 9)])
    assert state(engine, "scope") == dict(records=1, outbox=1, pending=1, inbox=0, total=0, applied=0)


def test_matching_prior_fact_is_adopted_once(engine):
    with Session(engine) as session:
        ingest(session, "scope", [Datum("a", 1, 7)])
    assert state(engine, "scope")["outbox"] == 0
    first = record(engine, "scope", [Datum("a", 1, 7)])
    assert first.receipt.duplicates == 1 and first.enqueued == 1
    assert record(engine, "scope", [Datum("a", 1, 7)]).enqueued == 0


def test_repeated_acknowledged_fact_does_not_requeue(engine):
    record(engine, "scope", [Datum("a", 1, 7)])
    assert publish_one(engine, "scope", lambda item: consume(engine, item)) == Event("scope", "a", 1, 7)
    assert record(engine, "scope", [Datum("a", 1, 7)]).enqueued == 0
    assert publish_one(engine, "scope", lambda item: consume(engine, item)) is None
    assert state(engine, "scope") == dict(records=1, outbox=1, pending=0, inbox=1, total=7, applied=1)


def test_inbox_and_aggregate_use_full_key_and_keep_zero(engine):
    for item in [
        Event("scope", "a", 1, 0),
        Event("scope", "a", 1, 0),
        Event("scope", "a", 2, 7),
        Event("other", "a", 1, 9),
    ]:
        assert consume(engine, item) == Accepted(item)
    assert state(engine, "scope")["inbox"] == 2 and state(engine, "scope")["applied"] == 2
    assert state(engine, "scope")["total"] == 7 and state(engine, "other")["total"] == 9


def test_consumer_changed_duplicate_keeps_original_effect(engine):
    consume(engine, Event("scope", "a", 1, 7))
    with pytest.raises(ConflictingEvent):
        consume(engine, Event("scope", "a", 1, 9))
    assert state(engine, "scope")["total"] == 7 and state(engine, "scope")["applied"] == 1


def test_actual_constraint_failure_rolls_back_inbox_and_effect(engine):
    with engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE delivery_effect ADD CONSTRAINT fixture_cap CHECK (total<=5)")
    with pytest.raises(DBAPIError) as failure:
        consume(engine, Event("scope", "a", 1, 7))
    assert failure.value.orig.pgcode == "23514"
    assert state(engine, "scope")["inbox"] == 0 and state(engine, "scope")["applied"] == 0


def test_publisher_failure_keeps_pending_and_calls_once(engine):
    record(engine, "scope", [Datum("a", 1, 7)])
    calls = []

    def fail(item):
        calls.append(item)
        raise RuntimeError("modeled transport failure")

    with pytest.raises(RuntimeError):
        publish_one(engine, "scope", fail)
    assert len(calls) == 1 and state(engine, "scope")["pending"] == 1
    assert state(engine, "scope")["applied"] == 0


def test_committed_effect_then_modeled_lost_response_replays_safely(engine):
    record(engine, "scope", [Datum("a", 1, 7)])

    def fail(item):
        consume(engine, item)
        raise RuntimeError("modeled missing response after real commit")

    with pytest.raises(RuntimeError):
        publish_one(engine, "scope", fail)
    assert state(engine, "scope")["pending"] == 1 and state(engine, "scope")["applied"] == 1
    publish_one(engine, "scope", lambda item: consume(engine, item))
    assert state(engine, "scope")["pending"] == 0 and state(engine, "scope")["applied"] == 1


@pytest.mark.parametrize("confirmation", [None, Accepted(Event("other", "a", 1, 7))])
def test_wrong_confirmation_cannot_acknowledge(engine, confirmation):
    record(engine, "scope", [Datum("a", 1, 7)])
    with pytest.raises(ValueError):
        publish_one(engine, "scope", lambda item: confirmation)
    assert state(engine, "scope")["pending"] == 1


def test_callback_mutation_cannot_change_claimed_identity(engine):
    record(engine, "scope", [Datum("a", 1, 7)])

    def mutate(item):
        object.__setattr__(item, "namespace", "other")
        return Accepted(item)

    with pytest.raises(ValueError):
        publish_one(engine, "scope", mutate)
    assert state(engine, "scope")["pending"] == 1 and state(engine, "other")["outbox"] == 0


def test_skip_locked_selects_next_available_without_claiming_global_order(engine):
    record(engine, "scope", [Datum("a", 1, 7), Datum("b", 1, 9)])
    other = make_engine(engine.url)
    try:
        with other.begin() as holder:
            holder.execute(
                text("SELECT id FROM delivery_outbox WHERE namespace='scope' AND id='a' FOR UPDATE")
            ).all()
            assert publish_one(engine, "scope", lambda item: consume(engine, item)) == Event(
                "scope", "b", 1, 9
            )
            assert state(engine, "scope")["pending"] == 1
        publish_one(engine, "scope", lambda item: consume(engine, item))
    finally:
        other.dispose()
    assert state(engine, "scope")["total"] == 16


def test_none_can_mean_available_rows_are_locked(engine):
    record(engine, "scope", [Datum("a", 1, 7)])
    other = make_engine(engine.url)
    try:
        with other.begin() as holder:
            holder.execute(text("SELECT id FROM delivery_outbox WHERE namespace='scope' FOR UPDATE")).all()
            assert publish_one(engine, "scope", lambda item: consume(engine, item)) is None
            assert state(engine, "scope")["pending"] == 1
    finally:
        other.dispose()


def test_separate_workers_claim_different_rows_and_release(engine):
    record(engine, "scope", [Datum("a", 1, 7), Datum("b", 1, 9)])
    claimed, release = Signal(), Signal()
    other = make_engine(engine.url)

    def first():
        def publish(item):
            assert item.id == "a"
            claimed.set()
            assert release.wait(5)
            return consume(engine, item)

        return publish_one(engine, "scope", publish)

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            task = pool.submit(first)
            try:
                assert claimed.wait(3)
                assert publish_one(other, "scope", lambda item: consume(other, item)).id == "b"
            finally:
                release.set()
            assert task.result(timeout=6).id == "a"
    finally:
        other.dispose()
    assert state(engine, "scope")["pending"] == 0 and state(engine, "scope")["applied"] == 2


def test_foreign_key_rejects_intent_without_source_fact(engine):
    with pytest.raises(DBAPIError) as failure:
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO delivery_outbox(namespace,id,revision,value) VALUES ('scope','a',1,7)")
            )
    assert failure.value.orig.pgcode == "23503"


@pytest.mark.parametrize(
    "stage,code", [("before-record-commit", 71), ("after-record-commit", 72), ("after-consume-commit", 73)]
)
def test_actual_process_crash_and_restart(engine, stage, code):
    if stage == "after-consume-commit":
        record(engine, "scope", [Datum("a", 1, 7)])
    assert crash(engine, Path(__file__).resolve().parents[1] / "crash_worker.py", stage, "scope") == code
    observed = state(engine, "scope")
    if stage == "before-record-commit":
        assert observed == dict(records=0, outbox=0, pending=0, inbox=0, total=0, applied=0)
        record(engine, "scope", [Datum("a", 1, 7)])
    elif stage == "after-record-commit":
        assert observed == dict(records=1, outbox=1, pending=1, inbox=0, total=0, applied=0)
    else:
        assert observed == dict(records=1, outbox=1, pending=1, inbox=1, total=7, applied=1)
    assert publish_one(engine, "scope", lambda item: consume(engine, item)) == Event("scope", "a", 1, 7)
    assert state(engine, "scope") == dict(records=1, outbox=1, pending=0, inbox=1, total=7, applied=1)


def test_install_is_explicit_one_time_and_does_not_erase_data(engine):
    record(engine, "scope", [Datum("a", 1, 7)])
    with pytest.raises(DBAPIError) as failure:
        install(engine)
    assert failure.value.orig.pgcode == "42P07"
    assert state(engine, "scope")["outbox"] == 1


def test_previous_api_permissions_public_fields_and_opt_in_boundary(engine):
    record(engine, "scope", [Datum("a", 1, 0)])
    token = secrets.token_urlsafe(32)
    with TestClient(create_app(engine, {token: "scope"})) as client:
        assert client.get("/namespaces/scope/readings").status_code == 401
        headers = {"Authorization": "Bearer " + token}
        assert client.get("/namespaces/other/readings", headers=headers).status_code == 403
        response = client.get("/namespaces/scope/readings", headers=headers)
        assert response.status_code == 200 and response.json()["items"] == [
            {"id": "a", "revision": 1, "value": 0}
        ]
        assert (
            client.post(
                "/namespaces/scope/readings",
                headers=headers,
                json={"items": [{"id": "b", "revision": 1, "value": 7}]},
            ).status_code
            == 200
        )
    assert state(engine, "scope")["records"] == 2 and state(engine, "scope")["outbox"] == 1


def test_local_settings_and_owned_pool_return_after_failure(engine):
    record(engine, "scope", [Datum("a", 1, 7)])
    with pytest.raises(RuntimeError):
        publish_one(engine, "scope", lambda item: (_ for _ in ()).throw(RuntimeError()))
    with engine.connect() as connection:
        assert connection.execute(text("SHOW lock_timeout")).scalar_one() == "0"
        assert connection.execute(text("SHOW statement_timeout")).scalar_one() == "0"
    assert isinstance(engine.pool, QueuePool) and engine.pool.checkedout() == 0
