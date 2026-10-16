# ADR 0019: advanced object behavior with finite local contracts

Date: 2026-10-03. Status: accepted.

## Context

Step 6 requires advanced Python teaching with simple explanations, runnable reproductions and reviewed practical evidence. Existing ingestion, policy and async contracts must remain usable. A knowledge test cannot establish expertise, and the API must never execute learner packages.

## Decision

Publish six ordered lessons on default attribute lookup, descriptor ownership, cooperative MRO/super, implicit special methods, equality/hash and bounded object contracts. Include separate guided/recall layers and original scenarios under `Python object contracts`, preserving older skill denominators and all exams. Catalog is `2026.10-object-model-v1`; interactive/recall content advances to v5 and rubric content to `2026.10-project-review-v5`. Existing submitted evidence stays pinned.

Use a separate standard-library package, `academy-feed-objects-lab` 0.1.0, Python 3.13+. Five unfinished methods implement a Budget data descriptor's access/update, frozen FeedKey equality/hash and a Snapshot constructor. Descriptor configuration belongs to the shared class object; actual values belong to each Budget. Supplied name binding rejects descriptor reuse for different fields. Class access returns the descriptor; missing values raise AttributeError. Updates accept exact ints 0..64 and validate before mutation.

Key identity is two validated exact built-in ASCII strings (excluding subclasses with custom equality/hash), 1..32 characters. Equality compares both fields for the same concrete type; unsupported comparisons return NotImplemented. Hash the same fields. Do not require collision-free hashes or cross-process hash stability. Subclass extension requires its own design review. Frozen fields describe ordinary value behavior, not protection against malicious Python code.

Snapshot borrows a single-pass iterable, accepts at most 64 exact immutable Readings, rejects equal duplicate keys, and saves a tuple in observed order. Detect overflow on the 65th observation; never fetch a 66th. Do not trust reported length. Propagate input failures without returning a partial result and leave cleanup to the input owner. Supplied Sequence behavior makes length, indexing, tuple slicing, iteration and truth consistent. Count limits do not stop a blocked iterator or prove arbitrary allocation bounds.

The authenticated starter is a fixed seven-file allowlist excluding references and private definitions. The API serves bytes and stores evidence only. Maintainer subprocesses execute trusted authored examples/tests, build source/wheel artifacts, install outside source and strictly type-check/run an adapter from prior installed ingestion Records. That adapter changes neither package contract. The maintained reference passes 50 public pytest cases. Four manual criteria cover descriptor ownership, identity, sequence bounds and reproducible installed evidence including a cooperative diamond trace and property/composition tradeoffs.

## Consequences

This finishes one bounded advanced unit. It does not finish step 6, the full advanced practical assessment or expert teaching. Generics, context state, threads/processes/build-specific GIL, measured profiling/cache/library evolution, persistence and applied AI remain open. Public tests and learner-reported output have finite scope; manual judgment is separate from objective grading and mastery. No new database migration or runtime dependency is required. CI includes the trusted installer but remote execution needs observed evidence.

References: [descriptor mechanics](https://docs.python.org/3.13/howto/descriptor.html), [data model](https://docs.python.org/3.13/reference/datamodel.html), [super](https://docs.python.org/3.13/library/functions.html#super), [Sequence](https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence).
