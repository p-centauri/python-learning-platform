from collections.abc import Callable
import json
from threading import Event as StopEvent
from sqlalchemy import Engine, text
from academy_competing_ingestion.contracts import RetryPolicy, owned_session
from academy_ingestion_service.contracts import field
from academy_durable_outbox import Accepted, Event
from academy_durable_outbox.contracts import validated
from .contracts import Failure, Lease, Policy, Report, integer, lease_copy, policy_copy

_LIMITS = RetryPolicy(max_attempts=1, delays=())


def claim(engine: Engine, namespace: str, policy: Policy, /) -> Lease | None:
    """Short transaction: adopt at most 64 intents, expire at most 64 final leases, claim one."""
    field(namespace)
    selected = policy_copy(policy)
    with owned_session(engine, _LIMITS) as session:
        with session.begin():
            # The source scope must already exist. Policy is immutable for that scope.
            session.execute(
                text("""
                INSERT INTO worker_policy(namespace,lease_ms,max_attempts,delays_ms)
                VALUES (:ns,:ms,:maximum,CAST(:delays AS integer[])) ON CONFLICT DO NOTHING
            """),
                dict(
                    ns=namespace,
                    ms=selected.lease_ms,
                    maximum=selected.max_attempts,
                    delays=list(selected.delays_ms),
                ),
            )
            saved = session.execute(
                text("""
                SELECT lease_ms,max_attempts,delays_ms FROM worker_policy WHERE namespace=:ns FOR SHARE
            """),
                dict(ns=namespace),
            ).one()
            if (saved.lease_ms, saved.max_attempts, tuple(saved.delays_ms)) != (
                selected.lease_ms,
                selected.max_attempts,
                selected.delays_ms,
            ):
                raise ValueError("worker policy differs from the persisted scope policy")
            session.execute(
                text("""
                INSERT INTO delivery_job(namespace,id,revision)
                SELECT o.namespace,o.id,o.revision FROM delivery_outbox o
                WHERE o.namespace=:ns AND NOT o.acknowledged AND NOT EXISTS (
                  SELECT 1 FROM delivery_job j WHERE (j.namespace,j.id,j.revision)=
                    (o.namespace,o.id,o.revision))
                ORDER BY o.id,o.revision LIMIT 64 FOR UPDATE OF o SKIP LOCKED
                ON CONFLICT DO NOTHING
            """),
                dict(ns=namespace),
            )
            session.execute(
                text("""
                WITH expired AS (
                  SELECT namespace,id,revision FROM delivery_job
                  WHERE namespace=:ns AND state='leased' AND generation=:maximum
                    AND lease_until <= clock_timestamp()
                  ORDER BY id,revision LIMIT 64 FOR UPDATE SKIP LOCKED
                ) UPDATE delivery_job j SET state='dead',lease_until=NULL,reason='exhausted'
                  FROM expired x WHERE (j.namespace,j.id,j.revision)=(x.namespace,x.id,x.revision)
            """),
                dict(ns=namespace, maximum=selected.max_attempts),
            )
            row = session.execute(
                text("""
                SELECT j.id,j.revision,o.value FROM delivery_job j JOIN delivery_outbox o
                  ON (j.namespace,j.id,j.revision)=(o.namespace,o.id,o.revision)
                WHERE j.namespace=:ns AND NOT o.acknowledged AND j.generation < :maximum
                  AND ((j.state='ready' AND j.next_at<=clock_timestamp()) OR
                    (j.state='leased' AND j.lease_until +
                      (CAST(:delays AS jsonb) ->> (j.generation::integer-1))::integer * interval '1 millisecond'
                       <= clock_timestamp()))
                ORDER BY j.id,j.revision LIMIT 1 FOR UPDATE OF j SKIP LOCKED
            """),
                dict(ns=namespace, maximum=selected.max_attempts, delays=json.dumps(selected.delays_ms)),
            ).first()
            if row is None:
                return None
            item = Event(namespace, row.id, row.revision, row.value)
            updated = session.execute(
                text("""
                UPDATE delivery_job SET state='leased',generation=generation+1,reason=NULL,
                  lease_until=clock_timestamp() + :ms * interval '1 millisecond'
                WHERE namespace=:ns AND id=:id AND revision=:rev
                RETURNING generation,lease_until
            """),
                dict(ns=namespace, id=item.id, rev=item.revision, ms=selected.lease_ms),
            ).one()
            lease = Lease(item, updated.generation, updated.lease_until)
        return lease


def settle(engine: Engine, lease: Lease, outcome: Accepted | Failure, /) -> bool:
    """Guard by current generation and live DB lease, then commit local settlement."""
    expected = lease_copy(lease)
    if type(outcome) is Accepted:
        if validated(outcome.event) != expected.event:
            raise ValueError("acceptance must match the complete leased event")
    elif type(outcome) is not Failure:
        raise ValueError("expected exact Accepted or Failure")
    item = expected.event
    parameters = dict(
        ns=item.namespace,
        id=item.id,
        rev=item.revision,
        gen=expected.generation,
        deadline=expected.deadline,
        value=item.value,
    )
    with owned_session(engine, _LIMITS) as session:
        with session.begin():
            # Read policy under the job lock; UPDATE checks a fresh clock after any wait.
            row = session.execute(
                text("""
                SELECT j.generation,p.max_attempts,p.delays_ms,o.value FROM delivery_job j
                JOIN worker_policy p ON p.namespace=j.namespace
                JOIN delivery_outbox o ON (o.namespace,o.id,o.revision)=(j.namespace,j.id,j.revision)
                WHERE j.namespace=:ns AND j.id=:id AND j.revision=:rev FOR UPDATE OF j
            """),
                parameters,
            ).first()
            if row is None or row.value != item.value:
                return False
            done = type(outcome) is Accepted
            terminal = outcome is Failure.POISON or expected.generation >= row.max_attempts
            reason = (
                None
                if done
                else "poison"
                if outcome is Failure.POISON
                else "exhausted"
                if terminal
                else "retry"
            )
            state = "done" if done else "dead" if terminal else "ready"
            delay = 0 if done or terminal else row.delays_ms[expected.generation - 1]
            changed = session.execute(
                text("""
                UPDATE delivery_job SET state=:state,reason=:reason,lease_until=NULL,
                  next_at=clock_timestamp() + :delay * interval '1 millisecond'
                WHERE namespace=:ns AND id=:id AND revision=:rev AND state='leased'
                  AND generation=:gen AND lease_until=:deadline AND lease_until>clock_timestamp()
                RETURNING generation
            """),
                {**parameters, "state": state, "reason": reason, "delay": delay},
            ).first()
            if changed is None:
                return False
            if done:
                session.execute(
                    text("""
                    UPDATE delivery_outbox SET acknowledged=true
                    WHERE namespace=:ns AND id=:id AND revision=:rev
                """),
                    parameters,
                )
        return True


def run(
    engine: Engine,
    namespace: str,
    policy: Policy,
    publish: Callable[[Event], Accepted | Failure],
    stop: StopEvent,
    *,
    limit: int = 8,
) -> Report:
    """Sequential finite admission; a stop flag is checked before each new claim."""
    field(namespace)
    selected = policy_copy(policy)
    integer(limit, 1, 64)
    if not callable(publish) or type(stop) is not StopEvent:
        raise ValueError("expected publisher and exact threading.Event")
    attempted = settled = stale = 0
    while attempted < limit and not stop.is_set():
        lease = claim(engine, namespace, selected)
        if lease is None:
            break
        attempted += 1
        original = validated(lease.event)
        offered = validated(original)
        try:
            outcome = publish(offered)  # No claim transaction or connection held here.
            if validated(offered) != original:
                raise ValueError("publisher altered the offered event")
            result = settle(engine, lease, outcome)
        except Exception:
            # Schedule the finite retry, then preserve the original callback/validation error.
            # BaseException / abrupt exits leave the committed lease to expire.
            try:
                settle(engine, lease, Failure.RETRY)
            except Exception:
                pass  # The original failure still matters; expiry is the recovery path.
            raise
        settled += int(result)
        stale += int(not result)
    return Report(attempted, settled, stale)
