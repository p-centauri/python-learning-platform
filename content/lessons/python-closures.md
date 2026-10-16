## The idea in plain language

A function can remember names from the scope where it was created. That remembered environment is a closure. It is useful when you want to configure a small operation once, then use it on many records. A filter factory can remember a prefix and minimum without introducing a large class or global settings.

Remembering a name does not mean copying its value at every line. Python looks up the captured name when the inner function runs. If a loop reassigns that name before you call the function, each function can see the final value. JavaScript developers sometimes expect the separate bindings of `let`; do not carry that assumption into a Python loop.

Give each filter its own factory call. The factory parameters belong to that call, so the returned functions keep separate settings. Strings and integers are convenient immutable settings. Capturing a list still shares that list: mutations are visible to the closure. A default argument can snapshot a binding at function creation, but it does not deep-copy a mutable object.

## Worked example

Run this small example locally, then explain the output in your own words.

```python
from collections.abc import Callable

def at_least(minimum: int) -> Callable[[int], bool]:
    def selected(value: int) -> bool:
        return value >= minimum
    return selected

filters = [at_least(limit) for limit in (10, 20)]
print([selected(15) for selected in filters])  # [True, False]
```

## Guided practice

Build two prefix/minimum filters from different factory calls. Apply both to the same three records, then repeat the first filter. Its results should be unchanged. Explain which names each closure remembers.

## Independent practice

Create a counter factory using nonlocal for one integer. Make two counters and show independent calls. Then capture a list and demonstrate why mutating the list remains visible. Use mutable state only when the contract needs it.

## Check your work

You can trace both creation and invocation, explain the loop trap, and distinguish a fresh binding from a deep copy. A test of one filter alone cannot establish independence.

Continue to [Arguments, signatures & defaults](/lessons/python-binding).
