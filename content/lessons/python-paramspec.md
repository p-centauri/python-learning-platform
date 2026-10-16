## The idea in plain language

A decorator should not silently turn a precise callable into an anything-goes interface. ParamSpec carries its parameter list, including positional and keyword call rules. A separate return type variable carries the result. Callable[P, R] in and Callable[P, R] out describe a wrapper that preserves those caller relationships.

Inside the wrapper, P.args and P.kwargs describe the forwarded argument groups. Pass them straight to the target. A Callable[..., R] permits an arbitrary parameter list to the checker and loses useful call-site checks. Merely annotating *args as object is also insufficient to preserve the original callable's signature.

functools.wraps has a different job: it copies useful metadata and exposes __wrapped__ for inspection. It does not perform runtime argument validation or make an incorrect wrapper implementation transparent. ParamSpec gives static call-site checks; the actual target binding and implementation determine runtime behavior. Check both layers. A wrapper that injects one leading positional parameter can use Concatenate with ParamSpec; arbitrary keyword remapping needs a separate, deliberate interface rather than pretending the original parameters stayed unchanged.

The example observes synchronous calls. The lab adds explicit started/returned/raised events and preserves target result/error identity when its observer is reliable. If a call returns a generator or awaitable, it has returned an object; that is not proof that consuming or awaiting it later succeeded. Observer failures can also occur before or after target effects. Document those phases and avoid automatic retries. A generic annotation does not decide side-effect, cancellation or ownership policy for you.

## Worked example

Run this trusted example locally and compare actual behavior with its static contract.

```python
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar, assert_type

P = ParamSpec("P")
R = TypeVar("R")
calls: list[str] = []

def traced(function: Callable[P, R]) -> Callable[P, R]:
    @wraps(function)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        calls.append("called")
        return function(*args, **kwargs)
    return wrapped

def label(value: int, /, *, prefix: str) -> str:
    return f"{prefix}-{value}"

observed = traced(label)
result = observed(3, prefix="api")
assert_type(result, str)
print(result, calls)  # api-3 ['called']
```

## Guided practice

Predict why observed(3, "api") must be rejected by the checker: prefix is keyword-only. Compare that with the accepted call. Inspect metadata and explain why wraps cannot repair a wrapper that changes the result or calls the target twice.

## Independent practice

Implement watch_call in the lab without casts or Any. Run the keyword-only, wrong-name and wrong-input fixtures, plus runtime result/error identity cases. Show a generator whose later failure happens after the wrapper has already recorded returned, and state the observer-failure policy.

## Check your work

The wrapper preserves P and R, forwards one call and keeps useful metadata. The emitted events describe the declared phase only; no async completion, retry or rollback promise is implied.

Continue to [Overloads & precise caller contracts](/lessons/python-overloads).
