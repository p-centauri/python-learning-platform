## The idea in plain language

Measure how work grows with input, not just one small run. Looking up each query by scanning every value can perform up to values times queries comparisons. A set adds setup/storage cost but usually reduces repeated membership work. Hash behavior and the objects' equality/hash costs matter; average lookup behavior is not a universal worst-case guarantee.

Count observable operations as well as time. The example deliberately counts list comparisons and set probes for the same immutable integers. It shows why an alternative is plausible, while setup and hashing costs mean it does not establish a speedup by itself.

Test several meaningful input sizes, missing/present keys and output equivalence. A prebuilt set is fair only if the intended application also reuses it; otherwise include construction. Retaining the set is a memory tradeoff, so state who owns it and how long it lives.

Streaming can reduce retained input, but a final tuple of all results still retains those results. Materializing a generator does not keep its earlier memory benefit. Count bounds limit items, not the sizes of each item or the referenced object graph.

Prefer one well-supported change over clever syntax. Preserve failure and ordering contracts. The lab keeps raw timing and computation counts separate, bounds cache entries and uses small trusted workloads. Real service/database cost needs its own later evidence.

## Worked example

Save this trusted example as example.py and run it locally. Keep profiling/memory instrumentation separate from benchmark timing.

```python
values = tuple(range(8))
queries = (0, 7, 9)
comparisons = 0
linear: list[bool] = []
for query in queries:
    found = False
    for value in values:
        comparisons += 1
        if value == query:
            found = True
            break
    linear.append(found)
indexed = set(values)
print(linear == [query in indexed for query in queries])
print(comparisons, len(queries))
```

## Guided practice

Trace comparisons for first, last and missing values. Explain set setup, retained memory and why probe count is not elapsed time.

## Independent practice

Compare fresh inputs across several sizes, including misses. Preserve output and report construction/reuse conditions, counts and observed timings.

## Check your work

Explain growth and memory tradeoffs. A small count or one timing does not prove universal complexity or benefit.

Continue to [Allocation tracing & memory ownership](/lessons/python-memory-observation).
