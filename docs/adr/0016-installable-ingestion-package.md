# ADR 0016 — installable ingestion package and managed HTTP practice

Date: 2026-10-01. Status: accepted.

## Context

The published Python path taught typed boundaries, lazy file processing and owned/borrowed cleanup, but lacked package installation and HTTP practice. Step 6 connects these skills to later backend and applied AI ingestion. Existing scenario, recall, guided and project histories must remain meaningful.

## Decision

Publish eight authored lessons and a bounded intermediate package lab. Use a src layout, pyproject metadata, package resources/typing marker and two installed CLI forms. HTTPX 0.28.1 is the declared runtime dependency; build/tool versions are stated and tested. Maintainer verification builds wheel and sdist, installs the wheel with runtime dependencies into a fresh environment, then runs the actual tests and commands outside the source tree. Normal API tests build without network; the separate clean-install verifier needs the configured package index or an explicit offline wheelhouse. CI is configured for both, but remote CI results remain unobserved.

The parser borrows chunk input and retains at most one bounded line. The HTTP context borrows its client and owns its streamed response. Explicit limits are 1,024 line bytes excluding LF, 8,192 actual body bytes and 256-byte raw HTTP chunks. Missing/identity encoding only avoids confusing compressed and decoded limits. Status 200 and NDJSON media are explicit; redirects and silent retries are excluded. The CLI owns a finite-timeout client and publishes success only after full consumption/cleanup. Per-operation timeouts are not a total deadline.

The URL rules are syntax restrictions, not SSRF protection. Only trusted configured destinations are within this lab's use. Later server-side fetchers must design destination/DNS/network isolation and total deadlines before accepting untrusted URLs. No learner code, test command, repository reference or package is executed by the academy API. Public tests use a fake transport and observable streams; they do not claim real DNS/TLS/deployment verification.

Downloads use the existing authenticated fixed-file registry, with exactly 13 authored starter files. Maintainer references and answer banks stay excluded. A new Python ingestion skill contains only the new scenarios, preserving previous skill denominators. New interaction/recall/rubric content versions add stable IDs; old submitted snapshots are not changed. Four rubric criteria use the existing manual review/revision workflow; reported tests never become an automatic practical grade or mastery award.

## Consequences

There are now 46 published lessons, including 33 Python lessons, and eight projects. This completes one packaging/HTTP module, not all step 6 or a full expert Python course. Async work, PostgreSQL writes, idempotent retries, services/workers and applied AI continuation remain explicit planned units in STEP_6_PATHS.md. A clean installation is separate evidence from lint, type checks, runtime behavior and human review.

## Sources

- [PyPA project metadata](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) and [src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/).
- [HTTPX clients](https://www.python-httpx.org/advanced/clients/), [timeouts](https://www.python-httpx.org/advanced/timeouts/) and [fake transports](https://www.python-httpx.org/advanced/transports/).
- Dependency fixes were selected using the actual pip-audit output, [PyPA setuptools advisory](https://github.com/pypa/advisory-database/blob/main/vulns/setuptools/PYSEC-2026-3447.yaml) and [wheel release notes](https://github.com/pypa/wheel/blob/main/docs/news.rst). No known advisories is limited dependency evidence, not a security certification.
