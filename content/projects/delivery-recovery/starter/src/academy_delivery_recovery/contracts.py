from dataclasses import dataclass
from enum import StrEnum
from academy_durable_outbox import Event
from academy_durable_outbox.contracts import validated
from academy_leased_worker.contracts import integer


@dataclass(frozen=True)
class DeadJob:
    event: Event
    generation: int
    reason: str
    maximum: int

    def __post_init__(self) -> None:
        validated(self.event)
        integer(self.generation, 1, 8)
        integer(self.maximum, 1, 8)
        if type(self.reason) is not str or self.reason not in ("poison", "exhausted"):
            raise ValueError("expected a stored terminal reason")
        if self.generation > self.maximum:
            raise ValueError("generation cannot exceed the saved budget")


def copied(job: DeadJob) -> DeadJob:
    if type(job) is not DeadJob:
        raise ValueError("expected an exact inspected DeadJob")
    return DeadJob(validated(job.event), job.generation, job.reason, job.maximum)


class Pruned(StrEnum):
    REMOVED = "removed"
    MISSING = "missing"
    BLOCKED = "blocked"
