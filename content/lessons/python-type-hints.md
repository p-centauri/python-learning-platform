## Type hints describe promises; checks enforce input rules

This is lesson 4 of 5. Type hints help a checker compare calls with function contracts before running the program. Like TypeScript types, they do not automatically validate incoming data. Keep the distinction clear when data arrives from JSON or a form.

```python
from collections.abc import Sequence

def require_title(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("title must be text")
    title = value.strip()
    if not title:
        raise ValueError("title must not be blank")
    return title

def first_title(values: Sequence[str]) -> str | None:
    return values[0] if values else None

assert require_title(" Read docs ") == "Read docs"
assert first_title([]) is None
assert first_title(("Read docs",)) == "Read docs"

result = first_title([])
message = "No tasks" if result is None else result.upper()
assert message == "No tasks"
```

`object` means any Python object may arrive, but the checker does not let us assume string methods exist. After `isinstance`, it knows this branch holds a string. This is called narrowing. `Any` instead permits operations without the same useful checks; spreading it throughout the program can hide mistakes.

`str | None` says that absence is a possible result. A caller must handle it before calling string methods. `Sequence[str]` describes ordered readable strings, allowing both a list and a tuple here. It does not ask for permission to append. A generic type takes a type parameter: `list[str]` and `list[int]` describe lists with different item types. More advanced custom generics come later.

## Guided practice

Save the example as `example.py`. In an activated virtual environment, install the development tool with `python -m pip install mypy==2.3.1`, then run `python -m mypy --strict example.py`. Mypy checks the source; it does not run the assertions. Run `python example.py` separately.

Now add `first_title([42])`. The checker should report an incompatible list item. Remove that line, then try `first_title([]).upper()`: the possible `None` needs handling. Keep a note of each diagnostic and the change that repairs it. Do not solve the exercise with `Any`, `cast` or `# type: ignore`.

## Independent task

Write `require_priority(value: object) -> int` for an integer from 1 to 5. Reject booleans as well as strings, floats and out-of-range integers. In Python, booleans are a subtype of integers, so `isinstance(value, int)` alone is too broad. Check the boolean case explicitly before accepting integers.

## Check your work

Run the checker and runtime tests for 1, 5, 0, 6, True and "2". A clean type check does not prove the range rule; the runtime tests do. Likewise, a few passing tests cannot check every caller in a large program. Use both kinds of evidence.

[Next: protocols and the task-inbox project](/lessons/python-protocols)
