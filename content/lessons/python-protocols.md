## Describe the operations a caller needs

This is lesson 5 of 5. A protocol is a typed description of supported operations. A class can satisfy it by having compatible methods without inheriting from it. This is useful when a service should accept both real storage and a small test substitute.

```python
from typing import Protocol

class TitleSink(Protocol):
    def add(self, title: str) -> None: ...

class RecordingSink:
    def __init__(self) -> None:
        self.received: list[str] = []

    def add(self, title: str) -> None:
        self.received.append(title)

def send_title(sink: TitleSink, title: str) -> None:
    sink.add(title)

recording = RecordingSink()
send_title(recording, "Write failure test")
assert recording.received == ["Write failure test"]
```

`RecordingSink` never mentions `TitleSink`, but its method fits the contract. The checker verifies that fit at the call. Matching parameter types, return types and callable names matter; method names alone are not enough. Save this example and run mypy in strict mode as in the previous lesson.

A protocol describes an interface, not the full behavior. A sink that silently discards titles can have the right types. Tests and documentation must say whether writes persist, duplicates are allowed and failures propagate. `@runtime_checkable` would not turn a protocol into a full signature or data validator; the project does not need runtime protocol checks.

## Guided practice

[Download the typed task-inbox project](/api/projects/python-task-inbox/starter). Read its README, then run the public tests. The starter includes typed interfaces and unfinished implementation points. Initial `NotImplementedError` failures are expected. Implement a frozen task value, separate memory-store state, strict input validation and a service accepting the storage protocol.

Run `python -m mypy` from the extracted folder after installing the pinned tool. The supplied configuration checks the implementation, demo and typed usage example. The starter can pass type checking while still raising `NotImplementedError`: compatible signatures do not supply working behavior.

## Independent project

Complete the documented contract and pass the local tests. Use a fake store that records accepted tasks to prove that the real service validates before writing. Use another store that raises an error to prove that storage failure reaches the caller. Do not mock the service under test.

Temporarily change the type example's store so `all()` returns strings instead of tasks. Capture the checker diagnostic, then restore the correct type. Add two runtime regression tests and a brief explanation of each class's responsibility. Libraries needed here are `dataclasses`, `typing` and `unittest` from Python, plus mypy as a development tool; no web framework is needed.

## Check your work

Show three separate results: runtime tests, a clean type check and the intentional incompatible-store diagnostic. A reviewer should inspect ownership, validation before writes, immutable snapshots and honest failure handling. Public tests are useful evidence, not proof of complete correctness.

Use the [project checklist](/projects#python-task-inbox) to record your work. The app does not execute or grade your code. This completes a bounded object-design module; continue with [generators and resource cleanup](/lessons/python-iterators). Packaging and the larger ingestion project remain planned.
