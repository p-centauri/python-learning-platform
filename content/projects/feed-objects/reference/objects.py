"""Small object contracts, not a generic ORM or a security boundary."""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from types import NotImplementedType
from typing import overload
import re


class BoundedInt:
    """A data descriptor for Budget fields: exact ints in 0..64 inclusive."""

    def __init__(self) -> None:
        self._binding: tuple[type[Budget], str] | None = None

    def __set_name__(self, owner: type[Budget], name: str) -> None:
        if self._binding is not None and self._binding != (owner, name):
            raise ValueError("Use a separate descriptor for each field")
        self._binding = (owner, name)

    def _name(self) -> str:
        if self._binding is None:
            raise RuntimeError("Descriptor is not bound")
        return self._binding[1]

    @overload
    def __get__(self, instance: None, owner: type[Budget] | None = None) -> BoundedInt: ...
    @overload
    def __get__(self, instance: Budget, owner: type[Budget] | None = None) -> int: ...
    def __get__(self, instance: Budget | None, owner: type[Budget] | None = None) -> BoundedInt | int:
        if instance is None:
            return self
        name = self._name()
        try:
            return instance._values[name]
        except KeyError:
            raise AttributeError(name) from None

    def __set__(self, instance: Budget, value: int) -> None:
        if type(value) is not int:
            raise TypeError("Expected an integer")
        if not 0 <= value <= 64:
            raise ValueError("Expected 0..64")
        instance._values[self._name()] = value


class Budget:
    limit = BoundedInt()
    reserve = BoundedInt()

    def __init__(self, limit: int, reserve: int = 0) -> None:
        self._values: dict[str, int] = {}
        self.limit = limit
        self.reserve = reserve


@dataclass(frozen=True, eq=False)
class FeedKey:
    """Two bounded ASCII identity fields. Subclasses must review equality afresh."""
    namespace: str
    name: str

    def __post_init__(self) -> None:
        for value in (self.namespace, self.name):
            if type(value) is not str:
                raise TypeError("Expected text")
            if not 1 <= len(value) <= 32 or re.fullmatch(r"[a-z][a-z0-9-]{0,31}", value) is None:
                raise ValueError("Expected a bounded ASCII identifier")

    def __eq__(self, other: object) -> bool | NotImplementedType:
        if not isinstance(other, FeedKey) or type(other) is not type(self):
            return NotImplemented
        return (self.namespace, self.name) == (other.namespace, other.name)

    def __hash__(self) -> int:
        return hash((self.namespace, self.name))


@dataclass(frozen=True)
class Reading:
    key: FeedKey
    value: int

    def __post_init__(self) -> None:
        if type(self.key) is not FeedKey or type(self.value) is not int:
            raise TypeError("Expected a FeedKey and an integer")
        if not 0 <= self.value <= 60000:
            raise ValueError("Expected 0..60000")


@dataclass(frozen=True, init=False)
class Snapshot(Sequence[Reading]):
    """Immutable, ordered, at most 64 distinct keys; borrows its input iterator."""
    _rows: tuple[Reading, ...]

    def __init__(self, rows: Iterable[Reading]) -> None:
        saved: list[Reading] = []
        keys: set[FeedKey] = set()
        for row in rows:
            if len(saved) == 64:
                raise ValueError("Too many readings")
            if type(row) is not Reading:
                raise TypeError("Expected a Reading")
            if row.key in keys:
                raise ValueError("Duplicate key")
            keys.add(row.key)
            saved.append(row)
        object.__setattr__(self, "_rows", tuple(saved))

    def __len__(self) -> int:
        return len(self._rows)

    @overload
    def __getitem__(self, index: int) -> Reading: ...
    @overload
    def __getitem__(self, index: slice) -> tuple[Reading, ...]: ...
    def __getitem__(self, index: int | slice) -> Reading | tuple[Reading, ...]:
        return self._rows[index]
