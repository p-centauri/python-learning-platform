# ADR 0008 — Practical Python continuation and repair lab

Date: 2026-09-21
Status: accepted

## Decision
Continue the foundations path with five ordered lessons on Unicode/text boundaries, collection patterns, timestamp validation, time zones/durations and debugging. Add ten scored scenarios under a separate `Python practical fluency` skill so earlier skill denominators do not change. Existing lesson IDs, exercises, exam banks and saved attempts remain intact. Catalog version becomes `2026.09-foundation-v3`.

Provide a small, intentionally buggy event-timeline program rather than another empty scaffold. Its explicit contract requires strict UTF-8, a reporting-specific label normalization policy, offset-aware timestamps, UTC conversion, stable chronological ordering and no partial report on failure. It loads small JSON files in memory; it is not a streaming ingestion service or strict RFC 3339 validator. Named-zone teaching is separate; the lab needs no IANA data dependency.

Extend authenticated project downloads with a registry of two fixed six-file bundles. Keep both maintainer references out of the ZIPs. The app only serves authored bytes; execution, debugging and practical review happen locally. Project checkboxes remain self-reported and do not affect mastery.

## Evidence and limits
Execute trusted lesson examples, verify that the public tests detect the supplied bugs and pass against a corrected reference, and test the UI continuation/download/persistence flow. The named-zone lesson explains how to supply tzdata when missing. Passing local tests is useful review evidence, not proof of expert competence. Next teaching work is intermediate object design and typing.
