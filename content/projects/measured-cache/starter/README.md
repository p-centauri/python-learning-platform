# Measured cache lab

Implement sample, LruCache.get_or_compute, LruCache.clear and legacy_get. Supplied contracts/init/info support the exercise. Runtime is standard library only; Python 3.13+.

## Exact timing contract

sample(work, /, *, repeats=3, clock=perf_counter_ns) validates exact integer repeats=1..7 before touching work/clock (bool rejected). Each repetition calls clock, work, clock, in that order. Clock readings are exact integers, nonnegative and nondecreasing across all readings, including between repetitions. Zero duration is valid. Return Measurement(last, elapsed_ns): the last returned reference and a tuple of raw end-minus-start integer durations, with no fabricated samples, normalization, warmup, GC toggling or output. Frozen report structure does not freeze/copy last. Propagate original clock/work errors, stop immediately and return no partial report; completed work effects are not rolled back. A work failure does not call its end clock. Repeats bound calls, not elapsed time. Clocks/work can block.

Use perf_counter_ns for wall intervals and process_time_ns for process CPU intervals; process CPU includes work of process threads and excludes ordinary sleeping time. Record clock choice in surrounding evidence. Do not compare wall and CPU values as if they measured the same quantity. This finite utility does not implement timeit calibration, distribution analysis or fair experimental ordering.

## Exact cache contract

- LruCache[T] is a single-caller, non-reentrant, per-instance cache. Exact integer capacity=1..8, checked before state creation. CacheKey has exact namespace/id ASCII [a-z][a-z0-9-]{0,31} and exact revision=1..8. All fields participate in equality/hash. Revision/namespace are caller-defined discriminators, not automatic freshness or authorization.
- get_or_compute(key, compute, /) rejects reentrant calls before any state mutation, then rejects non-exact CacheKey. On a hit, increment hits, move the key to most-recent, return the exact stored reference and do not call compute (None/False/zero are hits too).
- On a miss, increment misses before compute; set the compute guard and reset it in finally. Successful return stores the exact reference as most-recent; if over capacity, evict the least-recent key. Failed computation propagates the same exception, leaves entries/order unchanged, counts the attempted miss and permits later calls. No retries or caching failures. Do not permit get_or_compute or clear while compute is active. info is allowed and returns a fixed frozen snapshot in least-to-most-recent order.
- clear rejects reentrancy, drops cache references and resets hits/misses. Never call close on values during clear/eviction; borrowers may still own a returned reference. A cache entry is not a cleanup owner. Entry capacity does not bound value bytes, execution time, referenced object graphs or other owners' lifetimes. Values remain mutable if their type is mutable. No TTL, filesystem/content checking, thread safety or duplicate in-flight suppression is provided.

## Compatibility exercise

legacy_get(cache, key, factory, /) is a supported deprecated adapter in this educational contract; no previous public release is claimed. Emit DeprecationWarning with stacklevel=2, then delegate once to get_or_compute, preserving generic return identity, hit behavior and errors. Standard warning filters control display; if warnings become errors, delegation does not occur. Keep the old call shape usable while documenting migration. New code uses cache.get_or_compute(key, factory).

## Work and evidence

1. Complete four functions/methods and add two regressions beyond public cases. Test cold/warm paths, keys/revisions, failed/reentrant computation, clearing/eviction and old callers with warnings enabled.
2. Run finite public tests, strict types/lint and demo. Deterministic injected clocks test behavior; real clocks report observations without speed thresholds.
3. Save the demo JSON with Python/implementation/platform, workload size, cache capacity/state, variant order, raw wall/CPU samples, equivalent results and actual computation counts. Baseline has 32 computations; a fresh four-key cache has 4 misses/28 hits for this workload. Timing observations can vary. Profiler and memory instrumentation run separately from timing.
4. Inspect cumulative/self profiler cost and traced memory before/fill/clear/peak. tracemalloc observes traced Python allocation, not total RSS/native allocations. Only the standalone demo owns its fresh tracer; library import/measurement never alters it.
5. Build source archive/wheel, install the real wheel freshly, copy tests/demo outside source without PYTHONPATH/MYPYPATH and compose installed prior Row/Record/Snapshot/outcomes. Prove compatible typed callers and the observed warning location.
6. Submit actual output, artifacts, two regressions and a short interpretation through four manual criteria. The academy never executes this package or verifies reported output. Finite tests and manual judgment do not award mastery or certify performance/expertise.

## Local commands

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python -m mypy src/academy_measured_cache demo.py
.venv/bin/python -m ruff check src tests demo.py
.venv/bin/python demo.py --output measurement.json
.venv/bin/python -m build
```

Official references: [time](https://docs.python.org/3.13/library/time.html), [timeit](https://docs.python.org/3.13/library/timeit.html), [profilers](https://docs.python.org/3.13/library/profile.html), [tracemalloc](https://docs.python.org/3.13/library/tracemalloc.html), [functools](https://docs.python.org/3.13/library/functools.html), [warnings](https://docs.python.org/3.13/library/warnings.html).
