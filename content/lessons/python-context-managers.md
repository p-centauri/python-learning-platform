## Give resources a visible lifetime

This is lesson 5 of 5. A resource such as a file needs a clear owner and a clear end to its use. A `with` block makes that lifetime visible. It arranges cleanup when the block exits normally or raises, without relying on when an object is garbage-collected.

```python
from collections.abc import Iterator
from contextlib import contextmanager
from io import StringIO

@contextmanager
def open_example() -> Iterator[StringIO]:
    source = StringIO("api\ndb\n")
    try:
        yield source
    finally:
        source.close()

with open_example() as stream:
    assert next(stream) == "api\n"
    # Deliberately stop without reading db.
assert stream.closed

try:
    with open_example() as failing_stream:
        raise RuntimeError("consumer failed")
except RuntimeError:
    pass
assert failing_stream.closed
```

A function decorated with `@contextmanager` yields once to supply the value used inside the block. Its cleanup belongs in finally. This is different from a record generator, which may yield many records. Prefer a resource's existing context manager when it has one; the wrapper above makes the ownership rule easy to observe.

## A loop break does not promise generator cleanup

Stopping a `for` loop does not automatically close a generator that still has references. If the generator holds an open file while paused, the file can remain open. Do not rely on interpreter-specific destruction timing. Put file ownership in an enclosing `with` block, or explicitly close a generator you own using a suitable cleanup scope.

Likewise, avoid returning a lazy file iterator from inside a with block that has already ended. Its next read would use a closed resource. In this module's project, consume the iterator inside `with open_readings(path) as records:`. The context owns the file; the parser borrows a sequence of lines and must not close caller-owned input.

## Guided practice

[Download the streaming service-log lab](/api/projects/python-log-stream/starter). Read its exact contract and run the supplied tests. Implement the lazy parser, summary and file context. The starter's NotImplementedError failures are intentional. The project uses standard-library `collections.abc`, `contextlib`, `json`, `pathlib`, `dataclasses` and `unittest`; mypy remains an optional local development check.

## Independent project

Process one JSON record per line, enforce the byte limit, preserve error causes and return fixed service totals. The command must print its report only after successful consumption and cleanup. A good first record followed by a bad one must produce no success output.

Add two tests of your own. Show file closure after full consumption, no consumption, early exit, a parsing error and a consumer error. Use observable closed state instead of forcing garbage collection. Check a borrowed stream separately: closing it belongs to its caller.

## Check your work

Pass the public tests, then explain which object owns each resource and what remains in memory between records. Record a small reproduction for an early-exit leak and how your design prevents it. A reviewer should inspect both successful and failed paths; public tests do not certify the whole implementation.

Use the [project checklist](/projects#python-log-stream) to track your evidence. All code runs locally; the app does not grade it. Continue with [installable packages and managed HTTP ingestion](/lessons/python-packages).
