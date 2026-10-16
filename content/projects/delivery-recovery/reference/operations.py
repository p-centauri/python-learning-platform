from sqlalchemy import Engine, text
from academy_competing_ingestion.contracts import RetryPolicy, owned_session
from academy_durable_outbox import Event
from academy_ingestion_service.contracts import field
from academy_leased_worker.contracts import integer
from academy_stream_delivery import RedisBroker
from academy_stream_delivery.envelope import decode
from .contracts import DeadJob, Pruned, copied
from .support import remove_payload, selected_entry

LIMITS = RetryPolicy(max_attempts=1, delays=(), lock_timeout_ms=250)


def inspect_dead(engine: Engine, namespace: str, /, *, limit: int = 8) -> tuple[DeadJob, ...]:
    field(namespace)
    integer(limit, 1, 64)
    with owned_session(engine, LIMITS) as session, session.begin():
        rows = session.execute(
            text("""
            SELECT j.id,j.revision,o.value,j.generation,j.reason,p.max_attempts
            FROM delivery_job j JOIN delivery_outbox o USING(namespace,id,revision)
            JOIN worker_policy p USING(namespace)
            WHERE j.namespace=:ns AND j.state='dead' AND NOT o.acknowledged
            ORDER BY j.id,j.revision LIMIT :limit
        """),
            dict(ns=namespace, limit=limit),
        ).all()
        return tuple(
            DeadJob(Event(namespace, r.id, r.revision, r.value), r.generation, r.reason, r.max_attempts)
            for r in rows
        )


def redrive(engine: Engine, job: DeadJob, /, *, approve: bool = False) -> bool:
    selected = copied(job)
    if type(approve) is not bool or approve is not True:
        raise ValueError("explicit approve=True required after diagnosing the poison cause")
    if selected.reason != "poison" or selected.generation >= selected.maximum:
        return False  # Exhaustion requires a separately designed recovery policy; never reset attempts.
    item = selected.event
    with owned_session(engine, LIMITS) as session, session.begin():
        changed = session.execute(
            text("""
            UPDATE delivery_job j SET state='ready',reason='retry',next_at=clock_timestamp()
            FROM delivery_outbox o,worker_policy p
            WHERE (o.namespace,o.id,o.revision)=(j.namespace,j.id,j.revision)
              AND p.namespace=j.namespace AND j.namespace=:ns AND j.id=:id AND j.revision=:rev
              AND j.state='dead' AND j.reason=:reason AND j.generation=:gen
              AND j.lease_until IS NULL AND NOT o.acknowledged AND o.value=:value
              AND p.max_attempts=:maximum AND j.generation<p.max_attempts
            RETURNING j.generation
        """),
            dict(
                ns=item.namespace,
                id=item.id,
                rev=item.revision,
                value=item.value,
                gen=selected.generation,
                reason=selected.reason,
                maximum=selected.maximum,
            ),
        ).first()
        return changed is not None


def prune(
    engine: Engine, broker: RedisBroker, namespace: str, id: bytes, /, *, allow_loss: bool = False
) -> Pruned:
    field(namespace)
    if type(allow_loss) is not bool or allow_loss is not True:
        raise ValueError("explicit allow_loss=True required; freeze group topology/rewinds first")
    entry = selected_entry(broker, namespace, id)
    if entry is None:
        return Pruned.MISSING
    item = decode(entry.payload, namespace)
    with owned_session(engine, LIMITS) as session, session.begin():
        # Hold local history while checking the broker. No cross-store atomic commit is claimed.
        row = session.execute(
            text("""
            SELECT i.value AS inbox_value,o.value AS outbox_value,o.acknowledged,j.state
            FROM delivery_inbox i JOIN delivery_outbox o USING(namespace,id,revision)
            JOIN delivery_job j USING(namespace,id,revision)
            WHERE i.namespace=:ns AND i.id=:id AND i.revision=:rev
            FOR SHARE OF i,o,j
        """),
            dict(ns=namespace, id=item.id, rev=item.revision),
        ).first()
        if row is None or row.inbox_value != item.value or row.outbox_value != item.value:
            return Pruned.BLOCKED
        if row.state != "done" or not row.acknowledged:
            return Pruned.BLOCKED
        return remove_payload(broker, namespace, entry)
