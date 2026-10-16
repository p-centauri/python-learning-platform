from collections.abc import Sequence
from sqlalchemy import and_, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from .contracts import ConflictingDatum, Cursor, Datum, Page, Receipt, field
from .models import RecordRow, SourceRow


def ingest(session: Session, namespace: str, rows: Sequence[Datum], /) -> Receipt:
    field(namespace)
    if type(rows) not in (tuple, list) or len(rows) > 64:
        raise ValueError("expected at most 64 readings in a list or tuple")
    batch = tuple(rows)
    for row in batch:
        if type(row) is not Datum:
            raise ValueError("expected exact Datum")
        Datum(row.id, row.revision, row.value)
    if session.in_transaction():
        raise ValueError("caller session must be idle")
    inserted = 0
    duplicates = 0
    with session.begin():
        if batch:
            session.execute(
                insert(SourceRow)
                .values(namespace=namespace)
                .on_conflict_do_nothing(index_elements=[SourceRow.namespace])
            )
        for row in batch:
            value = session.execute(
                insert(RecordRow)
                .values(namespace=namespace, id=row.id, revision=row.revision, value=row.value)
                .on_conflict_do_nothing(
                    index_elements=[RecordRow.namespace, RecordRow.id, RecordRow.revision]
                )
                .returning(RecordRow.value)
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
                if stored is None or stored != row.value:
                    raise ConflictingDatum()
                duplicates += 1
    return Receipt(len(batch), inserted, duplicates)


def read_page(session: Session, namespace: str, /, *, limit: int = 16, after: Cursor | None = None) -> Page:
    field(namespace)
    if type(limit) is not int or not 1 <= limit <= 32:
        raise ValueError("limit must be an exact int in 1..32")
    if after is not None:
        if type(after) is not Cursor:
            raise ValueError("expected Cursor")
        Cursor(after.id, after.revision)
    if session.in_transaction():
        raise ValueError("caller session must be idle")
    statement = select(RecordRow).where(RecordRow.namespace == namespace)
    if after is not None:
        statement = statement.where(
            or_(RecordRow.id > after.id, and_(RecordRow.id == after.id, RecordRow.revision > after.revision))
        )
    statement = statement.order_by(RecordRow.id, RecordRow.revision).limit(limit + 1)
    with session.begin():
        observed = session.scalars(statement).all()
        items = tuple(Datum(row.id, row.revision, row.value) for row in observed[:limit])
        cursor = Cursor(items[-1].id, items[-1].revision) if len(observed) > limit else None
    return Page(items, cursor)
