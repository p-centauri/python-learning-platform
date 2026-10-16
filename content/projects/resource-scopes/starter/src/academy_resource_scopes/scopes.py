"""Implement the five marked functions/methods against the README contract."""

from collections.abc import AsyncIterator, Awaitable, Callable, Iterable, Iterator
from contextlib import asynccontextmanager, contextmanager
from typing import Generic, TypeVar
from weakref import WeakValueDictionary
from .contracts import AsyncResource, Resource

T = TypeVar("T")


@contextmanager
def owned_resources(
    factories: Iterable[Callable[[], Resource[T]]], /, *, limit: int = 8
) -> Iterator[tuple[T, ...]]:
    raise NotImplementedError("Register each successful handoff in an ExitStack")
    yield ()


@asynccontextmanager
async def owned_async_resources(
    factories: Iterable[Callable[[], Awaitable[AsyncResource[T]]]], /, *, limit: int = 8
) -> AsyncIterator[tuple[T, ...]]:
    raise NotImplementedError("Await acquisition and register awaited cleanup")
    yield ()


@contextmanager
def request_scope(label: str, /) -> Iterator[None]:
    raise NotImplementedError("Set a token and restore it in finally")
    yield


class WeakRegistry(Generic[T]):
    def __init__(self) -> None:
        self._values: WeakValueDictionary[str, T] = WeakValueDictionary()

    def store(self, key: str, value: T, /) -> None:
        raise NotImplementedError("Store a weak value without owning its lifetime")

    def get(self, key: str, /) -> T | None:
        raise NotImplementedError("Read once and return a temporary strong reference")

    def __len__(self) -> int:
        return len(self._values)
