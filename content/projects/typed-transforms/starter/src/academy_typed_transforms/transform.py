"""Finite synchronous contracts; no network, async completion or API execution."""

from collections.abc import Callable, Iterable, Sequence
from typing import ParamSpec, TypeVar, overload

from .contracts import Row

T = TypeVar("T")
U = TypeVar("U")
P = ParamSpec("P")
R = TypeVar("R")


def map_rows(rows: Iterable[T], mapper: Callable[[T], U], /, *, limit: int = 64) -> tuple[U, ...]:
    raise NotImplementedError("Implement map_rows using README.md")


def watch_call(function: Callable[P, R], /, *, observer: Callable[[str], None]) -> Callable[P, R]:
    raise NotImplementedError("Implement watch_call using README.md")


@overload
def first(rows: Sequence[T], /) -> T | None: ...
@overload
def first(rows: Sequence[T], /, *, default: U) -> T | U: ...
def first(rows: Sequence[T], /, *, default: U | None = None) -> T | U | None:
    raise NotImplementedError("Implement first using README.md")


def decode_row(payload: object) -> Row:
    raise NotImplementedError("Implement decode_row using README.md")
