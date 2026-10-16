from collections.abc import Callable
from threading import Event as StopEvent
from sqlalchemy import Engine
from academy_durable_outbox import Accepted, Event
from .contracts import Failure, Lease, Policy, Report


def claim(engine: Engine, namespace: str, policy: Policy, /) -> Lease | None:
    raise NotImplementedError("commit a bounded database lease with a new generation")


def settle(engine: Engine, lease: Lease, outcome: Accepted | Failure, /) -> bool:
    raise NotImplementedError("fence settlement and schedule retry or quarantine")


def run(
    engine: Engine,
    namespace: str,
    policy: Policy,
    publish: Callable[[Event], Accepted | Failure],
    stop: StopEvent,
    *,
    limit: int = 8,
) -> Report:
    raise NotImplementedError("bound admission and cooperate with shutdown")
