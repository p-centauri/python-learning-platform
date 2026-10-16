from collections.abc import Sequence
from sqlalchemy import Engine, select, tuple_
from academy_ingestion_service import Datum
from academy_ingestion_service.models import RecordRow
from .contracts import Reconciliation, RetryPolicy, owned_session, snapshot


def reconcile(
    engine: Engine, namespace: str, rows: Sequence[Datum], /, *, policy: RetryPolicy = RetryPolicy()
) -> Reconciliation:
    batch = snapshot(namespace, rows)
    unique = {(row.id, row.revision): row for row in batch}
    with owned_session(engine, policy) as session:
        if not unique:
            return Reconciliation(0, (), ())
        with session.begin():
            stored = session.execute(
                select(RecordRow.id, RecordRow.revision, RecordRow.value).where(
                    RecordRow.namespace == namespace,
                    tuple_(RecordRow.id, RecordRow.revision).in_(tuple(unique)),
                )
            ).all()
            values = {(row.id, row.revision): row.value for row in stored}
            missing = tuple(row for key, row in unique.items() if key not in values)
            conflicts = tuple(
                row for key, row in unique.items() if key in values and values[key] != row.value
            )
            matched = sum(key in values and values[key] == row.value for key, row in unique.items())
    return Reconciliation(matched, missing, conflicts)
