from dataclasses import dataclass
import re
from psycopg2.extensions import connection, ISOLATION_LEVEL_READ_COMMITTED, TRANSACTION_STATUS_IDLE


def field(value: str) -> str:
    if type(value) is not str or re.fullmatch(r"[a-z][a-z0-9-]{0,31}", value, flags=re.ASCII) is None:
        raise ValueError("invalid identity field")
    return value


@dataclass(frozen=True)
class Reading:
    namespace: str
    id: str
    revision: int
    value: int

    def __post_init__(self) -> None:
        field(self.namespace)
        field(self.id)
        if type(self.revision) is not int or not 1 <= self.revision <= 8:
            raise ValueError("invalid revision")
        if type(self.value) is not int or not 0 <= self.value <= 1000000:
            raise ValueError("invalid value")


@dataclass(frozen=True)
class BatchResult:
    observed: int
    inserted: int
    duplicates: int


class ConflictingReading(ValueError):
    """A stable identity already names another value; no replacement is permitted."""


def require_idle(conn: connection) -> None:
    if conn.closed or conn.autocommit or conn.isolation_level != ISOLATION_LEVEL_READ_COMMITTED:
        raise ValueError("an open non-autocommit READ COMMITTED connection is required")
    if conn.get_transaction_status() != TRANSACTION_STATUS_IDLE:
        raise ValueError("caller transaction must be idle")
