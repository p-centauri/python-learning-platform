## Produce an item when the caller asks

This is lesson 2 of 5. A generator function contains `yield`. Calling it creates a generator; its body starts when the caller asks for an item. At each yield, execution pauses with its local state saved. The next request resumes it.

```python
from collections.abc import Iterator

steps: list[str] = []

def durations() -> Iterator[int]:
    steps.append("start")
    yield 12
    steps.append("second")
    yield 7
    steps.append("finished")

values = durations()
assert steps == []
assert next(values) == 12
assert steps == ["start"]
assert next(values) == 7
assert steps == ["start", "second"]
assert next(values, None) is None
assert steps == ["start", "second", "finished"]
assert list(values) == []
```

This is lazy work: the producer does only what advancing it requires. It is not a background job and does not run in parallel with the caller. The caller decides when to ask again. Calling `list(values)` or `sum(values)` consumes the stream until it ends, so a lazy source can still lead to eager work downstream.

An ordinary `return` ends a generator. Do not raise `StopIteration` yourself to end one: that can become a RuntimeError. Create a new generator when you need another independent run; an exhausted generator stays exhausted.

## Errors can arrive later

A parser generator may be created successfully and fail on its third `next` call. Code that catches an exception only around generator creation misses that later failure. Put handling around the operation that consumes it.

This also changes validation claims. Reading one good record does not validate the unread file. A preview must not promise that all records are good. The project will calculate a complete summary before printing success.

## Guided practice

Add an exception after the first yield in a local copy. Confirm that creation succeeds, the first next succeeds, and the second next raises. Wrap consumption in `try/except` and inspect when control moves into the handler.

Then replace the last yield with `return`. Explain why the stream ends without producing that last value. Keep the original working example for comparison.

## Independent task

Write `running_totals(values: Iterable[int]) -> Iterator[int]`. For input `2, 5, -1`, it should yield `2, 7, 6`. Keep just the running sum. An empty source yields nothing, and two independent calls must not share their totals.

Use a recording source to check that construction requests nothing and one next requests only one input item. Do not build an output list first.

## Check your work

Your first result must be available before the rest of the source is consumed. A test that only compares `list(result)` with an expected list checks values but can miss unnecessary eager reading. Check both values and timing of consumption.

Generators retain their local references while suspended. They are not automatically small if their locals contain a huge cache. Next we will look at memory across the whole processing chain.

[Next: streaming pipelines and limits](/lessons/python-streaming)
