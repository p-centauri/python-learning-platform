# ADR 0021: explicit resource handoffs and scoped context lifetime

Date: 2026-10-03. Status: accepted.

## Context

Step 6 needs advanced resources after generics. Cleanup registered too late can leak partial setup; resetting labels to a default loses nested state. Weak references can be mistaken for owners. Prior package contracts and historical evidence must stay stable.

## Decision

Publish six lessons on ExitStack, cleanup/suppression outcomes, AsyncExitStack, ContextVars, weak lifetime and installed evidence. Use a separate Python resource contracts skill. Catalog 2026.10-resources-v1 adds twelve scenarios; interactive/recall/rubric content advances to v7. Exams, earlier denominators and frozen history stay unchanged.

Use academy-resource-scopes-lab 0.1.0, Python 3.13+, standard-library runtime. Five unfinished functions/methods implement owned sync/async scopes, token-restored labels and weak registry store/get. Resource/AsyncResource return transfers a value and cleanup callback. Factories own partial setup before return. Successful handoffs register immediately without an intervening await.

Validate exact limits 0..8 before touching input. Borrow a single-pass synchronous factory iterable; observe one extra factory on overflow without invoking it or fetching another. Acquire sequentially and yield one tuple after setup succeeds. Attempt callbacks once in reverse order. Returns cannot suppress; native chaining allows cleanup errors to replace earlier errors while remaining callbacks are attempted. No transaction/retry/rollback claim.

Await async release under cooperative single-cancellation tests. Repeated cancellation, stalled cleanup, forced termination and closed loops have no completion guarantee. Factories release incomplete acquisitions themselves. Public tests have a separate two-second coordination deadline to reject broken fixtures/starters; this is not a scope hard deadline.

Use a module-level ContextVar and explicit same-context token reset in finally on Python 3.13. Tasks normally capture shallow context at creation. Labels are bounded metadata, never authorization. Outer request scopes preserve labels during inner resource cleanup.

WeakRegistry uses weak values, validated keys, identity-preserving single lookup and None misses. Returned references temporarily keep values alive. Unsupported weak replacements preserve existing entries. The registry never closes values, promises no capacity/thread safety/collection timing, and is not tamper resistance. Finalizers can retain targets and cannot await async release.

The authenticated eight-file ZIP excludes references/private keys. The API serves bytes and stores manual evidence only. Trusted subprocesses verify 54 cases, strict types/lint, artifacts and installed prior-value composition. Four pinned criteria keep judgment and reported evidence distinct.

## Consequences and limits

One bounded unit is complete; step 6, advanced practical assessment and expertise remain open. A tuple of closed external handles does not extend their validity. Concurrency, measured performance/cache/library evolution, persistence and applied AI remain next. No migration or academy runtime dependency changes. CI is configured; remote execution is unobserved.

References: [contextlib](https://docs.python.org/3.13/library/contextlib.html), [contextvars](https://docs.python.org/3.13/library/contextvars.html), [weakref](https://docs.python.org/3.13/library/weakref.html).
