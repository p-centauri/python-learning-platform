from dataclasses import FrozenInstanceError
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import DBAPIError
from academy_ingestion_service import Datum, Receipt
from academy_ingestion_service.contracts import ConflictingDatum
from academy_competing_ingestion import (
    Decision,
    Delivery,
    RetryExhausted,
    RetryPolicy,
    UnknownOutcome,
    classify_sqlstate,
    retry_ingest,
)
import academy_competing_ingestion.retry as module


@pytest.mark.parametrize(
    "code,decision",
    [
        ("40001", Decision.RETRY),
        ("40P01", Decision.RETRY),
        ("55P03", Decision.STOP),
        ("57014", Decision.STOP),
        ("23505", Decision.STOP),
        ("23514", Decision.STOP),
        ("08006", Decision.RECONCILE),
        ("08P01", Decision.RECONCILE),
        ("57P01", Decision.RECONCILE),
        ("57P02", Decision.RECONCILE),
        (None, Decision.RECONCILE),
        ("XX000", Decision.STOP),
    ],
)
def test_sqlstate_not_message(code, decision):
    assert classify_sqlstate(code) is decision


@pytest.mark.parametrize("code", ["", "deadlock detected", "40p01", "40001 ", "4000", 40001, True])
def test_invalid_state(code):
    with pytest.raises(ValueError):
        classify_sqlstate(code)


@pytest.mark.parametrize(
    "changes",
    [
        {"max_attempts": 0},
        {"max_attempts": 4},
        {"max_attempts": True},
        {"lock_timeout_ms": 0},
        {"lock_timeout_ms": True},
        {"statement_timeout_ms": 2000},
        {"statement_timeout_ms": 5001},
        {"delays": (float("nan"), 0.0)},
        {"delays": (2.0, 0.0)},
        {"delays": (True, 0.0)},
        {"delays": (0, 0.0)},
        {"delays": []},
        {"delays": (0.0,)},
    ],
)
def test_policy_bounds(changes):
    with pytest.raises(ValueError):
        RetryPolicy(**changes)


def test_frozen_policy_and_one_attempt():
    policy = RetryPolicy(max_attempts=1, delays=())
    with pytest.raises(FrozenInstanceError):
        policy.max_attempts = 3
    assert policy.max_attempts == 1


class DriverFailure(Exception):
    def __init__(self, code):
        self.pgcode = code
        super().__init__("sensitive driver wording must not choose retry")


def db_error(code):
    return DBAPIError("private statement", {"private": "value"}, DriverFailure(code))


class Owned:
    def __init__(self, index, trace):
        self.index, self.trace = index, trace

    def __enter__(self):
        self.trace.append(("open", self.index))
        return self

    def __exit__(self, *args):
        self.trace.append(("closed", self.index))


@pytest.fixture
def controlled(monkeypatch):
    trace, calls = [], []
    monkeypatch.setattr(module, "require_engine", lambda engine: None)

    def session(engine, policy):
        return Owned(len(calls) + 1, trace)

    monkeypatch.setattr(module, "owned_session", session)
    return trace, calls


def test_retry_replays_snapshot_after_closed_session(controlled, monkeypatch):
    trace, calls = controlled
    original = Datum("a", 1, 0)
    rows = [original, Datum("a", 1, 0)]

    def ingest(session, namespace, batch):
        calls.append((session, namespace, batch))
        if len(calls) < 3:
            raise db_error("40001" if len(calls) == 1 else "40P01")
        return Receipt(2, 1, 1)

    monkeypatch.setattr(module, "ingest", ingest)

    def sleep(delay):
        assert trace[-1][0] == "closed"
        object.__setattr__(original, "value", 9)
        rows.clear()  # Caller mutations after snapshot cannot change later attempts.
        trace.append(("sleep", delay))

    delivery = retry_ingest(object(), "feed", rows, policy=RetryPolicy(delays=(0.1, 0.2)), sleep=sleep)
    assert delivery == Delivery(Receipt(2, 1, 1), 3)
    assert all(c[2] == (Datum("a", 1, 0), Datum("a", 1, 0)) for c in calls)
    assert len({id(c[0]) for c in calls}) == 3
    assert trace == [
        ("open", 1),
        ("closed", 1),
        ("sleep", 0.1),
        ("open", 2),
        ("closed", 2),
        ("sleep", 0.2),
        ("open", 3),
        ("closed", 3),
    ]


@pytest.mark.parametrize("code", [None, "08006", "57P01"])
def test_unknown_is_never_replayed(code, controlled, monkeypatch):
    trace, calls = controlled
    error = db_error(code)

    def ingest(*args):
        calls.append(args)
        raise error

    monkeypatch.setattr(module, "ingest", ingest)
    with pytest.raises(UnknownOutcome) as caught:
        retry_ingest(object(), "feed", [], sleep=lambda d: pytest.fail("unknown outcome retried"))
    assert caught.value.attempts == 1 and caught.value.__cause__ is error
    assert "private" not in str(caught.value)
    assert len(calls) == 1 and trace[-1] == ("closed", 1)


@pytest.mark.parametrize("code", ["55P03", "57014", "23505"])
def test_known_stop_preserves_original(code, controlled, monkeypatch):
    trace, calls = controlled
    error = db_error(code)

    def ingest(*args):
        calls.append(args)
        raise error

    monkeypatch.setattr(module, "ingest", ingest)
    with pytest.raises(DBAPIError) as caught:
        retry_ingest(object(), "feed", [], sleep=lambda d: pytest.fail("stop retried"))
    assert caught.value is error and len(calls) == 1 and trace[-1][0] == "closed"


def test_exhaustion_bound_and_cause(controlled, monkeypatch):
    trace, calls = controlled
    error = db_error("40P01")

    def ingest(*args):
        calls.append(args)
        raise error

    monkeypatch.setattr(module, "ingest", ingest)
    sleeps = []
    with pytest.raises(RetryExhausted) as caught:
        retry_ingest(object(), "feed", [], sleep=sleeps.append)
    assert caught.value.attempts == 3 and caught.value.sqlstate == "40P01"
    assert caught.value.__cause__ is error and len(calls) == 3 and sleeps == [0.0, 0.0]


def test_domain_failure_not_retried(controlled, monkeypatch):
    trace, calls = controlled
    error = ConflictingDatum()

    def ingest(*args):
        calls.append(args)
        raise error

    monkeypatch.setattr(module, "ingest", ingest)
    with pytest.raises(ConflictingDatum) as caught:
        retry_ingest(object(), "feed", [], sleep=lambda d: pytest.fail("domain failure retried"))
    assert caught.value is error and len(calls) == 1


def test_sleeper_failure_preserved_after_close(controlled, monkeypatch):
    trace, calls = controlled
    monkeypatch.setattr(module, "ingest", lambda *args: (_ for _ in ()).throw(db_error("40001")))
    error = RuntimeError("sleep failed")

    def sleep(delay):
        assert trace[-1][0] == "closed"
        raise error

    with pytest.raises(RuntimeError) as caught:
        retry_ingest(object(), "feed", [], sleep=sleep)
    assert caught.value is error


@pytest.mark.parametrize("rows", [[Datum("a", 1, 1)] * 65, (r for r in []), [object()]])
def test_input_rejected_before_database(rows):
    with pytest.raises(ValueError):
        retry_ingest(object(), "feed", rows)


def test_conflicting_batch_rejected_before_database():
    with pytest.raises(ConflictingDatum):
        retry_ingest(object(), "feed", [Datum("a", 1, 1), Datum("a", 1, 2)])


def test_sqlite_is_not_postgres():
    engine = create_engine("sqlite://")
    try:
        with pytest.raises(ValueError):
            retry_ingest(engine, "feed", [])
    finally:
        engine.dispose()
