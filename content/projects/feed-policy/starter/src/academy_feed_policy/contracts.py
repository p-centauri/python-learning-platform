from collections.abc import Callable, Iterable
from typing import Protocol, TypedDict


class Reading(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def value(self) -> int: ...


class Report(TypedDict):
    count: int
    total: int


class Reporter(Protocol):
    def __call__(self, records: Iterable[Reading], /) -> Report: ...


Selector = Callable[[Reading], bool]


class RuleError(ValueError):
    """An invalid selector or configured source label, without raw input in its message."""
