from collections.abc import Callable, Iterable
from concurrent.futures import Executor
from typing import Literal, TypeVar
from .contracts import Job, Outcome

T = TypeVar("T")
R = TypeVar("R")

def collect_ordered(
    executor: Executor, rows: Iterable[T], function: Callable[[T], R], /, *,
    pending: int = 2, limit: int = 16,
) -> tuple[R, ...]:
    """Borrow inputs/pool; bound submitted-but-not-retired work; retain input order."""
    raise NotImplementedError("Implement the bounded collector")

def read_job(job: Job) -> Outcome:
    """Top-level worker opens, bounds, parses and closes its own trusted local file."""
    raise NotImplementedError("Implement worker-owned reading")

def run_batch(
    jobs: Iterable[Job], /, *, mode: Literal["thread", "process"] = "thread",
    workers: int = 2, pending: int = 2, limit: int = 16,
) -> tuple[Outcome, ...]:
    """Own a dedicated pool, use explicit spawn for processes, join before returning."""
    raise NotImplementedError("Implement the owner")
