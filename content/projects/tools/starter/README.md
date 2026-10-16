# Authorized local tools lab

Complete `decode_proposal`, `execute` and async `run` in `src/academy_tools/operations.py`. Read TOOL_CONTRACT.md first. The untouched starter deliberately raises NotImplementedError. Supplied value types, SQLite transaction helper, strict JSON helpers, controlled providers and async tool hooks remain part of the exercise. Maintained solutions are outside the download.

The model can propose only `source_excerpt` or `save_note`. The application supplies the actor, tenant/group principal, selected exact RAG citations, stable operation ID and approval for one concrete note action. Proposal IDs never grant authority or choose retry identity. Refresh authority and current source before effects and before reusing evidence. Unknown tools, extra tenant/role/URL fields and changed approved parameters are rejected.

Python 3.13 or newer is required. Learn asyncio, dataclasses/typing, json, hashlib, pathlib and sqlite3, plus pytest/mypy/Ruff/build/setuptools/wheel for development. Runtime depends on the completed `academy-rag-lab==0.1.0`, which composes the model and retrieval packages. This lab has no provider account, real model, network tool, shell command, arbitrary path, financial action or academy API execution.

Complete and build the published model, retrieval and RAG labs first. Then install their actual wheels alongside this project:

```sh
python -m venv .venv
.venv/bin/python -m pip install /path/to/model.whl /path/to/retrieval.whl /path/to/rag.whl '.[dev]'
.venv/bin/python -m pytest -q
.venv/bin/python -m mypy --strict src demo.py
.venv/bin/python -m build
.venv/bin/python demo.py --output tools.json
```

Use separate local paths for the source index and note/receipt database; never choose the academy database. Construction is quiet and initialization is explicit. SQLite publication and note commits own/close their connections; no transaction spans a provider/tool wait. A local note and its receipt commit together. The scoped application operation ID survives a result being lost or a new model call ID. Same canonical action replays the receipt; changed action conflicts even when newly approved. Replays still require fresh source access and exact approval.

The loop has one cooperative deadline, configured context/cost/step limits, bounded local note counts and no automatic retry of uncertain tools. A tool can commit and then time out while returning its result. The demo observes this with actual storage/waits/cleanup and explicitly reconciles against the receipt after reopen. External cancellation propagates; a committed note remains. Local atomicity is not distributed exactly-once, permanent permission or a durable provider billing ledger.

Submit source/wheel revision, commands/output, tools.json, an original predicted regression and one approval/replay/deadline tradeoff at `/projects#tools`. The four criteria are self/human assessment; uploaded code is never executed by the academy. Finite tests and reported output do not establish originality, real model competence, production safety or mastery.
