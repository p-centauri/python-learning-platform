"""Finite synchronous contracts; no network, async completion or API execution."""

from collections.abc import Callable, Iterable, Sequence
from functools import wraps
from typing import ParamSpec, TypeVar, overload

from .contracts import Row, is_row_payload, require_callable

T = TypeVar("T")
U = TypeVar("U")
P = ParamSpec("P")
R = TypeVar("R")


def map_rows(rows: Iterable[T], mapper: Callable[[T], U], /, *, limit: int = 64) -> tuple[U, ...]:
    if type(limit) is not int:
        raise TypeError("Expected an integer limit")
    if not 0 <= limit <= 64:
        raise ValueError("Expected a limit in 0..64")
    require_callable(mapper)
    saved: list[U] = []
    for row in rows:
        if len(saved) == limit:
            raise ValueError("Too many rows")
        saved.append(mapper(row))
    return tuple(saved)


def watch_call(function: Callable[P, R], /, *, observer: Callable[[str], None]) -> Callable[P, R]:
    require_callable(function)
    require_callable(observer)

    @wraps(function)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        observer("started")
        try:
            result = function(*args, **kwargs)
        except BaseException:
            observer("raised")
            raise
        observer("returned")
        return result

    return wrapped


@overload
def first(rows: Sequence[T], /) -> T | None: ...
@overload
def first(rows: Sequence[T], /, *, default: U) -> T | U: ...
def first(rows: Sequence[T], /, *, default: U | None = None) -> T | U | None:
    return default if len(rows) == 0 else rows[0]


def decode_row(payload: object) -> Row:
    if not is_row_payload(payload):
        raise TypeError("Expected exactly text id and integer value")
    return Row(payload["id"], payload["value"])
