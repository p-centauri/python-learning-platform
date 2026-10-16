## The idea in plain language

A with statement gives one clear place to release a resource. When the number of resources comes from input, nested with statements become awkward. ExitStack collects cleanup as acquisition succeeds. It releases registered work in reverse order: the most recently acquired resource leaves first.

Register cleanup immediately after each successful handoff. If opening B fails after A opened, A must still close. If acquisition itself fails before returning a usable handoff, the factory owns its partial work. A stack cannot clean a resource it never received. Make that responsibility part of the interface.

Use enter_context when a resource already implements the context-manager protocol. It registers __exit__ only after __enter__ succeeds. Use callback for an ordinary cleanup function. Callback does not receive exception details and its return value cannot suppress an exception. An exit function entered as a context manager can suppress exceptions; these are different contracts.

The lab uses a supplied Resource(value, close) handoff and callback registrations. Its borrowed factory iterable stays owned by the caller. A count limit of eight prevents unlimited successful acquisitions. Detect overflow by observing one extra factory without calling it. Count limits cannot interrupt a blocked iterator or factory.

ExitStack does not run its callbacks just because the stack becomes garbage. Enter a scope or call close explicitly. pop_all transfers registrations to another stack without running them; whoever takes that stack becomes responsible for closing it. The lab keeps ownership inside one scope.

## Worked example

Run this trusted example locally and trace ownership and exit order.

```python
from contextlib import ExitStack
events: list[str] = []
def acquire(name: str) -> str:
    events.append("open:" + name)
    return name
def close(name: str) -> None:
    events.append("close:" + name)
with ExitStack() as stack:
    for name in ["a", "b"]:
        value = acquire(name)
        stack.callback(close, value)
    events.append("body")
print(events)  # open:a, open:b, body, close:b, close:a
```

## Guided practice

Trace a failure opening the second resource. State what was already registered and who owns work inside the failing factory.

## Independent practice

Implement owned_resources. Test partial acquisition, input failure, overflow and a body exception. Keep input borrowed and record exact open/close order.

## Check your work

Earlier handoffs close even when later setup fails. Registration happens before further acquisition.

Continue to [Cleanup errors & deliberate suppression](/lessons/python-cleanup-errors).
