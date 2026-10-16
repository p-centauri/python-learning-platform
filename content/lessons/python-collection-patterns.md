## Choose what must be preserved

This is lesson 2 of 5. A collection is not just a convenient container: it decides which information the program keeps. For an event timeline, multiple events can happen at the same instant. A dictionary keyed only by timestamp would overwrite earlier events, so the report needs a list.

```python
items = [("first", 3), ("second", 1), ("third", 1)]
ordered = sorted(items, key=lambda item: item[1])
assert ordered == [("second", 1), ("third", 1), ("first", 3)]
assert items[0] == ("first", 3)
```

`sorted` returns a new list. The key function chooses the value used for ordering. Python's sort is stable: when keys are equal, their original relative order stays the same. That gives our timeline a clear tie rule without inventing a secondary sort order.

## Count, group and look up

```python
from collections import Counter, defaultdict

labels = ["deploy", "login", "deploy"]
assert Counter(labels) == {"deploy": 2, "login": 1}
groups = defaultdict(list)
for position, label in enumerate(labels):
    groups[label].append(position)
assert groups["deploy"] == [0, 2]
```

Counter expresses counting. `defaultdict(list)` creates a fresh list when a missing key is accessed through indexing. That access changes the dictionary: inspecting `groups["missing"]` inserts a key. Use `.get()` when a missing lookup should leave the mapping unchanged. A regular dictionary and explicit loop are fine when they explain the task more clearly.

## Some helpers stop early

```python
names = ["Ali", "Sara"]
values = [10]
assert list(zip(names, values)) == [("Ali", 10)]
try:
    list(zip(names, values, strict=True))
except ValueError:
    mismatched = True
else:
    mismatched = False
assert mismatched
```

Ordinary zip stops at the shorter input. If both lists must describe the same number of records, that can silently lose data. `strict=True` detects different lengths when the iterator is consumed. Creating the zip object alone does not run all the checks. A tuple's slots cannot be reassigned, but a mutable list stored inside a tuple can still change; container immutability is not deep immutability.

## Guided practice

Add a fourth item with key 1 to the sorting example. Predict exactly where it lands. Then build a dictionary keyed by the numeric value and notice which items disappear. Pick the collection based on whether repeated values are allowed, not on typing less code.

## Independent task

Write `order_records(records)` that returns a new list ordered by a numeric `priority` field. Keep every record, preserve input order for ties, and leave the input list unchanged. Test an empty list, repeated priorities and already-sorted input.

## Check your work

The output should have exactly as many records as the input. Checking only the first record can miss data loss. In the timeline lab, the same rule applies, but the sort key must represent an actual instant rather than a displayed timestamp string.

[Next: dates and timestamp input](/lessons/python-dates)
