## The idea in plain language

Complete four functions/methods: finite sampling, cache lookup/computation, explicit clearing and the deprecated adapter. Keep measurement, reuse and compatibility separate so evidence can explain each one.

The sampler preserves raw intervals and the last result reference. The cache owns bounded entries, returns stored identity and states its failed-miss/reentrancy policy. The adapter preserves a supported old call shape while warning before delegation. None of these count bounds imposes a hard elapsed-time or memory-byte budget.

Run the guarded demo with fresh cache state per repetition. For its stated 32-request/four-key workload, output is equal and cached computations fall from 32 to four, with 28 hits. This is a verified computation-count change, not a guarantee that every workload becomes faster. Raw wall/CPU timing values can vary; the sequential toy's variant order and limited samples stay explicit.

Profile separately, then trace Python allocations separately. The demo records environment, workload, state, order, samples, counters, profile text and before/fill/clear/peak memory. Its fresh standalone tracer has an owner and stops in finally. It does not measure total RSS, all native allocations or production tail latency.

Build source archive/wheel, install freshly and run copied tests/demo outside source without editable paths. Compose earlier installed values and preserve strict typed callers for both new and deprecated interfaces. Add two regressions and report actual output instead of fabricated timings.

Four manual criteria review comparable measurement, memory interpretation, cache failure/lifetime and compatibility/artifact evidence. The academy stores learner-reported output and judgment; it never executes this project. Full expert practice, PostgreSQL/FastAPI persistence, durable workers and applied AI remain later work.

## Worked example

Save this trusted example as example.py and run it locally. Keep profiling/memory instrumentation separate from benchmark timing.

```python
from functools import lru_cache
@lru_cache(maxsize=4)
def square(number: int) -> int:
    return number * number
values = [square(n % 4) for n in range(32)]
info = square.cache_info()
print(sum(values), info.misses, info.hits)
square.cache_clear()
print(square.cache_info().currsize)
```

## Guided practice

Identify exact counters versus variable timing/memory observations. Explain the fresh-cache toy, owner scopes and separate manual criteria.

## Independent practice

Complete the starter, add two regressions and save real measurement JSON. Install the wheel freshly, compose prior values and submit bounded evidence.

## Check your work

Finite acceptance is behavior proof for this contract; actual measurements require interpretation and never certify expertise.

[Download the measured cache starter](/api/projects/python-measured-cache/starter), then open the [project checklist](/projects#python-measured-cache) and [submission workspace](/projects/python-measured-cache/submissions).

Continue to [Relational rows & stable identities](/lessons/python-relational-keys).
