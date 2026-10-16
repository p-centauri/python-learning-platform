# Model contracts lab

Implement `build_request`, `decode_reply` and async `run` in operations.py. Complete scaffold and **84 public cases** are supplied. Maintained solutions are excluded. The two provider formats are invented fixtures; no real model, SDK, network request, credential or paid account is required.

## Install and check

Use Python 3.13. After implementing the functions:

```sh
python -m pip install -e '.[dev]'
python -m pytest -q tests
python -m mypy --strict src/academy_model_contracts demo.py
python -m build
```

Build creates a source archive and a wheel from that archive. Install the wheel in a new environment outside the checkout, then copy tests/ and demo.py there:

```sh
python -m venv .venv
.venv/bin/python -m pip install '/absolute/path/academy_model_contracts_lab-0.1.0-py3-none-any.whl' 'pytest==9.0.3' 'mypy==2.3.1'
.venv/bin/python -m pip check
.venv/bin/python -I -m pytest -q tests
.venv/bin/python -I -m mypy --strict -p academy_model_contracts
.venv/bin/python -I -m mypy --strict demo.py
.venv/bin/python -I demo.py --output model-contracts.json
```

The runtime uses the standard library. Pytest, mypy, Ruff and build are development tools. No provider dependency is introduced into the academy API. The app serves authored starter bytes and stores reported/manual evidence; it never executes your package or its test command.

## Implement the boundary

MODEL_CONTRACT.md gives the exact fixture shapes and limits. Keep configured provider, model revision, prompt version and schema identity separate from user text. A request snapshots configuration and serializes all instructions, schema, model fields and user text. The fixture counts complete UTF-8 request bytes as input units, then reserves configured output units inside context. This is deliberately not a real tokenizer or a universally conservative token estimate. Do not truncate silently or claim a provider context guarantee.

Normalize the two different fixture envelopes into one frozen Reply. Validate bounded UTF-8 bytes, duplicate-free JSON, exact model/variant/usage fields and triage domain values. A complete proposal has exactly queue, summary and needs_human. Refusal and incomplete output never produce a Decision; do not repair fenced JSON or execute generated instructions. Shape/domain validity still cannot establish truth, ownership or permission.

The finite run accepts at most eight prompts, checks all requests before any call, then admits at most max_steps attempts. Before each attempt reserve input-bound and maximum-output fictional credits. Settle to bounded provider-reported usage only after the whole reply validates. Refused/incomplete replies have known usage but stop the run. Timeout, provider failure and invalid response keep the full reservation and stop; unknown usage is never free. No automatic retry is provided. Fresh runs have independent local ledgers, not durable billing/account quotas.

One monotonic cooperative time budget covers the provider-call loop; it is not reset per call. Timeout awaits cooperative cancellation cleanup. External cancellation propagates; the caller must handle durable reconciliation, since this local run produces no saved ledger when cancelled. Clients/transports stay borrowed. Blocking, cancellation-suppressing or slow cleanup code cannot be forcibly stopped. Preflight, synchronous parsing and arbitrary transport buffering are not hard interrupted.

## Evidence and independent review

The installed demo records both adapters, complete/refused/incomplete/wrong-model/malformed/provider-error/cost-blocked/step-limited results, an actual waiting-call timeout and external cancellation with observed cleanup. It saves versioned JSON without prompt text, raw refusal reasons or raw exception details. Test spies capture exact wire bytes; that is a local fixture, not a production logging policy. The outputs are predetermined; no semantic accuracy, real-provider conformance, current pricing or factual quality is measured.

Add your own regression and design note. Predict a context or reservation edge, explain unknown usage after an uncertain call, and demonstrate a malformed proposal or cancellation case not merely copied from a public fixture. Report real commands, exact revision/package versions, installed JSON, failures and limits. Submit the fixed artifact through the in-app Model contracts project; self/human review stays separate from objective mastery. Never attach secrets or real user text. Real provider adapters/tokenizers/billing, retries/durable quotas, retrieval, tools and adversarial release evaluation belong to later work.
