## The idea in plain language

Passing a request label through every helper can be noisy. A ContextVar stores a value in the current execution context. Async tasks can have different current values without overwriting one global label. Create ContextVar objects at module level; contexts retain references to the variables.

set returns a token for the previous state. Keep it and reset it in finally. A nested scope temporarily overrides its parent, then restores it. Do not reset to an invented default, because the parent may already have a meaningful label. On the Python 3.13 baseline, reset is explicit; we do not rely on newer token context-manager syntax.

An asyncio task normally captures a shallow current-context copy when created. Later parent changes do not rewrite the child's value. Stored objects are not deep-copied: a mutable value can still be shared through aliases. Use small immutable metadata when that is the intention.

copy_context captures the context, and Context.run enters it for a synchronous call, restoring the previous context on exit. Tokens belong to their variable and context. A scope must enter and exit in the same context; create fresh instances instead of moving an entered scope across tasks.

asyncio.to_thread propagates current context to its worker call. Direct executor submission does not automatically promise that behavior; pass a copied context explicitly when needed. Broader thread/process behavior belongs to the next unit.

A request label is metadata, not proof of identity or permission. Put request_scope outside resource scopes if cleanup needs its label: inner release happens before the outer token resets. Keep sensitive payloads out of metadata and logs.

## Worked example

Run this trusted example locally and trace ownership and exit order.

```python
import asyncio
from contextvars import ContextVar
label: ContextVar[str] = ContextVar("label", default="none")
async def main() -> None:
    gate = asyncio.Event()
    async def child() -> str:
        await gate.wait()
        return label.get()
    token = label.set("parent")
    try:
        task = asyncio.create_task(child())
        nested = label.set("later")
        try:
            gate.set()
            print(await task, label.get())  # parent later
        finally:
            label.reset(nested)
    finally:
        label.reset(token)
    print(label.get())  # none
asyncio.run(main())
```

## Guided practice

Trace parent, child and default values. Explain task-creation time versus later changes and why token reset preserves nesting.

## Independent practice

Implement request_scope. Test nested normal/failure restoration, tasks, copy_context and invalid labels. Show cleanup sees its label with correct nesting.

## Check your work

No label leaks into a later scope. Tasks keep captured values, and metadata never replaces authorization.

Continue to [Weak references & honest lifetime ownership](/lessons/python-weak-lifetime).
