## The idea in plain language

Start with a question you can test: what operation is slow, for which input, and what result must stay the same? Keep a working baseline. A shorter function is not automatically faster, and a fast wrong result is still wrong.

Wall time measures the interval the caller experiences, including waiting. Process CPU time measures CPU used by the process, including its threads, and excludes ordinary sleeping time. perf_counter_ns and process_time_ns return integer nanoseconds; their starting values are not calendar timestamps. Compare differences from the same clock.

Repeat work and preserve the raw samples. Report Python/build, platform, input size, repetitions, variant order and whether a cache starts empty or warm. Reusing a consumed iterator or mutated input changes the experiment. Repeated operations can have effects; timing does not roll them back.

For a tiny snippet, timeit manages repeated calls and can separate setup. It normally disables cyclic garbage collection during its timed run, so say when GC behavior matters. Look at the sample vector and interference. A best microbenchmark sample describes a lower observed cost; it is not a production latency percentile. A few samples do not establish broad statistical certainty.

The lab's sample function is intentionally smaller than timeit: explicit finite repeats, two clock reads around each call and an unchanged last result. Injected clocks test call order and errors deterministically. Actual clocks produce observations; no machine must beat a fixed timing threshold. A repeat count bounds calls, not elapsed time.

## Worked example

Save this trusted example as example.py and run it locally. Keep profiling/memory instrumentation separate from benchmark timing.

```python
from time import perf_counter_ns, process_time_ns
def work() -> int:
    return sum(n * n for n in range(1000))
wall_start, cpu_start = perf_counter_ns(), process_time_ns()
value = work()
cpu_ns = process_time_ns() - cpu_start
wall_ns = perf_counter_ns() - wall_start
print(value)
print(wall_ns >= 0, cpu_ns >= 0)
```

## Guided practice

Identify workload, result and clock. Explain why the two intervals cover slightly different instrumentation and why samples do not establish production percentiles.

## Independent practice

Implement sample with injected clocks, exact repeat validation and failure traces. Record actual wall/CPU observations separately and state cache/input reuse.

## Check your work

Keep raw observations and equivalent results. Report effects and environment; no brittle timing pass/fail threshold.

Continue to [Profiling: find where the work goes](/lessons/python-profile-costs).
