"""A factory owns partial work until it returns this cleanup handoff."""

from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass
import re
from typing import Generic, TypeVar

T = TypeVar("T")
_request: ContextVar[str | None] = ContextVar("academy_request", default=None)


@dataclass(frozen=True)
class Resource(Generic[T]):
    value: T
    close: Callable[[], None]

    def __post_init__(self) -> None:
        if not callable(self.close):
            raise TypeError("Expected a cleanup callback")


@dataclass(frozen=True)
class AsyncResource(Generic[T]):
    value: T
    aclose: Callable[[], Awaitable[None]]

    def __post_init__(self) -> None:
        if not callable(self.aclose):
            raise TypeError("Expected an async cleanup callback")


def current_request() -> str | None:
    return _request.get()


def validate_label(label: str) -> None:
    if type(label) is not str:
        raise TypeError("Expected exact text")
    if not 1 <= len(label) <= 32 or re.fullmatch(r"[a-z][a-z0-9-]{0,31}", label) is None:
        raise ValueError("Expected a bounded ASCII label")


def validate_limit(limit: int) -> None:
    if type(limit) is not int:
        raise TypeError("Expected exact integer limit")
    if not 0 <= limit <= 8:
        raise ValueError("Expected limit in 0..8")
