# ADR 0010 — Python streaming and resource lifetime

Date: 2026-09-21
Status: accepted

## Decision
Continue object design with five lessons on iterators, generators, streaming pipelines, error causes and context managers. Add ten scored scenarios under a separate `Python streaming` skill to keep previous skill denominators and exam snapshots unchanged. Catalog revision is `2026.09-streaming-v1`.

Use a local service-log summary as the bounded practical project. Each line is a UTF-8 JSON record, at most 1024 bytes including the terminator. A binary reader requests at most limit + 1 bytes to detect oversized input before loading a full line. Validate a fixed set of three service kinds and integer durations, retaining only a current record and group totals. Integer counters can grow; do not claim literally fixed memory bytes or a universal benchmark.

Separate a borrowed-input parser from the context owning its file. The parser is lazy and never closes caller-owned input. The context closes its parser and file after full consumption, unused input, early stop and errors. The CLI emits success only after complete consumption and cleanup. Preserve decoding/JSON causes with line context; propagate upstream I/O failures.

Add the fourth authenticated fixed six-file ZIP bundle. Reference code stays outside the download. No learner execution, result ingestion or practical grade is added. Runtime behavior is tested locally, and trusted examples/reference code also receive strict mypy verification with the existing development tool.

## Scope and follow-up
The project is a synchronous local file pipeline, not the complete ingestion package. HTTP transport, retries, persistence, packaging, concurrency and async cleanup remain separate work. Next build packaging/workflow lessons and an installable package before managed HTTP ingestion. Public tests and self-reported milestones require human review of retained state and ownership decisions.
