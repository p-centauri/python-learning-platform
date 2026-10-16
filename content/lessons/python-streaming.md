## Follow memory through every stage

This is lesson 3 of 5. A pipeline is a sequence of transformations. A source yields values, a stage validates or transforms them, and a final consumer produces a result. Streaming works when every stage can make progress without storing the whole input.

```python
from collections.abc import Iterable, Iterator

def nonnegative(values: Iterable[int]) -> Iterator[int]:
    for value in values:
        if value < 0:
            raise ValueError("negative duration")
        yield value

def summarize(values: Iterable[int]) -> tuple[int, int]:
    count = 0
    total = 0
    for value in values:
        count += 1
        total += value
    return count, total

assert summarize(nonnegative(iter([12, 7, 0]))) == (3, 19)
assert summarize(nonnegative(iter([]))) == (0, 0)
```

There is no list of intermediate values here. The consumer keeps two counters. That does not mean literally constant bytes forever: Python integers can grow as counts grow. It means the program does not retain one object per input record. This distinction is more useful than promising unlimited input with no memory growth.

Some transformations need more state. `sorted(source)` must collect values for sorting. Grouping every distinct user into a dictionary can grow with the number of users. A generator at the beginning does not cancel either cost. Decide whether to use a fixed group set, external storage or a documented limit.

## Bound a single record too

Reading line by line avoids keeping the entire file, but a single line can still be enormous. In the project, a binary file reader uses `readline(limit + 1)` and rejects a line exceeding the limit. The extra byte distinguishes a line at the limit from a longer one without reading the rest into memory.

The project counts bytes including any newline, then decodes each accepted line as UTF-8. A byte limit and a character limit differ for non-ASCII text. This is a teaching contract, not a promise about all log formats.

## Guided practice

Feed the example a source that raises after two values. Observe that `summarize` raises rather than returning a partial result. Now insert `list(...)` between stages and notice that consumption shifts earlier. Explain which stage owns each retained value.

## Independent task

Write a summary for readings in exactly three groups: api, db and worker. Each group needs count and total duration. Reject other groups. Empty input should return all three groups with zero values.

Use a one-use source and a larger generated input. Keep only the current reading and the fixed group totals. Do not sort, keep a history list or create a dictionary entry for every record ID.

## Check your work

Verify exact totals, the empty result and failure on an unknown group. Inspect the code's retained state in addition to passing tests. A finite test cannot prove a memory bound for every possible implementation.

When the input is a file, consumption and cleanup must agree on who owns it. The next lessons add useful error context and an explicit resource lifetime.

[Next: exceptions with useful context](/lessons/python-error-chains)
