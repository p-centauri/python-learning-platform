Begin a profiling report with the workload and the exact measured scope. The installed fixture inserts 128 facts: 32 ids with four revisions each. After four actual scoped HTTP pages, it freezes the latest 32 values. The reporting workload requests eight hot ids sixteen times, then the remaining 24 ids once: 152 requested fingerprints. The fingerprint performs 128 SHA-256 rounds over canonical frozen fields as a stated synthetic CPU component. It is a teaching workload, not a security protocol or a claim about production demand.

The baseline recomputes each requested fingerprint. The candidate uses the earlier eight-entry LRU inside one call. On the hot distribution, expect 152 versus 32 computations and 120 cache hits, with identical ordered fingerprints and Snapshot values. A second distribution cycles all 32 ids twice. It exceeds capacity, so both variants compute 64 times with zero hits. This counterexample matters: a cache benefit depends on reuse distance, not just the existence of repeated keys.

The supplied report records three wall-time and three process-CPU intervals per variant, fresh cache state for every invocation and explicit variant order. It profiles baseline and candidate separately with cProfile and cumulative pstats text, then checks actual fingerprint call counts. It observes traced Python retained/peak/after-release bytes separately. If another owner already started tracemalloc, the helper refuses rather than stopping that borrowed tracer. Result equivalence and finite counts are behavioral checks. Faster timing is not a passing requirement.

State what the measurements leave out. The CPU comparison starts after service collection; it is not a whole-service throughput benchmark. Profiler and allocation instrumentation add overhead and run separately from ordinary timing. tracemalloc is not process RSS or every native allocation. Cache entries bound count, not arbitrary byte growth. Warm caches, implementation, platform, order and process-start costs can change observations. Interpret the recorded values and add your own changed distribution before proposing a production optimization.

## Guided practice

Predict the printed value, then explain which boundary this small illustration leaves unevaluated.

```python
requests = [0, 1, 0, 1, 0]
computations = len(set(requests))
print(computations)
```

## Independent practice

Implement analyse, then run the installed demo on both stated distributions. Preserve ordered outputs. Explain cProfile calls and cumulative time, Python allocation limits, fresh cache state and why the cyclic distribution gets no hits. Add a different independent workload.

## Check your work

Include actual JSON and command output. Do not invent a speedup or use a fixed millisecond threshold. Separate service collection, CPU reporting, worker ownership and instrumented observations.

Use the [Composed Python practical review project](/projects#python-practical-review). Record actual commands and outcomes, preserve the submitted version and keep credentials private.
