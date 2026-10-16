from dataclasses import dataclass
import re
from typing import Generic, TypeVar

T = TypeVar("T")


def exact_integer(value: int, low: int, high: int, name: str) -> None:
    if type(value) is not int:
        raise TypeError("Expected exact integer " + name)
    if not low <= value <= high:
        raise ValueError("Invalid " + name)


@dataclass(frozen=True)
class CacheKey:
    namespace: str
    id: str
    revision: int = 1

    def __post_init__(self) -> None:
        for field in (self.namespace, self.id):
            if type(field) is not str:
                raise TypeError("Expected exact key text")
            if not 1 <= len(field) <= 32 or re.fullmatch(r"[a-z][a-z0-9-]{0,31}", field) is None:
                raise ValueError("Invalid ASCII key field")
        exact_integer(self.revision, 1, 8, "revision")


@dataclass(frozen=True)
class CacheInfo:
    capacity: int
    hits: int
    misses: int
    keys: tuple[CacheKey, ...]  # Least to most recently used.

    @property
    def size(self) -> int:
        return len(self.keys)


@dataclass(frozen=True)
class Measurement(Generic[T]):
    last: T
    elapsed_ns: tuple[int, ...]
