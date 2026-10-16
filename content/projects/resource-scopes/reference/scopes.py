"""Trusted reference; cooperative resources and explicit ownership."""

from collections.abc import AsyncIterator, Awaitable, Callable, Iterable, Iterator
from contextlib import AsyncExitStack, ExitStack, asynccontextmanager, contextmanager
from typing import Generic, TypeVar
from weakref import WeakValueDictionary
from .contracts import AsyncResource, Resource, _request, validate_label, validate_limit

T = TypeVar("T")


@contextmanager
def owned_resources(
    factories: Iterable[Callable[[], Resource[T]]], /, *, limit: int = 8
) -> Iterator[tuple[T, ...]]:
    validate_limit(limit)
    with ExitStack() as stack:
        values: list[T] = []
        for factory in factories:
            if len(values) == limit:
                raise ValueError("Too many resources")
            if not callable(factory):
                raise TypeError("Expected a resource factory")
            resource = factory()
            if type(resource) is not Resource:
                raise TypeError("Expected a Resource handoff")
            stack.callback(resource.close)
            values.append(resource.value)
        yield tuple(values)


@asynccontextmanager
async def owned_async_resources(
    factories: Iterable[Callable[[], Awaitable[AsyncResource[T]]]], /, *, limit: int = 8
) -> AsyncIterator[tuple[T, ...]]:
    validate_limit(limit)
    async with AsyncExitStack() as stack:
        values: list[T] = []
        for factory in factories:
            if len(values) == limit:
                raise ValueError("Too many resources")
            if not callable(factory):
                raise TypeError("Expected an async resource factory")
            resource = await factory()
            if type(resource) is not AsyncResource:
                raise TypeError("Expected an AsyncResource handoff")
            stack.push_async_callback(resource.aclose)
            values.append(resource.value)
        yield tuple(values)


@contextmanager
def request_scope(label: str, /) -> Iterator[None]:
    validate_label(label)
    token = _request.set(label)
    try:
        yield
    finally:
        _request.reset(token)


class WeakRegistry(Generic[T]):
    """Non-owning lookup; no cleanup or retention guarantee."""

    def __init__(self) -> None:
        self._values: WeakValueDictionary[str, T] = WeakValueDictionary()

    def store(self, key: str, value: T, /) -> None:
        validate_label(key)
        self._values[key] = value

    def get(self, key: str, /) -> T | None:
        validate_label(key)
        return self._values.get(key)

    def __len__(self) -> int:
        return len(self._values)
