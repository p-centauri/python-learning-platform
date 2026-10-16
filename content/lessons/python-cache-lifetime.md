## The idea in plain language

Least recently used eviction removes the entry that has gone longest without successful access. A hit promotes its key to most-recent. A new successful miss enters as most-recent; exceeding capacity evicts the oldest entry. A completed computation is not a reason to silently change result order or identity.

The lab counts hits and attempted misses. On a failed miss, the miss count rises but existing entries/order stay unchanged. No failure is cached or retried automatically. A later request may try again. This is an explicit contract, not a universal cache convention.

Callbacks can surprise an implementation by reentering it. The lab rejects get_or_compute and clear while a miss computation is active, before extra state mutation. Its guard resets in finally, so a failed callback does not permanently block the cache. info may observe a fixed snapshot. This guard handles cooperative reentrancy; it is not thread synchronization or tamper resistance.

clear drops cache references and resets counters. It never calls close on values. The cache may be one owner of a Python object reference, while a caller owns a returned reference and an external scope owns resource cleanup. Eviction does not make a borrowed value disappear or keep a closed file usable.

Entry capacity bounds the number of stored keys/results. Each value can reference a large graph, and active calls/input/results have their own memory. There is no TTL or elapsed-time budget. Keep caches scoped to a useful owner and verify growth and failure behavior before relying on them.

## Worked example

Save this trusted example as example.py and run it locally. Keep profiling/memory instrumentation separate from benchmark timing.

```python
from collections import OrderedDict
cache: OrderedDict[str, int] = OrderedDict([("a", 1), ("b", 2)])
cache.move_to_end("a")
cache["c"] = 3
cache.popitem(last=False)
print(list(cache))
held = cache["a"]
cache.clear()
print(len(cache), held)
```

## Guided practice

Trace least-to-most-recent order, a hit and an eviction. Explain why clear leaves held intact and why failed computations need a documented counter policy.

## Independent practice

Implement get_or_compute and clear. Test hit promotion, bounds, failed/reentrant calls, guard restoration, snapshot info and no implicit cleanup.

## Check your work

No retry, implicit close or thread-safety promise. Count limits and owned references have precise scopes.

Continue to [Compatible interfaces & useful deprecation](/lessons/python-library-evolution).
