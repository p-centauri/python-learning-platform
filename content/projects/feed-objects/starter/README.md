# Feed object-contract lab

Implement five methods in `src/academy_feed_objects/objects.py`: the descriptor's `__get__`/`__set__`, the key's `__eq__`/`__hash__`, and `Snapshot.__init__`. Supplied validation, length and indexing are part of the contract. No network, database or third-party runtime dependency is needed. Python 3.13+; pytest, mypy, Ruff and build are development tools.

## Literal contract

- `Budget.limit` and `reserve` are separate data descriptors. Class access returns the descriptor. Each Budget has its own `_values`; reading an unset field raises AttributeError. Accept exact ints (reject bool) from 0 through 64. Reject before changing existing state. Inherited descriptors work; each field uses its own descriptor. Provided binding rejects reusing one descriptor for another field. Do not store learner objects on the shared descriptor.
- `FeedKey(namespace, name)` is frozen. Both fields are exact built-in strings (exclude subclasses that could override equality/hash), ASCII `[a-z][a-z0-9-]{0,31}` with length 1..32. Equality compares both fields only for the same concrete type; unsupported comparisons return the singleton NotImplemented so Python can try the other operand. Hash the same fields. Hash values need not be unique or stable between processes; do not assert literal hashes. Subclass extension requires its own design review.
- `Reading` is supplied, frozen, and accepts an exact FeedKey plus an exact int in 0..60000. Immutability supports stable keys here because all identity values are strings; frozen objects containing mutable fields would need more care.
- `Snapshot(rows)` borrows and consumes an iterable once, stores a tuple in input order, accepts at most 64 exact Reading objects, and rejects equal duplicate keys even when their values differ. Do not trust `len(rows)`. Stop after fetching the 65th item; do not fetch a 66th. Raise TypeError for wrong elements, ValueError for duplicates/overflow; propagate input exceptions. No partial snapshot escapes on failure. Do not close a borrowed iterator.
- Supplied Sequence methods give length, negative indexing, tuple slicing, iteration, membership and reverse iteration. Empty snapshots are false through `__len__`. Original list mutation must not change the snapshot. Frozen fields reject ordinary assignment. Private storage and `object.__setattr__` are not tamper-proof security barriers.

## Run and produce installed evidence

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
python -m mypy src/academy_feed_objects demo.py
python -m ruff check src tests demo.py
python -m build
```

Then create a second fresh environment, install the built wheel and pytest==9.0.3, copy `tests` and `demo.py` to an empty folder outside this checkout, and run `python -I -m pytest -q tests` and `python -I demo.py` there. Expected demo: `{"limit": 2, "count": 2, "total": 15}`. Do not set PYTHONPATH. Check the imported module path belongs to the second environment and `python -m pip check` passes. Tests/maintainer references must not appear in the wheel.

Connect the earlier ingestion package locally by mapping its Records to Reading(FeedKey("feed", record.id), record.value) and building Snapshot. This changes neither package's public contract; use strict types and an offline example. No HTTP is required for the composition check.

## Review evidence

Submit a repository/artifact reference, commands and actual output, and two new regression cases. Include a lookup reproduction with a same-named instance entry; a dictionary lookup using a distinct equal key; a diamond inheritance trace showing each cooperative method once; and an explanation of why a property or composition would be simpler in most applications. Use the accompanying lessons for those traces. Explain input ownership and the 65-item observation bound.

The public tests check a finite local contract. The app stores reported evidence and four self/human criteria; it does not run your code or grant mastery. Passing tests does not prove expertise, concurrency safety, arbitrary memory limits or protection against malicious Python code. No custom metaclass or general descriptor framework is requested.
