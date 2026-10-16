## A collection and a position are different things

This is lesson 1 of 5 in streaming and resource cleanup. An iterable can supply an iterator. An iterator remembers where it is and supplies the next item. A list can usually supply a fresh iterator each time; an existing iterator keeps its current position.

```python
from collections.abc import Iterable

names = ["api", "db", "worker"]
cursor = iter(names)
assert next(cursor) == "api"
assert list(cursor) == ["db", "worker"]
assert list(cursor) == []
assert list(names) == ["api", "db", "worker"]
assert iter(cursor) is cursor

def count_items(values: Iterable[str]) -> int:
    total = 0
    for _ in values:
        total += 1
    return total

fresh = iter(names)
assert count_items(fresh) == 3
assert count_items(fresh) == 0
```

The first `list(cursor)` consumes the remaining items. It does not reset the cursor. Calling `iter` on that iterator returns the same iterator, so it cannot restart a second pass. When no items remain, `next` raises `StopIteration`; a `for` loop handles that signal for you. `next(cursor, None)` can instead provide a default when exhausted, if None cannot be confused with a real result.

Think of the list as a playlist and the iterator as a play position. This analogy has a limit: arbitrary iterables may read files or perform work, and they may be usable only once. An `Iterable` annotation alone does not promise cheap access, a length or replay.

## Guided practice

Run the example and predict every assertion before checking it. Make two separate iterators from `names`. Advance one twice and the other once. Their positions are independent because each call created a fresh list iterator.

Then assign `other = cursor`. This gives another name to the same cursor. Advancing through either name changes the position both see. Link this behavior to the earlier ownership lesson: assignment shares an object, not a copy of its state.

## Independent task

Write `count_and_last(values: Iterable[str]) -> tuple[int, str | None]`. Return the count and last item in one pass. Empty input returns `(0, None)`. Do not convert the input to a list or iterate over it twice.

Test a list, an empty iterator and an iterator whose first item has already been consumed. If the caller passes a partially consumed iterator, your function must process only what remains. Document that consuming input is part of this function's behavior.

## Check your work

Use an iterator that records each request for an item. Check that your function does not attempt a second pass. A solution that counts once and then searches for the last item will fail on a one-use source even if it works on lists.

A list conversion is sometimes appropriate for small data that must be reused. Make that choice explicitly because it consumes the source and keeps all its items. This module's project will instead read once and retain only a small summary.

[Next: generators and deferred work](/lessons/python-generators)
