## The idea in plain language

This lab joins related concerns without mixing their responsibilities. Resource scopes own successful cleanup handoffs. Context variables carry current metadata. A weak registry finds a live object without owning its lifetime. Each interface should be precise on its own and when composed.

Resource and AsyncResource pair a value with cleanup. A factory owns partial setup until it returns a valid handoff. The scope then registers cleanup immediately. Do not assume a partly entered context manager automatically receives __exit__: entering may fail before registration. The factory must release its own partial work.

Implement bounded synchronous/asynchronous acquisition, a token-based request scope and two weak-registry methods. Observe events, exact identities, overflow, awaited release and restored context. Finite counts do not impose elapsed-time limits, and a tuple does not keep closed external handles usable.

Nesting is observable. A request scope outside a resource scope preserves its label during cleanup. An acquired immutable Row or Record can be mapped to an ordinary snapshot. Do not generalize that to every resource value: a live file or connection may be unusable after exit.

Build a source archive and wheel. Install the real wheel freshly and run copied tests/demo outside source without editable paths. Strict types inspect caller relationships; runtime tests inspect behavior. Add two regressions and explain failure traces.

Submit artifacts and actual reported output through four review criteria. The academy does not execute this project or independently verify learner-reported output. This is a bounded advanced continuation; concurrency, measured performance, persistence and applied AI remain later work.

## Worked example

Run this trusted example locally and trace ownership and exit order.

```python
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
events: list[str] = []
@contextmanager
def scope(names: list[str], limit: int) -> Iterator[tuple[str, ...]]:
    with ExitStack() as stack:
        values: list[str] = []
        for name in names:
            if len(values) == limit:
                raise ValueError("overflow")
            events.append("open:" + name)
            stack.callback(events.append, "close:" + name)
            values.append(name)
        yield tuple(values)
try:
    with scope(["a", "b"], limit=1):
        raise AssertionError("body must not start")
except ValueError:
    print(events)  # ['open:a', 'close:a']
```

## Guided practice

Identify the owner of input, partial acquisition, registered cleanup, request labels and weak lookup. Trace release before token reset.

## Independent practice

Complete the downloadable lab, add two regressions and install its wheel cleanly. Compose earlier installed values. Submit actual output and explain limits.

## Check your work

Evidence identifies actual ownership and outcomes. Manual judgment remains separate from grades and mastery.

[Download the resource scopes starter](/api/projects/python-resource-scopes/starter), then open the [project checklist](/projects#python-resource-scopes) and [submission workspace](/projects/python-resource-scopes/submissions).

Continue to [Threads, processes & choosing the work boundary](/lessons/python-thread-process).
