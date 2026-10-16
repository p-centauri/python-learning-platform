"""Static interfaces and runtime value checks have separate jobs."""

from collections.abc import Callable
from dataclasses import dataclass
import re
from typing import Protocol, TypeGuard, TypedDict, TypeVar

T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)


class Valued(Protocol[T_co]):
    @property
    def value(self) -> T_co: ...


class Consumer(Protocol[T_contra]):
    def __call__(self, value: T_contra, /) -> None: ...


class RowPayload(TypedDict):
    id: str
    value: int


def is_row_payload(payload: object) -> TypeGuard[RowPayload]:
    return (
        type(payload) is dict
        and set(payload) == {"id", "value"}
        and type(payload["id"]) is str
        and type(payload["value"]) is int
    )


@dataclass(frozen=True)
class Row:
    id: str
    value: int

    def __post_init__(self) -> None:
        if type(self.id) is not str or type(self.value) is not int:
            raise TypeError("Expected exact text and integer fields")
        if not 1 <= len(self.id) <= 32 or re.fullmatch(r"[a-z][a-z0-9-]{0,31}", self.id) is None:
            raise ValueError("Expected a bounded ASCII identifier")
        if not 0 <= self.value <= 60000:
            raise ValueError("Expected 0..60000")


def require_callable(function: Callable[..., object]) -> None:
    if not callable(function):
        raise TypeError("Expected a callable")
