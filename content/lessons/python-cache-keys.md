## The idea in plain language

Caching stores a result so later equivalent requests can reuse it. First define equivalent. If output depends on a namespace, item and data revision, the key must include all three. Omitting a dependency can return another context's result or stale data even when lookup is fast.

The lab CacheKey is immutable with exact bounded text and revision fields. All fields participate in equality and hashing. Namespace/revision distinguish entries; they do not authorize a caller or automatically detect changing external data. The caller must choose a correct revision and perform permissions checks outside the cache.

Cache deterministic values with a stated lifetime. A changing file path, current time, random output or mutable external database state is not automatically safe to memoize. A copied path is not a content snapshot. TTL, invalidation and revision changes are different policies; this bounded lab implements explicit revision keys and clear, not timed expiry.

functools.lru_cache requires hashable arguments and retains references to keys/results until eviction/clearing. Different call patterns may form different entries, and typed options have subtleties. Its internal cache structure is thread-safe, but concurrent misses may still compute more than once. That is not an exactly-once side-effect guarantee.

Avoid caching generators or async coroutine objects as if they were reusable completed values. A returned mutable object is also shared with later callers unless the interface copies/freezes it. The lab deliberately preserves result identity and documents single-caller use. A hit returning None, False or zero is still a hit.

## Worked example

Save this trusted example as example.py and run it locally. Keep profiling/memory instrumentation separate from benchmark timing.

```python
from dataclasses import dataclass
from functools import lru_cache
@dataclass(frozen=True)
class Key:
    namespace: str
    item: str
    revision: int
@lru_cache(maxsize=4)
def label(key: Key) -> str:
    return f"{key.namespace}:{key.item}:{key.revision}"
a, b = Key("team-a", "x", 1), Key("team-b", "x", 1)
print(label(a), label(b))
print(label(a) == label(a))
```

## Guided practice

List every dependency in the result. Explain key equality, namespace versus authorization and why revision selection belongs to the caller.

## Independent practice

Implement exact CacheKey behavior and test namespace/revision separation, falsy hits and mutable identity. Describe a freshness policy for external data without pretending it already exists.

## Check your work

Keys include relevant dependencies. No key, entry limit or frozen path guarantees authorization, freshness or exactly-once effects.

Continue to [LRU eviction, failures & value lifetime](/lessons/python-cache-lifetime).
