# ADR 0009 — Python object design and typing

Date: 2026-09-21
Status: accepted

## Decision
Publish five ordered lessons after the existing ownership lesson: classes/state, dataclasses, composition, type hints/input validation and protocols/testing with fakes. Keep explanations simple and separate static guarantees from runtime behavior. Use a new `Python object design` skill so old practice denominators and saved exam definitions remain unchanged. Catalog revision is `2026.09-objects-v1`.

The local task-inbox project has a frozen validated value, a parser accepting `object`, an injected storage protocol and a per-instance memory store. Its contract is deliberately bounded: no network, database, concurrency or persistence guarantees. It includes 14 runtime tests, a positive typed usage fixture and instructions for a deliberately incompatible store. Checklists remain self-report; the API serves authored bytes and never runs learner code.

Add a third fixed six-file starter bundle to the authenticated registry. Keep the corrected reference outside the download. Verify the reference and all five trusted lesson examples with runtime checks and strict mypy. Verify that the intentionally incompatible protocol is rejected. This prevents a typing lesson from relying on untested signatures.

Pin mypy 2.3.1 in backend development requirements so CI's existing test command also verifies authored Python teaching material. It is not an API runtime dependency. The downloadable project's README pins the same tool; its runtime only uses the standard library. Future updates must rerun both passing and intentionally failing fixtures before changing the pin.

## Limits and follow-up
A clean type check can accept a function that raises NotImplementedError. Runtime behavior, static checks and human design review are distinct evidence. Full intermediate coverage is unfinished; next teach iterators/generators and resource cleanup as the foundation of the planned streaming ingestion project.
