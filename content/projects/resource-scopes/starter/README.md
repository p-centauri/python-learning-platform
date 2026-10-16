# Resource scopes lab

Python 3.13+. Implement the five marked functions/methods in scopes.py.
Use the supplied contracts. Runtime requires only the standard library; pytest,
mypy, Ruff and build are development tools. Run locally in your own environment.
The academy stores reported evidence and never executes this package.

## Exact contracts

owned_resources(factories, *, limit=8) is a fresh one-use context manager.
Calling the factory creates a scope; validation and input acquisition start
when entering it. Validate an exact int limit in 0..8 before touching input.
Borrow the single-pass iterable; do not close it, materialize it or retry it.
Invoke each accepted callable once, in order. Each factory must return an exact
Resource containing a value and callable close handoff. Until that return,
the factory owns any partial work and must clean it if acquisition fails.

Register each successful handoff immediately with ExitStack.callback, then
save its value. Yield one tuple of values only after all acquisition succeeds.
Accept at most limit resources. Observe one extra factory to detect overflow,
but do not invoke it or fetch another. On success, caller failure, partial setup,
bad factory/handoff, input failure or overflow, attempt each registered callback
once in reverse order. Callback return values cannot suppress an exception.
With reliable callbacks preserve the exact acquisition/body BaseException.
If cleanup raises, keep native ExitStack exception chaining and attempt remaining
callbacks; the last raised cleanup error can replace the earlier error.
These scopes close only owned handoffs. Returning a tuple does not extend the
external handle's validity or freeze its contents.

owned_async_resources has the same count/ownership contract, using a borrowed
synchronous iterable of async factories. Await acquisition sequentially; each
returns an exact AsyncResource with callable aclose. Register immediately with
AsyncExitStack.push_async_callback, without an intervening await. Await cleanup
in reverse order. A normal single task cancellation after a handoff must await
cooperative cleanup and propagate cancellation. A factory cancelled before
return owns its incomplete acquisition. Repeated cancellation, stalled cleanup,
closed loops, forced termination and hostile code have no guaranteed completion
or hard deadline. No shielding, retries, transactions or global shutdown policy.

request_scope(label) validates exact ASCII text matching [a-z][a-z0-9-]{0,31},
length 1..32, on entry. Set the supplied module-level ContextVar and reset its
token in finally, preserving parent/default on normal and exceptional exit.
A scope must enter/exit in the same context. Make fresh scopes for nesting/reuse.
It is request metadata, not authentication/authorization or a global mutable
registry. Async tasks capture their current context at creation; later parent
changes do not rewrite that child. Values are shallow references, not deep copies.
Place the request scope outside resource scopes if cleanup needs its label.

WeakRegistry stores a WeakValueDictionary, with the same key validation.
store preserves the exact weak-referenceable value without owning its lifetime;
unsupported values raise TypeError and preserve an existing entry. Replacement
updates the current key. get performs one lookup and returns the exact value
or None. The returned reference keeps it alive while the caller holds it.
The registry never calls close. It is a lookup optimization, not an ownership,
memory-size, thread-safety or deterministic garbage-collection promise.
Explicit resource scopes own cleanup; finalizers cannot guarantee timely release.

## Work and evidence

Create a virtual environment and install the starter's development extra:

    python -m pip install -e ".[dev]"
    python -m pytest -q
    python -m mypy src/academy_resource_scopes demo.py
    python -m ruff check src tests demo.py
    python demo.py
    python -m build --no-isolation

Build with the pinned build requirements available. Install the real wheel into
a second fresh environment, with pytest/mypy separately installed. Run copies
of tests/demo outside the source tree without PYTHONPATH or editable installs.
Check pip consistency, quiet import, packaged py.typed and actual package path.
Do not expect the intentionally unfinished starter to pass runtime cases.

Add two regressions: one partial-acquisition/cleanup failure trace and one
context/weak-reference lifetime case. Record exact command output and explain
native exception chaining, callback non-suppression and cancellation limits.
Demonstrate typed composition with earlier installed records/transformations
without changing their contracts. Keep metadata outside private payload logs.

Submit code/artifact references, setup/failure traces, installed output and
self-review against the four criteria. A human reviewer assesses the explanation.
Finite public tests and reported output do not certify advanced expertise.

Public async tests use a two-second harness timeout to reject broken coordination. This test deadline is separate from the resource scope's cooperative cleanup contract. The maintained reference passes 54 public cases.
