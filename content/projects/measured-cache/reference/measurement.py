from collections.abc import Callable
from time import perf_counter_ns
from typing import TypeVar
from .contracts import Measurement, exact_integer

T = TypeVar("T")


def sample(
    work: Callable[[], T],
    /,
    *,
    repeats: int = 3,
    clock: Callable[[], int] = perf_counter_ns,
) -> Measurement[T]:
    exact_integer(repeats, 1, 7, "repeats")
    durations: list[int] = []
    previous = 0
    last: T
    for _ in range(repeats):
        start = clock()
        if type(start) is not int:
            raise TypeError("Expected exact clock integer")
        if start < previous:
            raise ValueError("Clock must be nonnegative and monotonic")
        last = work()
        end = clock()
        if type(end) is not int:
            raise TypeError("Expected exact clock integer")
        if end < start:
            raise ValueError("Clock must be monotonic")
        durations.append(end - start)
        previous = end
    return Measurement(last, tuple(durations))
