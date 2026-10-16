from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from academy_durable_outbox import Event
from academy_durable_outbox.contracts import validated


def integer(value: int, low: int, high: int) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError("expected a bounded exact integer")


@dataclass(frozen=True)
class Policy:
    lease_ms: int = 1000
    max_attempts: int = 3
    delays_ms: tuple[int, ...] = (100, 200)

    def __post_init__(self) -> None:
        integer(self.lease_ms, 100, 60000)
        integer(self.max_attempts, 1, 8)
        if type(self.delays_ms) is not tuple or len(self.delays_ms) != self.max_attempts - 1:
            raise ValueError("one tuple delay per possible retry")
        for delay in self.delays_ms:
            integer(delay, 0, 60000)


def policy_copy(policy: Policy) -> Policy:
    if type(policy) is not Policy:
        raise ValueError("expected exact Policy")
    return Policy(policy.lease_ms, policy.max_attempts, policy.delays_ms)


@dataclass(frozen=True)
class Lease:
    event: Event
    generation: int
    deadline: datetime

    def __post_init__(self) -> None:
        validated(self.event)
        integer(self.generation, 1, 8)
        if type(self.deadline) is not datetime or self.deadline.utcoffset() is None:
            raise ValueError("expected an aware database deadline")


def lease_copy(lease: Lease) -> Lease:
    if type(lease) is not Lease:
        raise ValueError("expected exact Lease")
    copied = Lease(validated(lease.event), lease.generation, lease.deadline)
    return Lease(copied.event, copied.generation, copied.deadline.astimezone(timezone.utc))


class Failure(Enum):
    RETRY = "retry"
    POISON = "poison"


@dataclass(frozen=True)
class Report:
    attempted: int
    settled: int
    stale: int
