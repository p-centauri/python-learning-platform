from datetime import datetime, timezone
from threading import Event as StopEvent
from unittest.mock import MagicMock
from sqlalchemy import Engine, create_engine
import pytest
from academy_durable_outbox import Accepted, Event
from academy_leased_worker import Failure, Lease, Policy, claim, run, settle
from academy_leased_worker.contracts import lease_copy, policy_copy


@pytest.mark.parametrize("bad", [True, 99, 60001, 1.0, "100"])
def test_lease_duration(bad):
    with pytest.raises(ValueError):
        Policy(lease_ms=bad)


@pytest.mark.parametrize("bad", [True, 0, 9, 1.0, "1"])
def test_attempt_limit(bad):
    with pytest.raises(ValueError):
        Policy(max_attempts=bad)


@pytest.mark.parametrize("bad", [[], (0,), (True, 0), (-1, 0), (0, 60001), (0, 1.0)])
def test_backoff_shape_and_values(bad):
    with pytest.raises(ValueError):
        Policy(delays_ms=bad)


@pytest.mark.parametrize("bad", [True, 0, 9, 1.0])
def test_generation(bad):
    with pytest.raises(ValueError):
        Lease(Event("scope", "a", 1, 0), bad, datetime.now(timezone.utc))


def test_naive_deadline_and_mutated_values():
    with pytest.raises(ValueError):
        Lease(Event("scope", "a", 1, 0), 1, datetime.now())
    policy = Policy()
    assert policy_copy(policy) == policy and policy_copy(policy) is not policy
    object.__setattr__(policy, "lease_ms", True)
    with pytest.raises(ValueError):
        policy_copy(policy)
    item = Lease(Event("scope", "a", 1, 0), 1, datetime.now(timezone.utc))
    assert lease_copy(item) == item and lease_copy(item).event is not item.event
    object.__setattr__(item.event, "value", True)
    with pytest.raises(ValueError):
        lease_copy(item)


@pytest.mark.parametrize("bad", [None, {}, "policy"])
def test_claim_boundary_before_sql(bad):
    engine = MagicMock(spec=Engine)
    with pytest.raises(ValueError):
        claim(engine, "scope", bad)
    engine.connect.assert_not_called()


@pytest.mark.parametrize("bad", [None, {}, "retry", Accepted(Event("other", "a", 1, 0))])
def test_settlement_boundary_before_sql(bad):
    engine = MagicMock(spec=Engine)
    lease = Lease(Event("scope", "a", 1, 0), 1, datetime.now(timezone.utc))
    with pytest.raises(ValueError):
        settle(engine, lease, bad)
    engine.connect.assert_not_called()


@pytest.mark.parametrize("bad", [True, 0, 65, 1.0])
def test_admission_bound(bad):
    with pytest.raises(ValueError):
        run(MagicMock(spec=Engine), "scope", Policy(), lambda e: Accepted(e), StopEvent(), limit=bad)


def test_pre_stopped_does_not_open_connection():
    engine = MagicMock(spec=Engine)
    stop = StopEvent()
    stop.set()
    assert run(engine, "scope", Policy(), lambda e: Accepted(e), stop).attempted == 0
    engine.connect.assert_not_called()


def test_sqlite_is_not_postgres():
    engine = create_engine("sqlite://")
    try:
        with pytest.raises(ValueError):
            claim(engine, "scope", Policy())
    finally:
        engine.dispose()


def test_strict_namespace_and_stop():
    engine = MagicMock(spec=Engine)
    with pytest.raises(ValueError):
        run(engine, "Upper", Policy(), lambda e: Failure.RETRY, StopEvent())
    with pytest.raises(ValueError):
        run(engine, "scope", Policy(), lambda e: Failure.RETRY, object())
    engine.connect.assert_not_called()
