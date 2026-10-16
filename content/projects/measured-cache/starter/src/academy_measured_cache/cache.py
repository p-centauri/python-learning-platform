from collections import OrderedDict
from collections.abc import Callable
from typing import Generic, TypeVar
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
        """Promote hits, count attempted misses, insert successful results and evict LRU."""
        raise NotImplementedError("Implement cache behavior")

    def clear(self) -> None:
        """Drop owned references/reset counters; never call close on cached values."""
        raise NotImplementedError("Implement explicit cache clearing")


def legacy_get(cache: LruCache[T], key: CacheKey, factory: Callable[[], T], /) -> T:
    """Supported compatibility exercise: caller-located warning then delegate."""
    raise NotImplementedError("Implement the deprecated adapter")
