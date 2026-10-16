from collections.abc import Callable, Sequence
from sqlalchemy import Engine
from academy_ingestion_service import Datum
from .contracts import Accepted, Event, Recorded


def record(engine: Engine, namespace: str, rows: Sequence[Datum], /) -> Recorded:
    """Commit source facts and stable event intents together; adopt matching prior facts."""
    raise NotImplementedError("implement atomic recording")


def consume(engine: Engine, event: Event, /) -> Accepted:
    """Commit inbox identity and one database effect together; validate duplicate values."""
    raise NotImplementedError("implement duplicate-safe consumption")


def publish_one(engine: Engine, namespace: str, publish: Callable[[Event], Accepted], /) -> Event | None:
    """Own one pending row lock until exact durable acceptance and committed acknowledgment."""
    raise NotImplementedError("implement claim/publish/ack")
