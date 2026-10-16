# ADR 0020: typed transformations with separate runtime and checker evidence

Date: 2026-10-03. Status: accepted.

## Context

Step 6 needs advanced generics and typed interface teaching after object behavior. Type annotations alone can look complete while unfinished code still fails at runtime. Prior ingestion/policy/async/object contracts must remain usable, and learner code must stay outside the API.

## Decision

Publish seven ordered lessons on generic input/output relationships, covariance/contravariance/invariance, ParamSpec wrappers, overloads, TypeGuard/TypeIs narrowing, object/cast/runtime boundaries and useful structural library interfaces. Use a separate `Python typed interfaces` skill so old scenario denominators remain stable. Catalog `2026.10-typing-v1` adds 14 scenarios; interactive/recall/rubric content advances to v6. Exams and frozen historical evidence retain their definitions.

Use `academy-typed-transforms-lab` 0.1.0, Python 3.13+, with standard-library runtime. Four unfinished functions preserve generic T/U mapping, Callable[P,R] call shapes, optional/default overloads and validated Row construction. Supplied protocols expose read-only producer and consuming interfaces. A structural TypeGuard is distinct from domain validation; exact built-in string/integer fields and frozen Rows provide stable ordinary values without claiming tamper resistance or concurrent-mutation safety.

Mapping validates limit/callability before input acquisition, accepts 0..64 elements and observes only one extra on overflow without mapping it. It consumes borrowed input once, propagates failures without retries or partial returns and does not close the caller's iterator. A tuple is not deep immutability, and count limits cannot stop blocked code.

The observer wrapper uses wraps plus ParamSpec, forwards one target call and preserves exact result/BaseException identity with a reliable observer. Fixed started/returned/raised events contain no arguments or exception text. Observer failures deliberately propagate with documented before/after-effect behavior. Returned means the synchronous invocation returned its object, not that a generator/awaitable later completed. Async observation/retry/rollback behavior would require another contract.

The public lab separates 47 runtime cases from one positive assert_type file and ten deliberately rejected checker fixtures. Each rejection requires exactly its intended diagnostic with the real package available, not any nonzero exit. The fixture checker inspects source and never executes those snippets. Mypy 2.3.1 is pinned for diagnostic reproducibility; an unfinished correctly annotated starter can pass these static fixtures while failing runtime tests.

The authenticated starter uses an eleven-file allowlist, including public runtime/checker fixtures and excluding references/private academy definitions. The API serves bytes and stores manual evidence only. Trusted maintainer subprocesses build/install artifacts outside source and verify a strict-typed offline adapter from earlier installed Records into transformations and prior Snapshots without changing their contracts. Four pinned manual criteria cover type relationships, call phases, validated boundaries and actual separate evidence.

## Consequences and limits

This finishes a bounded typing unit, not step 6, the full advanced practical assessment or expertise. TypeIs requires an honest all-and-only compatible target; neither guards, casts, TypedDict nor NewType validate or authorize by annotation. Mutable aliases and external input still need runtime/ownership decisions. Context/resource lifetime, threads/processes/build-specific GIL, measured profiling/cache/library evolution, persistence and applied AI paths remain open. No schema migration or academy runtime dependency change is needed. CI includes the trusted installer; remote execution remains unobserved.

References: [typing](https://docs.python.org/3.13/library/typing.html), [generics specification](https://typing.python.org/en/latest/spec/generics.html), [callables](https://typing.python.org/en/latest/spec/callables.html), [type narrowing](https://typing.python.org/en/latest/spec/narrowing.html).
