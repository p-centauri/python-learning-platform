from pathlib import Path
from threading import Event as StopEvent
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from academy_ingestion_service import Datum
from academy_durable_outbox import ConflictingEvent, Event, record
from academy_durable_outbox.evidence import state
from academy_leased_worker import Policy, claim, run, settle
from academy_leased_worker.evidence import wait_due
from academy_stream_delivery import InvalidEnvelope, deliver, encode, publisher
from academy_stream_delivery.contracts import stream
from academy_stream_delivery.evidence import crash, pending, restart_owned, wait_idle

pytestmark = pytest.mark.live


def test_broker_acceptance_precedes_the_consumer_effect(live):
    engine, broker, ns = live
    record(engine, ns, [Datum("a", 1, 7)])
    report = run(engine, ns, Policy(), publisher(broker), StopEvent())
    assert report.settled == 1 and state(engine, ns)["pending"] == 0
    assert state(engine, ns)["inbox"] == 0 and broker.client.xlen(stream(ns)) == 1
    result = deliver(engine, broker, ns, "effects", "first")
    assert result.acknowledged and state(engine, ns)["applied"] == 1 and pending(broker, ns) == 0


@pytest.mark.parametrize("version", [1, 2])
def test_supported_wire_versions_apply_zero_as_one_effect(live, version):
    engine, broker, ns = live
    broker.append(ns, encode(Event(ns, "a", 1, 0), version=version))
    assert deliver(engine, broker, ns, "effects", "first").event == Event(ns, "a", 1, 0)
    assert state(engine, ns)["applied"] == 1 and state(engine, ns)["total"] == 0


def test_duplicate_stream_entries_have_one_stable_effect(live):
    engine, broker, ns = live
    event = Event(ns, "a", 1, 7)
    first = broker.append(ns, encode(event, version=1))
    second = broker.append(ns, encode(event, version=2))
    assert first != second and broker.client.xlen(stream(ns)) == 2
    assert deliver(engine, broker, ns, "effects", "first").acknowledged
    assert deliver(engine, broker, ns, "effects", "second").acknowledged
    assert state(engine, ns)["applied"] == 1 and state(engine, ns)["total"] == 7
    assert pending(broker, ns) == 0


def test_conflicting_duplicate_stays_pending(live):
    engine, broker, ns = live
    for value in (7, 8):
        broker.append(ns, encode(Event(ns, "a", 1, value)))
    deliver(engine, broker, ns, "effects", "first")
    with pytest.raises(ConflictingEvent):
        deliver(engine, broker, ns, "effects", "second")
    assert pending(broker, ns) == 1 and state(engine, ns)["total"] == 7


@pytest.mark.parametrize("payload", [b'{"schema":3}', b"{}"])
def test_unknown_or_malformed_schema_stays_pending_without_effect(live, payload):
    engine, broker, ns = live
    broker.append(ns, payload)
    with pytest.raises(InvalidEnvelope):
        deliver(engine, broker, ns, "effects", "first")
    assert pending(broker, ns) == 1 and state(engine, ns)["inbox"] == 0


def test_other_namespace_payload_is_not_applied_or_acknowledged(live):
    engine, broker, ns = live
    broker.append(ns, encode(Event("other", "a", 1, 7)))
    with pytest.raises(InvalidEnvelope):
        deliver(engine, broker, ns, "effects", "first")
    assert state(engine, "other")["inbox"] == 0 and pending(broker, ns) == 1


def test_no_new_entry_does_not_mean_no_pending(live):
    engine, broker, ns = live
    broker.append(ns, encode(Event(ns, "a", 1, 7)))
    broker.take(ns, "effects", "first", recover=False, idle_ms=100, cursor=b"0-0")
    assert deliver(engine, broker, ns, "effects", "second").event is None and pending(broker, ns) == 1
    assert deliver(engine, broker, ns, "effects", "second", recover=True, idle_ms=60000).event is None
    wait_idle(broker, ns)
    assert deliver(engine, broker, ns, "effects", "second", recover=True).acknowledged
    assert pending(broker, ns) == 0


def test_effect_check_failure_leaves_pending_and_no_inbox(live):
    engine, broker, ns = live
    broker.append(ns, encode(Event(ns, "a", 1, 7)))
    with engine.begin() as c:
        c.execute(text("ALTER TABLE delivery_effect ADD CONSTRAINT reject_effect CHECK (total=0)"))
    with pytest.raises(IntegrityError) as caught:
        deliver(engine, broker, ns, "effects", "first")
    assert caught.value.orig.pgcode == "23514" and pending(broker, ns) == 1
    assert state(engine, ns)["inbox"] == 0 and engine.pool.checkedout() == 0


def test_deleted_pending_payload_is_reported_not_invented(live):
    engine, broker, ns = live
    id = broker.append(ns, encode(Event(ns, "a", 1, 7)))
    broker.take(ns, "effects", "first", recover=False, idle_ms=100, cursor=b"0-0")
    broker.client.xdel(stream(ns), id)
    result = deliver(engine, broker, ns, "effects", "second", recover=True, idle_ms=0)
    assert result.event is None and result.deleted == (id,)
    assert state(engine, ns)["inbox"] == 0


def test_xack_removes_pending_without_deleting_the_stream(live):
    engine, broker, ns = live
    id = broker.append(ns, encode(Event(ns, "a", 1, 7)))
    result = deliver(engine, broker, ns, "effects", "first")
    assert result.acknowledged and pending(broker, ns) == 0
    assert broker.client.xlen(stream(ns)) == 1 and not broker.ack(ns, "effects", id)
    broker.setup(ns, "effects")  # Explicit existing group setup must not reset position.
    assert deliver(engine, broker, ns, "effects", "first").event is None


def test_real_exit_after_broker_flush_republishes_stable_identity(live):
    engine, broker, ns = live
    record(engine, ns, [Datum("a", 1, 7)])
    assert crash(engine, broker, Path(__file__).parents[1] / "worker_process.py", "after-append", ns) == 91
    assert broker.client.xlen(stream(ns)) == 1 and state(engine, ns)["pending"] == 1
    wait_due(engine, ns)
    lease = claim(engine, ns, Policy(100, 3, (0, 0)))
    assert lease.generation == 2
    assert settle(engine, lease, publisher(broker)(lease.event))
    assert broker.client.xlen(stream(ns)) == 2
    for consumer in ("first", "second"):
        assert deliver(engine, broker, ns, "effects", consumer).acknowledged
    assert state(engine, ns)["applied"] == 1 and state(engine, ns)["pending"] == 0


def test_real_exit_after_consumer_commit_reclaims_then_acks(live):
    engine, broker, ns = live
    broker.append(ns, encode(Event(ns, "a", 1, 7)))
    assert crash(engine, broker, Path(__file__).parents[1] / "worker_process.py", "after-effect", ns) == 92
    assert state(engine, ns)["applied"] == 1 and pending(broker, ns) == 1
    wait_idle(broker, ns)
    assert deliver(engine, broker, ns, "effects", "second", recover=True).acknowledged
    assert state(engine, ns)["applied"] == 1 and pending(broker, ns) == 0


def test_actual_controlled_broker_restart_preserves_stream_and_pending(live):
    engine, broker, ns = live
    broker.append(ns, encode(Event(ns, "a", 1, 7)))
    broker.take(ns, "effects", "first", recover=False, idle_ms=100, cursor=b"0-0")
    restart_owned(broker)
    assert broker.client.xlen(stream(ns)) == 1 and pending(broker, ns) == 1
    assert deliver(engine, broker, ns, "effects", "second", recover=True, idle_ms=0).acknowledged
    assert state(engine, ns)["applied"] == 1
