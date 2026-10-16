## The idea in plain language

A profiler helps locate expensive work. cProfile observes function calls and records how much measured time they consume. Use it to find a likely bottleneck, then time the actual proposed change separately. Instrumentation adds cost, so a profiled run is a different experiment.

Self time is measured in a function's own body, excluding subcalls. Cumulative time includes calls beneath it. A coordinator can have low self time and high cumulative time because its children do the work. Sorting by cumulative cost helps locate expensive paths; sorting by self cost highlights work in a particular body.

Call counts matter. An inexpensive operation repeated thousands of times can dominate the total. In the lab a four-key workload repeats 32 requests: a cache changes computation count from 32 to four while retaining the same result. That count is behavioral evidence; actual timing still depends on the environment.

Reproduce representative inputs. A tiny hot-cache profile does not describe a cold start, a cache-miss-heavy job or live network waiting. CPU profiling also does not explain every latency cause. Combine the question, failure behavior and observations before choosing a change.

Keep profiling separate from benchmark timing and allocation tracing when you want to understand each cost. Save the report and explain the selected function/call path. The academy stores your interpretation and reported output for manual review; it does not turn a profiler table into an automatic expert grade.

## Worked example

Save this trusted example as example.py and run it locally. Keep profiling/memory instrumentation separate from benchmark timing.

```python
import cProfile
from io import StringIO
import pstats
def compute(number: int) -> int:
    return sum(n * n for n in range(number))
def work() -> int:
    return sum(compute(n) for n in [10, 20, 30])
profile = cProfile.Profile()
result = profile.runcall(work)
stream = StringIO()
pstats.Stats(profile, stream=stream).strip_dirs().sort_stats("cumulative").print_stats(5)
print(result == work())
print(len(profile.getstats()) > 0)
```

## Guided practice

Find self/cumulative columns in an actual report. Identify why a coordinator can have little self time but substantial cumulative cost.

## Independent practice

Profile the baseline separately from timing. Preserve the report, identify a repeated call and state a testable optimization hypothesis.

## Check your work

A profile suggests where to investigate. Verify outputs and measure separately before claiming benefit.

Continue to [Input growth, algorithms & retained results](/lessons/python-workload-growth).
