from collections.abc import Callable, Sequence
from sqlalchemy import Engine, select, text
from sqlalchemy.dialects.postgresql import insert
from academy_ingestion_service import Datum, Receipt
from academy_ingestion_service.contracts import ConflictingDatum, field
from academy_ingestion_service.models import RecordRow, SourceRow
from academy_competing_ingestion.contracts import RetryPolicy, owned_session, require_engine, snapshot
from .contracts import Accepted, ConflictingEvent, Event, Recorded, validated

LIMITS = RetryPolicy(max_attempts=1, delays=())


def record(engine: Engine, namespace: str, rows: Sequence[Datum], /) -> Recorded:
    batch = snapshot(namespace, rows)
    require_engine(engine)
    if not batch:
        return Recorded(Receipt(0, 0, 0), 0)
    inserted = duplicates = enqueued = 0
    with owned_session(engine, LIMITS) as session, session.begin():
        session.execute(insert(SourceRow).values(namespace=namespace).on_conflict_do_nothing())
        for row in batch:
            params = {"namespace": namespace, "id": row.id, "revision": row.revision, "value": row.value}
            value = session.execute(
                insert(RecordRow).values(**params).on_conflict_do_nothing().returning(RecordRow.value)
            ).scalar_one_or_none()
            if value is not None:
                inserted += 1
            else:
                stored = session.execute(
                    select(RecordRow.value)
                    .where(
                        RecordRow.namespace == namespace,
                        RecordRow.id == row.id,
                        RecordRow.revision == row.revision,
                    )
                    .with_for_update(read=True)
                ).scalar_one_or_none()
                if stored != row.value:
                    raise ConflictingDatum()
                duplicates += 1
            queued = session.execute(
                text("""
                INSERT INTO delivery_outbox(namespace,id,revision,value)
                VALUES (:namespace,:id,:revision,:value)
                ON CONFLICT (namespace,id,revision) DO NOTHING RETURNING value
            """),
                params,
            ).scalar_one_or_none()
            if queued is not None:
                enqueued += 1
            else:
                stored_event = session.execute(
                    text("""
                    SELECT value FROM delivery_outbox
                    WHERE namespace=:namespace AND id=:id AND revision=:revision FOR SHARE
                """),
                    params,
                ).scalar_one_or_none()
                if stored_event != row.value:
                    raise ConflictingEvent()
    return Recorded(Receipt(len(batch), inserted, duplicates), enqueued)


def consume(engine: Engine, event: Event, /) -> Accepted:
    item = validated(event)
    with owned_session(engine, LIMITS) as session, session.begin():
        params = {"namespace": item.namespace, "id": item.id, "revision": item.revision, "value": item.value}
        inserted = session.execute(
            text("""
            INSERT INTO delivery_inbox(namespace,id,revision,value)
            VALUES (:namespace,:id,:revision,:value)
            ON CONFLICT (namespace,id,revision) DO NOTHING RETURNING value
        """),
            params,
        ).scalar_one_or_none()
        if inserted is not None:
            session.execute(
                text("""
                INSERT INTO delivery_effect(namespace,total,applied) VALUES (:namespace,:value,1)
                ON CONFLICT (namespace) DO UPDATE
                SET total=delivery_effect.total+EXCLUDED.total, applied=delivery_effect.applied+1
            """),
                params,
            )
        else:
            stored = session.execute(
                text("""
                SELECT value FROM delivery_inbox
                WHERE namespace=:namespace AND id=:id AND revision=:revision FOR SHARE
            """),
                params,
            ).scalar_one_or_none()
            if stored != item.value:
                raise ConflictingEvent()
    return Accepted(item)


def publish_one(engine: Engine, namespace: str, publish: Callable[[Event], Accepted], /) -> Event | None:
    field(namespace)
    if not callable(publish):
        raise ValueError("publisher must be callable")
    item = None
    with owned_session(engine, LIMITS) as session, session.begin():
        row = session.execute(
            text("""
            SELECT namespace,id,revision,value FROM delivery_outbox
            WHERE namespace=:namespace AND NOT acknowledged
            ORDER BY id,revision FOR UPDATE SKIP LOCKED LIMIT 1
        """),
            {"namespace": namespace},
        ).one_or_none()
        if row is not None:
            expected = Event(row.namespace, row.id, row.revision, row.value)
            item = validated(expected)
            confirmation = publish(item)
            if (
                type(confirmation) is not Accepted
                or validated(confirmation.event) != expected
                or validated(item) != expected
            ):
                raise ValueError("publisher must confirm the exact event after durable acceptance")
            session.execute(
                text("""
                UPDATE delivery_outbox SET acknowledged=true
                WHERE namespace=:namespace AND id=:id AND revision=:revision
            """),
                {"namespace": expected.namespace, "id": expected.id, "revision": expected.revision},
            )
            item = expected
    return item
