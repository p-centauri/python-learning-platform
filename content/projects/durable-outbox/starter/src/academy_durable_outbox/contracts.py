from dataclasses import dataclass
from academy_ingestion_service import Datum, Receipt
from academy_ingestion_service.contracts import field


@dataclass(frozen=True)
class Event:
    namespace: str
    id: str
    revision: int
    value: int

    def __post_init__(self) -> None:
        field(self.namespace)
        Datum(self.id, self.revision, self.value)

    @property
    def key(self) -> tuple[str, str, int]:
        return self.namespace, self.id, self.revision


@dataclass(frozen=True)
class Accepted:
    event: Event

    def __post_init__(self) -> None:
        if type(self.event) is not Event:
            raise ValueError("expected exact Event")
        Event(self.event.namespace, self.event.id, self.event.revision, self.event.value)


@dataclass(frozen=True)
class Recorded:
    receipt: Receipt
    enqueued: int


class ConflictingEvent(Exception):
    pass


def validated(event: Event) -> Event:
    if type(event) is not Event:
        raise ValueError("expected exact Event")
    return Event(event.namespace, event.id, event.revision, event.value)
