## The idea in plain language

Cleanup can fail too. A close method might raise while the caller is already handling a parsing error. Decide what callers should observe instead of assuming release always succeeds. Native ExitStack continues attempting remaining callbacks after one raises. A later cleanup error can replace the earlier error, with Python's exception context retaining the preceding failure.

Callback return values do not suppress errors. A callback returning True still leaves a body error active. In contrast, __exit__ can return a true value to suppress the active exception. Broad suppression can turn a failed operation into apparent success. Suppress only a narrow error the caller can safely treat as handled.

A generator context manager must yield exactly once. If it catches an error around yield just to log it, re-raise it. Otherwise it reports the error as handled. Put required release work in finally, preserving the outcome unless the contract intentionally changes it.

The lab chooses callback cleanup, without suppression or retry. With reliable cleanup it preserves the exact acquisition/body BaseException. Cleanup failures retain native chaining and remaining-attempt behavior. It does not promise an ExceptionGroup containing every error or successful release after close fails. Retrying could duplicate effects and needs its own contract.

Scopes produced by contextmanager are for one entry. Call the factory again for a fresh scope; do not cache a used instance for repeated or concurrent entries. Reverse cleanup helps dependent resources, but it is not a database transaction or rollback of body effects.

## Worked example

Run this trusted example locally and trace ownership and exit order.

```python
from contextlib import ExitStack
events: list[str] = []
body = ValueError("body")
cleanup = OSError("cleanup")
def close_a() -> None:
    events.append("a")
def close_b() -> None:
    events.append("b")
    raise cleanup
try:
    with ExitStack() as stack:
        stack.callback(close_a)
        stack.callback(close_b)
        raise body
except OSError as error:
    assert error is cleanup and error.__context__ is body
    print(events)  # ['b', 'a']
```

## Guided practice

Follow a body error, an inner cleanup error and a remaining outer cleanup. Explain the final raised error and its __context__.

## Independent practice

Add a regression where both callbacks fail. Record the order and exception chain. Explain why a callback returning True cannot suppress a body error.

## Check your work

Remaining cleanup is attempted. The observed outcome and chain match the published semantics.

Continue to [AsyncExitStack & awaited cleanup](/lessons/python-async-cleanup).
