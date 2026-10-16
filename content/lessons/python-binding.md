## The idea in plain language

Calling a function first binds arguments to parameter names. Only after a valid binding does the body run. A missing required argument, two values for the same parameter, or an unexpected keyword normally raises TypeError. Treat these as interface errors rather than swallowing them inside the function.

A slash marks preceding parameters as positional-only. A star marks following parameters as keyword-only. Read the signature below as: supply the records positionally, and name the minimum explicitly. Naming settings makes call sites easier to review. Positional-only data keeps a wrapper from promising keyword forwarding that it does not implement.

Default expressions are evaluated when the function is defined, not afresh for every call. A default list can therefore retain items from earlier callers. Use None as the absence marker and allocate a fresh container inside the function. This is about ownership, not a rule against all defaults: immutable numbers and strings are usually straightforward defaults.

`inspect.signature(function).bind(...)` can check argument binding without executing the body. It is useful in tooling, but it does not validate domain rules or prove runtime types. Binding the integer -1 to minimum can be legal even when your application contract rejects negative thresholds.

## Worked example

Run this small example locally, then explain the output in your own words.

```python
from collections.abc import Iterable

def total(values: Iterable[int], /, *, minimum: int = 0) -> int:
    return sum(value for value in values if value >= minimum)

def add_note(note: str, notes: list[str] | None = None) -> list[str]:
    result = [] if notes is None else notes
    result.append(note)
    return result

print(total([2, 10], minimum=5))  # 10
print(add_note("first"), add_note("second"))  # separate lists
```

## Guided practice

Write out three calls to total: one valid, one supplying values by keyword, and one supplying minimum positionally. Predict which fail before the body. Confirm failures in a small local test using pytest.raises(TypeError).

## Independent practice

Design a report signature with a positional input and named configuration. Explain whether a supplied notes list should be borrowed or copied. Use inspect.signature.bind to check a valid call and a duplicate argument without calling the function.

## Check your work

Your examples separate argument binding from value validation. A fresh default list stays independent across callers; an explicitly supplied list follows the documented ownership decision.

Continue to [Decorators that preserve behavior](/lessons/python-decorators).
