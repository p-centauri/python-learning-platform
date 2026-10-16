from collections.abc import Callable
from time import perf_counter_ns
from typing import TypeVar
from .contracts import Measurement

T = TypeVar("T")


def sample(
    work: Callable[[], T],
    /,
    *,
    repeats: int = 3,
    clock: Callable[[], int] = perf_counter_ns,
) -> Measurement[T]:
    """Run finite repeated work; retain raw durations and the last returned reference."""
    raise NotImplementedError("Implement explicit timing samples")
