## The idea in plain language

A decorator receives a callable and returns a callable. The @ syntax is a convenient way to assign that returned function back to the original name. A decorator factory adds an earlier configuration step: first receive settings, then receive the target, then run the wrapper when someone calls it. Draw those stages before debugging a decorator.

The smallest useful wrapper does one extra job while preserving the target's contract. For our reporting interface that means passing the same iterable once, returning the same report object, and allowing the same failure to escape. Materializing the iterable in the wrapper would change memory use and the timing of a late error. Catching an error and returning an empty report would silently convert failure into success.

Use functools.wraps so the wrapper carries the target's name and documentation and exposes __wrapped__. Tools such as inspect.signature can follow that link. Metadata preservation does not magically forward arguments or enforce annotations. This unit wraps one explicit reporter signature; a fully generic typed decorator needs additional concepts such as ParamSpec, which remain later material.

A bare raise inside an exception handler preserves the caught exception. Catch ordinary Exception only when you have a reason, such as recording a safe failure event. KeyboardInterrupt and SystemExit belong to BaseException and usually need to keep their special behavior.

## Worked example

Run this small example locally, then explain the output in your own words.

```python
from collections.abc import Callable
from functools import wraps

def observed(function: Callable[[int], int]) -> Callable[[int], int]:
    @wraps(function)
    def wrapped(value: int) -> int:
        return function(value)
    return wrapped

@observed
def double(value: int) -> int:
    """Double one integer."""
    return value * 2

print(double(4), double.__name__)  # 8 double
```

## Guided practice

Add a call counter outside the target. Assert that one wrapper call produces one target call and returns the identical dictionary. Raise a pre-created exception and assert identity, rather than checking only its text.

## Independent practice

Build a configured logging wrapper for the project reporter. Validate its source label when creating the wrapper. Explain why configuration failures must happen before consuming records. Document the supported signature rather than claiming universal forwarding.

## Check your work

The wrapper is quiet during creation, preserves metadata and leaves resource ownership with its caller. Tests cover success and failure. An assertion about __name__ alone cannot prove transparency.

Continue to [Pytest fixtures & useful case tables](/lessons/python-test-fixtures).
