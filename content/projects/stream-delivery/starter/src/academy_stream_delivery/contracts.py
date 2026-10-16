from collections.abc import Callable
from dataclasses import dataclass
import re
from typing import Protocol
from academy_durable_outbox import Accepted, Event
from academy_durable_outbox.contracts import validated
from academy_ingestion_service.contracts import field


class InvalidEnvelope(ValueError):
    pass


class UnconfirmedAppend(RuntimeError):
    pass


def stream(namespace: str) -> str:
    field(namespace)
    return "academy:events:" + namespace


def entry_id(value: bytes) -> None:
    if type(value) is not bytes or not re.fullmatch(rb"[0-9]{1,20}-[0-9]{1,20}", value):
        raise ValueError("invalid exact stream id")


@dataclass(frozen=True)
class Entry:
    id: bytes
    payload: bytes

    def __post_init__(self) -> None:
        entry_id(self.id)
        if type(self.payload) is not bytes or not 1 <= len(self.payload) <= 1024:
            raise InvalidEnvelope("expected 1..1024 exact bytes")


@dataclass(frozen=True)
class Batch:
    entry: Entry | None
    cursor: bytes = b"0-0"
    deleted: tuple[bytes, ...] = ()


@dataclass(frozen=True)
class Result:
    event: Event | None
    entry_id: bytes | None
    acknowledged: bool
    cursor: bytes
    deleted: tuple[bytes, ...]


class Broker(Protocol):
    def append(self, namespace: str, payload: bytes) -> bytes: ...
    def take(
        self, namespace: str, group: str, consumer: str, *, recover: bool, idle_ms: int, cursor: bytes
    ) -> Batch: ...
    def ack(self, namespace: str, group: str, id: bytes) -> bool: ...


def publisher(broker: Broker, *, version: int = 2) -> Callable[[Event], Accepted]:
    from .envelope import encode

    if type(version) is not int or version not in (1, 2):
        raise ValueError("supported envelope versions are 1 and 2")

    def publish(event: Event) -> Accepted:
        expected = validated(event)
        id = broker.append(expected.namespace, encode(expected, version=version))
        entry_id(id)
        return Accepted(expected)  # Broker's stated AOF boundary, not a consumer effect.

    return publish
