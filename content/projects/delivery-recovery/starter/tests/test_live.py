from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from academy_ingestion_service import Datum
from academy_durable_outbox import Accepted, Event, consume, record
from academy_leased_worker import Failure, Policy, claim, settle
from academy_stream_delivery import deliver
from academy_stream_delivery.envelope import encode
from academy_stream_delivery.contracts import stream
from academy_delivery_recovery import DeadJob, Pruned, inspect_dead, prune, redrive

POLICY = Policy(lease_ms=60000, max_attempts=3, delays_ms=(0, 0))


def poisoned(live, *, id="a", revision=1, value=7):
    engine, _, namespace = live
    record(engine, namespace, [Datum(id, revision, value)])
    lease = claim(engine, namespace, POLICY)
    assert lease is not None and settle(engine, lease, Failure.POISON)
    return lease


def completed(live, *, value=7, id=b"*"):
    engine, broker, namespace = live
    record(engine, namespace, [Datum("a", 1, value)])
    lease = claim(engine, namespace, POLICY)
    assert lease is not None
    # Explicit append and same complete-event producer receipt; no inferred consumer effect.
    transport_id = broker.client.xadd(stream(namespace), {b"payload": encode(lease.event)}, id=id)
    assert type(transport_id) is bytes
    assert settle(engine, lease, Accepted(lease.event))
    return lease, transport_id


def state(engine, namespace):
    with engine.connect() as connection:
        return tuple(
            connection.execute(
                text("""
            SELECT j.generation,j.state,j.reason,p.max_attempts,o.acknowledged
            FROM delivery_job j JOIN worker_policy p USING(namespace)
            JOIN delivery_outbox o USING(namespace,id,revision) WHERE j.namespace=:ns ORDER BY j.id,j.revision
        """),
                dict(ns=namespace),
            ).all()
        )


def history(engine):
    with engine.connect() as connection:
        return {
            table: tuple(connection.execute(text(f"SELECT * FROM {table} ORDER BY 1,2,3")).all())
            for table in ("feed_record", "delivery_outbox", "delivery_inbox", "delivery_job")
        }


def test_scoped_bounded_ordered_inspection_is_read_only(live):
    engine, broker, ns = live
    poisoned(live, id="a", revision=1, value=0)
    poisoned(live, id="a", revision=2, value=9)
    poisoned((engine, broker, "other"), id="z")
    before = state(engine, ns)
    result = inspect_dead(engine, ns, limit=1)
    assert result == (DeadJob(Event(ns, "a", 1, 0), 1, "poison", 3),)
    assert len(inspect_dead(engine, ns)) == 2 and state(engine, ns) == before


def test_redrive_preserves_identity_generation_policy_and_fences_old_lease(live):
    engine, _, ns = live
    old = poisoned(live)
    selected = inspect_dead(engine, ns)[0]
    assert redrive(engine, selected, approve=True)
    assert not redrive(engine, selected, approve=True)
    assert state(engine, ns)[0] == (1, "ready", "retry", 3, False)
    assert not settle(engine, old, Accepted(old.event))
    new = claim(engine, ns, POLICY)
    assert new is not None and new.event == old.event and new.generation == 2
    assert not settle(engine, old, Accepted(old.event))
    assert settle(engine, new, Accepted(new.event))
    assert not redrive(engine, selected, approve=True)


@pytest.mark.parametrize(
    "field,value",
    [
        ("generation", 2),
        ("maximum", 2),
        ("reason", "exhausted"),
        ("value", 8),
        ("revision", 2),
        ("namespace", "other"),
    ],
)
def test_mismatched_dead_snapshot_cannot_mutate(live, field, value):
    engine, _, ns = live
    poisoned(live)
    selected = inspect_dead(engine, ns)[0]
    data = dict(generation=selected.generation, maximum=selected.maximum, reason=selected.reason)
    event = dict(namespace=ns, id="a", revision=1, value=7)
    (data if field in data else event)[field] = value
    before = state(engine, ns)
    assert not redrive(engine, DeadJob(Event(**event), **data), approve=True)
    assert state(engine, ns) == before


def test_concurrent_redrive_has_one_success(live):
    engine, _, ns = live
    poisoned(live)
    selected = inspect_dead(engine, ns)[0]
    barrier = Barrier(2)

    def attempt():
        barrier.wait(timeout=5)
        return redrive(engine, selected, approve=True)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(attempt) for _ in range(2)]
        assert sorted(f.result(timeout=10) for f in futures) == [False, True]
    assert state(engine, ns)[0] == (1, "ready", "retry", 3, False)


def test_exhaustion_stays_terminal_after_repeated_explicit_requests(live):
    engine, _, ns = live
    record(engine, ns, [Datum("a", 1, 7)])
    for generation in (1, 2, 3):
        lease = claim(engine, ns, POLICY)
        assert lease is not None and lease.generation == generation
        assert settle(engine, lease, Failure.RETRY)
    job = inspect_dead(engine, ns)[0]
    for _ in range(2):
        assert not redrive(engine, job, approve=True)
    assert claim(engine, ns, POLICY) is None and state(engine, ns)[0][0] == 3


def test_real_database_failure_rolls_back_redrive_and_releases_pool(live):
    engine, _, ns = live
    poisoned(live)
    selected = inspect_dead(engine, ns)[0]
    with engine.begin() as c:
        c.execute(
            text(
                "CREATE FUNCTION reject_ready() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'fixture failure'; END $$"
            )
        )
        c.execute(
            text(
                "CREATE TRIGGER reject_ready BEFORE UPDATE ON delivery_job FOR EACH ROW EXECUTE FUNCTION reject_ready()"
            )
        )
    before = state(engine, ns)
    with pytest.raises(DBAPIError):
        redrive(engine, selected, approve=True)
    assert state(engine, ns) == before and engine.pool.checkedout() == 0


def test_prune_requires_local_effect_then_keeps_all_database_history_and_replay_safe(live):
    engine, broker, ns = live
    lease, id = completed(live, value=0)
    assert prune(engine, broker, ns, id, allow_loss=True) is Pruned.BLOCKED
    assert deliver(engine, broker, ns, "effects", "reader").acknowledged
    before = history(engine)
    assert prune(engine, broker, ns, id, allow_loss=True) is Pruned.REMOVED
    assert broker.client.xlen(stream(ns)) == 0 and history(engine) == before
    assert prune(engine, broker, ns, id, allow_loss=True) is Pruned.MISSING
    # A new transport ID carries the same Event; retained inbox prevents a second effect.
    broker.append(ns, encode(lease.event, version=1))
    assert deliver(engine, broker, ns, "effects", "reader").acknowledged
    assert history(engine) == before
    with engine.connect() as c:
        assert tuple(
            c.execute(
                text("SELECT total,applied FROM delivery_effect WHERE namespace=:ns"), dict(ns=ns)
            ).one()
        ) == (0, 1)
    assert record(engine, ns, [Datum("a", 1, 0)]).enqueued == 0
    assert claim(engine, ns, POLICY) is None


@pytest.mark.parametrize("condition", ["pending", "unread", "no-groups", "nine-groups"])
def test_every_current_group_blocks_unsafe_deletion(live, condition):
    engine, broker, ns = live
    _, id = completed(live)
    assert deliver(engine, broker, ns, "effects", "reader").acknowledged
    if condition == "no-groups":
        broker.client.xgroup_destroy(stream(ns), "effects")
    else:
        for index in range(8 if condition == "nine-groups" else 1):
            broker.setup(ns, "audit" + str(index))
        if condition == "pending":
            assert (
                broker.take(ns, "audit0", "other", recover=False, idle_ms=0, cursor=b"0-0").entry is not None
            )
    assert prune(engine, broker, ns, id, allow_loss=True) is Pruned.BLOCKED
    assert broker.client.xlen(stream(ns)) == 1


def test_acknowledged_second_group_allows_pruning(live):
    engine, broker, ns = live
    broker.setup(ns, "audit")
    _, id = completed(live)
    for group in ("effects", "audit"):
        assert deliver(engine, broker, ns, group, "reader").acknowledged
    assert prune(engine, broker, ns, id, allow_loss=True) is Pruned.REMOVED


def test_large_sequence_comparison_has_no_float_rounding(live):
    engine, broker, ns = live
    _, id = completed(live, id=b"1-9007199254740993")
    assert deliver(engine, broker, ns, "effects", "reader").acknowledged
    broker.client.xgroup_setid(stream(ns), "effects", b"1-9007199254740992")
    assert prune(engine, broker, ns, id, allow_loss=True) is Pruned.BLOCKED
    broker.client.xgroup_setid(stream(ns), "effects", id)
    assert prune(engine, broker, ns, id, allow_loss=True) is Pruned.REMOVED


def test_missing_stream_id_does_not_mutate_database(live):
    engine, broker, ns = live
    before = history(engine)
    assert prune(engine, broker, ns, b"1-0", allow_loss=True) is Pruned.MISSING
    assert history(engine) == before


def test_payload_replacement_is_rechecked_atomically(live):
    from academy_delivery_recovery.support import remove_payload, selected_entry

    engine, broker, ns = live
    _, id = completed(live)
    assert deliver(engine, broker, ns, "effects", "reader").acknowledged
    selected = selected_entry(broker, ns, id)
    assert selected is not None
    broker.client.delete(stream(ns))
    broker.client.xadd(stream(ns), {b"payload": encode(Event(ns, "a", 1, 99))}, id=id)
    broker.client.xgroup_create(stream(ns), "effects", id=id)
    assert remove_payload(broker, ns, selected) is Pruned.BLOCKED
    assert broker.client.xlen(stream(ns)) == 1


def test_local_effect_without_producer_completion_cannot_be_pruned(live):
    engine, broker, ns = live
    record(engine, ns, [Datum("a", 1, 7)])
    lease = claim(engine, ns, POLICY)
    assert lease is not None
    id = broker.append(ns, encode(lease.event))
    consume(engine, lease.event)
    assert deliver(engine, broker, ns, "effects", "reader").acknowledged
    assert prune(engine, broker, ns, id, allow_loss=True) is Pruned.BLOCKED
    assert broker.client.xlen(stream(ns)) == 1


def test_broker_deletion_cannot_be_rolled_back_by_database_failure(live, monkeypatch):
    import academy_delivery_recovery.operations as operations

    engine, broker, ns = live
    _, id = completed(live)
    assert deliver(engine, broker, ns, "effects", "reader").acknowledged
    before = history(engine)
    original = operations.remove_payload

    def fail_after_delete(*args):
        assert original(*args) is Pruned.REMOVED
        raise RuntimeError("fixture lost result after actual deletion")

    monkeypatch.setattr(operations, "remove_payload", fail_after_delete)
    with pytest.raises(RuntimeError):
        prune(engine, broker, ns, id, allow_loss=True)
    assert broker.client.xlen(stream(ns)) == 0 and history(engine) == before
    assert prune(engine, broker, ns, id, allow_loss=True) is Pruned.MISSING
    assert engine.pool.checkedout() == 0
