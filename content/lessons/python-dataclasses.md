## Describe a value without repetitive methods

This is lesson 2 of 5. A task needs an identifier and a title. A dataclass can generate initialization, a useful printed representation and value-based equality from declared fields. It does not decide the rules for a valid task. Write those rules yourself.

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Task:
    task_id: str
    title: str

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ValueError("task_id must be nonblank text")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be nonblank text")

one = Task("t1", "Read traceback")
assert one == Task("t1", "Read traceback")
assert one != Task("t2", "Read traceback")

@dataclass
class Draft:
    titles: list[str] = field(default_factory=list)

left = Draft()
right = Draft()
left.titles.append("Investigate")
assert right.titles == []
```

Here equality compares the fields, so separately created tasks can represent equal values. This is useful in tests and snapshots. It does not automatically make two tasks the same database record; your storage rules still decide what an identifier means.

`default_factory=list` calls `list` when an instance needs its default. Passing `list()` would create a value immediately instead of supplying a factory. Also, a factory does not copy a list deliberately supplied by the caller. Ownership still needs thought.

## Frozen is a limited promise

`frozen=True` blocks ordinary field assignment. It does not freeze objects inside a field. A frozen object with a list field can still have that list mutated. Our task contains strings, which avoids that particular problem. Frozen also does not mean validated: without `__post_init__`, a blank title would be accepted despite its type annotation.

The example rejects invalid values but does not strip valid fields. Keeping validation and normalization separate makes the behavior predictable. The project later normalizes outside input before building a task.

## Guided practice

Print `one`, compare it with another equal task and try assigning a new title. Inspect the exception. Next make a frozen dataclass with a list field and append an item to the list. Explain why these two operations differ; do not describe the whole nested object as immutable.

## Independent task

Create a frozen `TaskBatch` with a `name: str` and `tasks: tuple[Task, ...]`. Reject blank names. Add a read-only `count` property. Make two equal batches using separately created task values, and test that equality works as expected.

Keep mutation in a separate store instead of adding an editing method to the value. Do not use `unsafe_hash=True` to silence a design problem. A mutable value used as a dictionary key can break lookup expectations.

## Check your work

Test empty and nonempty batches, invalid names and equal values. Explain why tuples of these tasks are a useful snapshot, and why the same reasoning would fail if a task held a mutable nested list.

[Next: composition and small services](/lessons/python-composition)
