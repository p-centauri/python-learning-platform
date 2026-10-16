from sqlalchemy import Engine, text
from academy_ingestion_service.contracts import field
from .contracts import Filter, Match, Revision, Summary, copied, limit as valid_limit, scoped
from .support import read, resource


def summarize(engine: Engine, namespace: str, /) -> Summary | None:
    scoped(namespace)
    with read(engine) as connection:
        row = connection.execute(text(resource("summary.sql")), {"namespace": namespace}).one_or_none()
    return None if row is None else Summary(row.namespace, row.records, row.total, row.noted_records)


def history(engine: Engine, namespace: str, id: str, /, *, limit: int = 8) -> tuple[Revision, ...]:
    scoped(namespace)
    field(id)
    valid_limit(limit, 8)
    with read(engine) as connection:
        rows = connection.execute(text(resource("history.sql")), {"namespace": namespace, "id": id, "limit": limit}).all()
    return tuple(Revision(row.revision, row.value, row.previous, row.delta, row.running_total, row.latest) for row in rows)


def search(engine: Engine, namespace: str, filter: Filter, /, *, limit: int = 16) -> tuple[Match, ...]:
    scoped(namespace)
    configured = copied(filter)
    valid_limit(limit)
    with read(engine) as connection:
        rows = connection.execute(text(resource("search.sql")), {"namespace": namespace, "filter": configured.encoded, "limit": limit}).all()
    return tuple(Match(row.id, row.revision, row.value) for row in rows)
