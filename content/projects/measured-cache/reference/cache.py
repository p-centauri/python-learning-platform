from collections import OrderedDict
from collections.abc import Callable
from typing import Generic, TypeVar
import warnings
from .contracts import CacheInfo, CacheKey, exact_integer

T = TypeVar("T")


class LruCache(Generic[T]):
    """Single-caller cache; count bounds are not byte/deadline/freshness guarantees."""

    def __init__(self, capacity: int = 4) -> None:
        exact_integer(capacity, 1, 8, "capacity")
        self._capacity = capacity
        self._items: OrderedDict[CacheKey, T] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._computing = False

    def info(self) -> CacheInfo:
        return CacheInfo(self._capacity, self._hits, self._misses, tuple(self._items))

    def get_or_compute(self, key: CacheKey, compute: Callable[[], T], /) -> T:
        if self._computing:
            raise RuntimeError("Reentrant cache access is unsupported")
        if type(key) is not CacheKey:
            raise TypeError("Expected CacheKey")
        if key in self._items:
            self._hits += 1
            self._items.move_to_end(key)
            return self._items[key]
        self._misses += 1
        self._computing = True
        try:
            value = compute()
        finally:
            self._computing = False
        self._items[key] = value
        if len(self._items) > self._capacity:
            self._items.popitem(last=False)
        return value

    def clear(self) -> None:
        if self._computing:
            raise RuntimeError("Reentrant cache clearing is unsupported")
        self._items.clear()
        self._hits = self._misses = 0


def legacy_get(cache: LruCache[T], key: CacheKey, factory: Callable[[], T], /) -> T:
    warnings.warn("legacy_get is deprecated; use cache.get_or_compute", DeprecationWarning, stacklevel=2)
    return cache.get_or_compute(key, factory)
