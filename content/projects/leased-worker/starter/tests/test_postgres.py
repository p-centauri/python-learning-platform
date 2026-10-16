from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Event as StopEvent
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from academy_ingestion_service import Datum
from academy_durable_outbox import Accepted, Event, consume, record
from academy_durable_outbox.evidence import state
from academy_leased_worker import Failure, Policy, claim, install, run, settle
from academy_leased_worker.evidence import process, wait_due

pytestmark = pytest.mark.postgres
POLICY = Policy(5000, 3, (0, 0))


def seed(engine, namespace="scope", value=7):
    record(engine, namespace, [Datum("a", 1, value)])


def job(engine, namespace="scope"):
    with engine.connect() as connection:
        return dict(
            connection.execute(text("SELECT * FROM delivery_job WHERE namespace=:ns"), dict(ns=namespace))
            .mappings()
            .one()
        )


def expire(engine, namespace="scope"):
    # Controlled SQL fixture, distinct from observed actual child-expiry evidence.
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE delivery_job SET lease_until=clock_timestamp()-interval '2 minutes' "
                "WHERE namespace=:ns AND state='leased'"
            ),
            dict(ns=namespace),
        )


def test_claim_commits_without_publisher_or_held_pool(engine):
    seed(engine)
    lease = claim(engine, "scope", POLICY)
    assert lease.event == Event("scope", "a", 1, 7) and lease.generation == 1
    assert job(engine)["state"] == "leased" and state(engine, "scope")["pending"] == 1
    assert engine.pool.checkedout() == 0
    assert claim(engine, "scope", POLICY) is None


def test_fresh_generation_rejects_stale_acceptance_and_failure(engine):
    seed(engine)
    old = claim(engine, "scope", POLICY)
    expire(engine)
    fresh = claim(engine, "scope", POLICY)
    assert fresh.generation == 2 and fresh.event == old.event
    assert not settle(engine, old, Accepted(old.event))
    assert not settle(engine, old, Failure.POISON)
    assert job(engine)["state"] == "leased" and state(engine, "scope")["pending"] == 1
    assert settle(engine, fresh, consume(engine, fresh.event))
    assert job(engine)["state"] == "done" and state(engine, "scope")["applied"] == 1
    assert not settle(engine, fresh, Accepted(fresh.event))


def test_expiry_without_reclaim_rejects_settlement(engine):
    seed(engine)
    lease = claim(engine, "scope", POLICY)
    expire(engine)
    assert not settle(engine, lease, Accepted(lease.event))
    assert state(engine, "scope")["pending"] == 1


def test_exact_deadline_payload_key_and_acceptance(engine):
    seed(engine)
    lease = claim(engine, "scope", POLICY)
    from datetime import timedelta

    assert not settle(
        engine, replace(lease, deadline=lease.deadline + timedelta(seconds=1)), Accepted(lease.event)
    )
    changed = replace(lease, event=Event("scope", "a", 1, 8))
    assert not settle(engine, changed, Accepted(changed.event))
    other = replace(lease, event=Event("other", "a", 1, 7))
    assert not settle(engine, other, Accepted(other.event))
    with pytest.raises(ValueError):
        settle(engine, lease, Accepted(Event("scope", "a", 1, 8)))
    assert settle(engine, lease, consume(engine, lease.event))


def test_persisted_backoff_prevents_early_retry(engine):
    seed(engine)
    policy = Policy(5000, 2, (60000,))
    lease = claim(engine, "scope", policy)
    with engine.connect() as c:
        before = c.execute(text("SELECT clock_timestamp()")).scalar_one()
    assert settle(engine, lease, Failure.RETRY)
    saved = job(engine)
    assert saved["next_at"] > before and (saved["next_at"] - before).total_seconds() >= 60
    assert claim(engine, "scope", policy) is None
    with engine.begin() as c:
        c.execute(text("UPDATE delivery_job SET next_at=clock_timestamp()-interval '1 second'"))
    later = claim(engine, "scope", policy)
    assert later.generation == 2
    assert settle(engine, later, Failure.RETRY)
    assert job(engine)["state"] == "dead" and job(engine)["reason"] == "exhausted"
    assert claim(engine, "scope", policy) is None and state(engine, "scope")["pending"] == 1


def test_expired_lease_backoff_is_from_saved_expiry(engine):
    seed(engine)
    policy = Policy(5000, 2, (60000,))
    lease = claim(engine, "scope", policy)
    with engine.begin() as c:
        c.execute(text("UPDATE delivery_job SET lease_until=clock_timestamp()-interval '1 second'"))
    assert claim(engine, "scope", policy) is None
    expire(engine)
    fresh = claim(engine, "scope", policy)
    assert fresh.generation == 2 and fresh.event == lease.event


def test_poison_is_quarantined_without_ack_or_automatic_redrive(engine):
    seed(engine)
    lease = claim(engine, "scope", POLICY)
    assert settle(engine, lease, Failure.POISON)
    assert job(engine)["state"] == "dead" and job(engine)["reason"] == "poison"
    assert claim(engine, "scope", POLICY) is None
    record(engine, "scope", [Datum("a", 1, 7)])
    assert claim(engine, "scope", POLICY) is None and state(engine, "scope")["pending"] == 1


def test_expired_final_attempt_is_quarantined(engine):
    seed(engine)
    policy = Policy(5000, 1, ())
    lease = claim(engine, "scope", policy)
    expire(engine)
    assert claim(engine, "scope", policy) is None
    assert job(engine)["reason"] == "exhausted" and job(engine)["state"] == "dead"
    assert not settle(engine, lease, Accepted(lease.event))


def test_scope_policy_cannot_silently_change(engine):
    seed(engine)
    lease = claim(engine, "scope", POLICY)
    with pytest.raises(ValueError):
        claim(engine, "scope", Policy(5000, 2, (0,)))
    assert job(engine)["generation"] == 1
    assert settle(engine, lease, consume(engine, lease.event))


def test_two_workers_claim_distinct_complete_keys(engine):
    record(engine, "scope", [Datum("a", 1, 0), Datum("a", 2, 7)])
    with ThreadPoolExecutor(max_workers=2) as pool:
        leases = list(pool.map(lambda _: claim(engine, "scope", POLICY), range(2)))
    assert {lease.event.key for lease in leases} == {("scope", "a", 1), ("scope", "a", 2)}
    for lease in leases:
        assert settle(engine, lease, consume(engine, lease.event))
    assert state(engine, "scope")["applied"] == 2 and engine.pool.checkedout() == 0


def test_skip_locked_available_is_not_empty(engine):
    seed(engine)
    lease = claim(engine, "scope", POLICY)
    settle(engine, lease, Failure.RETRY)
    with engine.begin() as holder:
        holder.execute(text("SELECT 1 FROM delivery_job FOR UPDATE")).all()
        assert claim(engine, "scope", POLICY) is None
        assert state(engine, "scope")["pending"] == 1
    assert claim(engine, "scope", POLICY).generation == 2


def test_namespace_and_acknowledged_adoption(engine):
    seed(engine, "left", 0)
    seed(engine, "right", 7)
    left = claim(engine, "left", POLICY)
    settle(engine, left, consume(engine, left.event))
    assert claim(engine, "left", POLICY) is None
    assert state(engine, "right")["pending"] == 1 and claim(engine, "right", POLICY).event.value == 7


def test_settlement_and_ack_share_real_rollback(engine):
    seed(engine)
    lease = claim(engine, "scope", POLICY)
    with engine.begin() as c:
        c.execute(text("ALTER TABLE delivery_outbox ADD CONSTRAINT no_ack CHECK (NOT acknowledged)"))
    with pytest.raises(IntegrityError) as caught:
        settle(engine, lease, Accepted(lease.event))
    assert caught.value.orig.pgcode == "23514"
    assert job(engine)["state"] == "leased" and state(engine, "scope")["pending"] == 1
    assert engine.pool.checkedout() == 0


def test_callback_error_schedules_then_preserves_original(engine):
    seed(engine)
    failure = RuntimeError("trusted test failure")

    def broken(item):
        assert engine.pool.checkedout() == 0
        raise failure

    with pytest.raises(RuntimeError) as caught:
        run(engine, "scope", POLICY, broken, StopEvent())
    assert caught.value is failure and job(engine)["reason"] == "retry"
    assert state(engine, "scope")["pending"] == 1


def test_callback_mutation_or_false_acceptance_is_not_ack(engine):
    seed(engine)

    def forged(item):
        object.__setattr__(item, "value", 8)
        return Accepted(item)

    with pytest.raises(ValueError):
        run(engine, "scope", POLICY, forged, StopEvent())
    assert job(engine)["reason"] == "retry" and state(engine, "scope")["pending"] == 1


def test_bounded_admission_finishes_current_then_stops(engine):
    record(engine, "scope", [Datum("a", 1, 7), Datum("b", 1, 8)])
    stop = StopEvent()

    def publishing(item):
        assert engine.pool.checkedout() == 0
        stop.set()
        return consume(engine, item)

    result = run(engine, "scope", POLICY, publishing, stop)
    assert (result.attempted, result.settled, result.stale) == (1, 1, 0)
    assert state(engine, "scope")["pending"] == 1
    stop.clear()
    assert run(engine, "scope", POLICY, lambda e: consume(engine, e), stop, limit=1).settled == 1


def test_adoption_and_admission_are_count_bounded(engine):
    record(engine, "scope", [Datum("a", r, 7) for r in range(1, 9)])
    result = run(engine, "scope", POLICY, lambda e: consume(engine, e), StopEvent(), limit=2)
    assert result.attempted == 2 and state(engine, "scope")["pending"] == 6


@pytest.mark.parametrize("stage,code,applied", [("after-claim", 81, 0), ("after-accept", 82, 1)])
def test_actual_process_exit_expiry_and_reclaim(engine, stage, code, applied):
    seed(engine)
    policy = Policy(100, 3, (0, 0))
    evidence = process(engine, Path(__file__).parents[1] / "worker_process.py", stage, "scope")
    assert evidence["exit"] == code
    assert state(engine, "scope")["applied"] == applied and state(engine, "scope")["pending"] == 1
    wait_due(engine, "scope")
    lease = claim(engine, "scope", policy)
    assert lease.generation == 2
    assert settle(engine, lease, consume(engine, lease.event))
    assert state(engine, "scope")["applied"] == 1 and state(engine, "scope")["pending"] == 0


def test_actual_sigterm_stops_new_claims_after_current_acceptance(engine):
    record(engine, "scope", [Datum("a", 1, 7), Datum("b", 1, 8)])
    evidence = process(engine, Path(__file__).parents[1] / "worker_process.py", "graceful", "scope")
    assert evidence["exit"] == 0 and evidence["report"] == dict(attempted=1, settled=1, stale=0)
    assert state(engine, "scope")["pending"] == 1 and state(engine, "scope")["applied"] == 1
    assert engine.pool.checkedout() == 0


def test_setup_is_explicit_one_time(engine):
    with pytest.raises(ProgrammingError) as caught:
        install(engine)
    assert caught.value.orig.pgcode == "42P07"


def test_actual_database_expiry_rejects_same_stored_deadline(engine):
    seed(engine)
    lease = claim(engine, "scope", Policy(100, 2, (0,)))
    wait_due(engine, "scope")
    assert job(engine)["lease_until"] == lease.deadline
    assert not settle(engine, lease, Accepted(lease.event))
    assert state(engine, "scope")["pending"] == 1


def test_adoption_is_at_most_64_intents_per_claim(engine):
    for start in (0, 64, 128):
        record(engine, "scope", [Datum("k-" + str(i), 1, 7) for i in range(start, min(start + 64, 129))])
    assert claim(engine, "scope", POLICY) is not None
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM delivery_job")).scalar_one() == 64
    assert claim(engine, "scope", POLICY) is not None
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM delivery_job")).scalar_one() == 128


def test_replay_after_callback_response_loss_applies_once(engine):
    seed(engine)

    def lost(item):
        consume(engine, item)
        raise RuntimeError("modeled lost response after real local acceptance")

    with pytest.raises(RuntimeError):
        run(engine, "scope", POLICY, lost, StopEvent())
    assert state(engine, "scope")["applied"] == 1 and state(engine, "scope")["pending"] == 1
    assert run(engine, "scope", POLICY, lambda e: consume(engine, e), StopEvent()).settled == 1
    assert state(engine, "scope")["applied"] == 1 and state(engine, "scope")["pending"] == 0
