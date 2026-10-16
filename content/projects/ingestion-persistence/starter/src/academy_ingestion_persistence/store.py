from collections.abc import Iterable
from psycopg2.extensions import connection
from .contracts import BatchResult, Reading


def snapshot_batch(source: Iterable[Reading], /) -> tuple[Reading, ...]:
    """Observe at most 65 items; accept at most 64 exact validated Readings, without closing input."""
    raise NotImplementedError("implement bounded validation before database access")


def persist_batch(conn: connection, source: Iterable[Reading], /) -> BatchResult:
    """Borrow an idle configured connection, own a transaction, preserve immutable key/value identity."""
    raise NotImplementedError("implement parameter binding, duplicate checks, commit and rollback")


def load_namespace(conn: connection, namespace: str, /) -> tuple[Reading, ...]:
    """Own a read transaction; return at most 64 records ordered by id/revision, or fail on overflow."""
    raise NotImplementedError("implement bounded parameterized read with explicit transaction ownership")
