## The idea in plain language

Memory questions need precise terms. Current traced memory describes allocations still traced at a moment. Peak is the largest traced total observed since tracing began or its peak was reset. A snapshot records tracked allocation locations at capture time; comparing snapshots helps locate retained changes.

tracemalloc observes traced Python allocations, not total process resident memory or every native-library allocation. sys.getsizeof describes one object's reported size and generally excludes the objects it references. Neither number alone establishes the full cost of an application graph.

Start tracing before the allocations you want to study. In the standalone example, this script owns its fresh tracer and stops it in finally. A library must not silently stop an application's existing tracer or reset its global peak. The lab's measurement/cache runtime does not manage tracing at all; its guarded demo owns the observation.

Holding references changes the experiment. A cache, last measurement result, traceback, snapshot or local variable can keep objects or diagnostic data around. Clearing a cache drops its references but does not revoke references already returned to callers. Resource validity and object reachability are different concerns.

Separate memory instrumentation from timing to avoid confusing its overhead with normal cost. Capture before/fill/clear/peak, explain what stayed alive and report actual observations. No test requires a fixed byte count or RSS reduction. An entry capacity bounds entries, not arbitrary cached values' bytes.

## Worked example

Save this trusted example as example.py and run it locally. Keep profiling/memory instrumentation separate from benchmark timing.

```python
import tracemalloc
tracemalloc.start(1)
try:
    before = tracemalloc.take_snapshot()
    values = [bytes(4096) for _ in range(8)]
    after = tracemalloc.take_snapshot()
    changes = after.compare_to(before, "lineno")
    current, peak = tracemalloc.get_traced_memory()
    print(bool(changes), peak >= current)
    values.clear()
finally:
    tracemalloc.stop()
```

## Guided practice

Identify allocations after tracing starts and the surviving references. Explain snapshot differences versus current/peak and total RSS.

## Independent practice

Capture separate memory observations before filling and after clearing the lab cache. Explain scope ownership, retained values and omitted native/process memory.

## Check your work

State exactly what was observed. Do not assert a fixed byte threshold or stop a borrowed global tracer.

Continue to [Cache keys, versions & honest freshness](/lessons/python-cache-keys).
