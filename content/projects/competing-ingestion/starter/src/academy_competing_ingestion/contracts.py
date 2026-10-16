from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
import math
from sqlalchemy import Connection, Engine, event, text
from sqlalchemy.orm import Session, SessionTransaction
from academy_ingestion_service import Datum, Receipt
from academy_ingestion_service.contracts import ConflictingDatum, field


class Decision(StrEnum):
    RETRY = "retry-full-transaction"
    STOP = "stop"
    RECONCILE = "reconcile"


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    lock_timeout_ms: int = 2000
    statement_timeout_ms: int = 5000
    delays: tuple[float, ...] = (0.0, 0.0)

    def __post_init__(self) -> None:
        if type(self.max_attempts) is not int or not 1 <= self.max_attempts <= 3:
            raise ValueError("attempt count must be an exact int in 1..3")
        if type(self.lock_timeout_ms) is not int or not 50 <= self.lock_timeout_ms <= 2000:
            raise ValueError("lock wait must be an exact int in 50..2000 milliseconds")
        if (
            type(self.statement_timeout_ms) is not int
            or not self.lock_timeout_ms < self.statement_timeout_ms <= 5000
        ):
            raise ValueError("statement limit must exceed lock wait and be at most 5000 milliseconds")
        if type(self.delays) is not tuple or len(self.delays) != self.max_attempts - 1:
            raise ValueError("supply one exact tuple delay per possible retry")
        if any(type(d) is not float or not math.isfinite(d) or not 0.0 <= d <= 1.0 for d in self.delays):
            raise ValueError("delays must be finite exact floats in 0..1 seconds")


@dataclass(frozen=True)
class Delivery:
    receipt: Receipt
    attempts: int


@dataclass(frozen=True)
class Reconciliation:
    matched_keys: int
    missing: tuple[Datum, ...]
    conflicts: tuple[Datum, ...]

    @property
    def state(self) -> str:
        return "conflict" if self.conflicts else "missing" if self.missing else "complete"


class RetryExhausted(Exception):
    def __init__(self, attempts: int, sqlstate: str) -> None:
        self.attempts, self.sqlstate = attempts, sqlstate
        super().__init__("bounded transaction attempts exhausted")


class UnknownOutcome(Exception):
    def __init__(self, attempts: int) -> None:
        self.attempts = attempts
        super().__init__("delivery outcome requires reconciliation")


def snapshot(namespace: str, rows: Sequence[Datum]) -> tuple[Datum, ...]:
    field(namespace)
    if type(rows) not in (list, tuple) or len(rows) > 64:
        raise ValueError("expected at most 64 rows in an exact list or tuple")
    values: dict[tuple[str, int], int] = {}
    for row in rows:
        if type(row) is not Datum:
            raise ValueError("expected exact Datum")
        Datum(row.id, row.revision, row.value)
        key = row.id, row.revision
        if key in values and values[key] != row.value:
            raise ConflictingDatum()
        values[key] = row.value
    return tuple(Datum(row.id, row.revision, row.value) for row in rows)


def require_engine(engine: Engine) -> None:
    if engine.dialect.name != "postgresql" or engine.dialect.driver != "psycopg2":
        raise ValueError("PostgreSQL through Psycopg 2 required")


def owned_session(engine: Engine, policy: RetryPolicy) -> Session:
    require_engine(engine)
    if type(policy) is not RetryPolicy:
        raise ValueError("expected exact RetryPolicy")
    # Revalidate even if frozen state was bypassed by a caller.
    RetryPolicy(policy.max_attempts, policy.lock_timeout_ms, policy.statement_timeout_ms, policy.delays)
    session = Session(engine)

    def limits(session: Session, transaction: SessionTransaction, connection: Connection) -> None:
        if connection.get_isolation_level() != "READ COMMITTED":
            raise ValueError("delivery/reconciliation requires READ COMMITTED")
        connection.execute(
            text(
                "SELECT set_config('lock_timeout', :lock_wait, true), set_config('statement_timeout', :statement_wait, true)"
            ),
            {"lock_wait": str(policy.lock_timeout_ms), "statement_wait": str(policy.statement_timeout_ms)},
        )

    event.listen(session, "after_begin", limits)
    return session
