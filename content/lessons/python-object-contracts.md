## The idea in plain language

Finish the feed-object library as one small local package. Budget fields validate assignment and keep settings separate for each object. FeedKey makes durable identity fields explicit while allowing dictionary lookup through a distinct equal key. Reading and Snapshot preserve ordered observations with a finite element limit. No metaclass, ORM, network request or API execution is needed.

The input iterable is borrowed. Consume it once and snapshot valid elements as you go; do not rely on its reported length. A 65th observation proves the 64-element limit has been exceeded, so fail immediately and never request a 66th. Reject duplicate equal keys even when their values differ, because silently choosing a duplicate would invent a conflict policy. Propagate input errors and let construction fail without returning a partial result. The caller remains responsible for closing a resource-backed iterator.

Review observable behavior: independent fields, missing values, preserved old state after rejected updates, class descriptor access, supported comparison dispatch, equal-key dictionary lookup, index/slice/order behavior and input mutation after snapshotting. Avoid tests demanding exact hash integers, distinct hashes for all unequal keys, private allocation sizes or a particular dictionary implementation. Count limits do not prove time bounds on arbitrary iterators.

Build both source archive and wheel, install the wheel in a fresh environment, and run outside the source directory without PYTHONPATH. The maintained verifier also maps records from the earlier installed ingestion package into these value objects. That is an explicit adapter; neither original package contract changes. Submit actual command output, two regression cases, the cooperative diamond reproduction and a short design explanation. Four manual criteria preserve the difference between finite local test evidence and reviewer judgment. Reading completion, checkpoints and reported project output do not certify advanced expertise; typing and context/resource lifetime are published next, while concurrency and measured performance remain later units.

## Worked example

Run this trusted example locally and predict the output before execution.

```python
from collections.abc import Iterator

def bounded_copy(rows: Iterator[int], limit: int) -> tuple[int, ...]:
    saved: list[int] = []
    for row in rows:
        if len(saved) == limit:
            raise ValueError("too many")
        saved.append(row)
    return tuple(saved)

pulls: list[int] = []
def source() -> Iterator[int]:
    for value in range(10):
        pulls.append(value)
        yield value

borrowed = source()
try:
    bounded_copy(borrowed, 2)
except ValueError:
    print(pulls)  # [0, 1, 2]
print(next(borrowed))  # 3
```

## Guided practice

Explain why overflow requires one observation beyond the accepted capacity. Identify the owner of borrowed, and predict the next unconsumed value after failure. This small example illustrates observation count; the lab adds type, identity and duplicate validation.

## Independent practice

Finish all five lab methods, run the public tests, types/lint, builds and clean installed demo. Add two regressions and an offline adapter from the prior ingestion Record to Reading with namespace "feed". Submit evidence in Projects, including the MRO trace and a property/composition tradeoff.

## Check your work

You can reproduce lookup, delegation and key behavior and show the installed artifact works independently of source. Report only commands actually run. Explain remaining gaps instead of calling a finite suite an expert certificate.

Open the [Feed object-contract lab](/projects#python-feed-objects) to download and submit evidence. Advanced typing and contexts are published next; concurrency and measurement remain planned.

Continue to [Generics & related input and output types](/lessons/python-generic-functions) for the next published Python unit.
