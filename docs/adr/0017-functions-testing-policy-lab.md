# ADR 0017: separate feed policy and observable testing lab

Date: 2026-10-02. Status: accepted.

## Context

Step 6 needs function behavior and testing depth before bounded async work. The published synchronous ingestion package already has a precise parser/HTTP contract. Adding filter configuration or diagnostic behavior inside that parser would change the earlier exercise and its installed interface.

## Decision

Publish seven ordered lessons and a separately packaged `academy-feed-policy-lab` v0.1.0. It uses read-only `Reading` properties and a precise `Report` TypedDict; the previous frozen ingestion `Record` satisfies the protocol structurally. A small typed adapter connects the previous summary return annotation. The policy borrows input and leaves acquisition/closure with the HTTP owner.

Use a factory for independent prefix/minimum closures, explicit positional/keyword boundaries, a `functools.wraps` reporter wrapper and a bounded ASCII `re.fullmatch` rule with separate numeric validation. The wrapper forwards once, preserves result and exception identity, and emits allowlisted events through an injected logger. No raw payloads, totals, URLs, exception bodies or tracebacks are logged. Ordinary failures and process interrupts remain distinct. A reliable configured logger and valid reporter output are explicit bounded-contract assumptions; general ParamSpec decorators remain advanced planned work.

Runtime uses only the standard library. Pytest 9.0.3 is a pinned development dependency, alongside existing mypy/Ruff/build tooling. Public tests cover fixtures/yield cleanup, meaningful parametrized boundaries, patching the lookup site, actual captured records and late failures. The authenticated starter is a fixed nine-file allowlist; maintained reference and answer banks are excluded. Maintainer verifiers execute trusted authored code in temporary subprocesses, including real wheel/source-archive builds, a fresh installed environment and offline HTTPX transport composition. The API never executes learner uploads.

Catalog `2026.10-functions-v1` uses a new `Python functions & testing` skill. Existing scenario definitions/denominators and exams are unchanged. Interactive/recall definitions advance to v3, and project rubrics to `2026.10-project-review-v3`. Fixed submitted history retains its own snapshots. Four manual project criteria assess supplied evidence; neither reported tests, checklists nor reviews award mastery.

## Consequences and limits

The module provides useful intermediate practice with simple explanations and runnable typed examples. It does not complete async/advanced Python, PostgreSQL persistence, backend or applied AI paths. Finite tests do not establish expertise, regex safety for arbitrary patterns, reliable production logging or authorization. Clean installation needs a package index unless a complete wheelhouse is supplied. CI is configured but remote runs need their own evidence.

Sources: [Python wraps](https://docs.python.org/3.13/library/functools.html#functools.wraps), [argument boundaries](https://docs.python.org/3.13/tutorial/controlflow.html#special-parameters), [logging](https://docs.python.org/3.13/library/logging.html), [fullmatch](https://docs.python.org/3.13/library/re.html#re.fullmatch), [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html), [parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html), [monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html), [pytest 9.0.3 distribution](https://pypi.org/project/pytest/9.0.3/).
