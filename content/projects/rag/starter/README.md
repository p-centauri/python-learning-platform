# Evidence answering lab

Complete `publish`, `prepare` and async `answer` in `src/academy_rag/operations.py`. Read RAG_CONTRACT.md first. Supplied contracts, index transaction helpers, strict JSON helpers, citation resolver and controlled fixtures remain part of the exercise. The untouched starter deliberately fails with NotImplementedError.

This is a bounded extractive RAG rehearsal. It publishes complete document/vector revisions into a separate SQLite file, retrieves authorized evidence, reranks and packs whole excerpts, then calls a controlled provider proposing evidence IDs and exact whole quotes. It rejects unsupported output, abstains when evidence is missing, and refreshes permissions/source state after generation. It does not evaluate freeform entailment, truth, a real model or held-out quality. There is no answer cache, URL fetching, tool execution, ANN/vector-database index or academy runtime integration.

Python 3.13 or newer is required. Runtime uses sqlite3, asyncio, dataclasses, json, pathlib, hashlib/re via prior retrieval, and the two completed local packages `academy-retrieval-lab==0.1.0` and `academy-model-contracts-lab==0.1.0`. Learn those boundaries and pytest/mypy/Ruff/build/setuptools/wheel as development tools. No embedding/provider SDK or account is required. Production PostgreSQL, real embeddings and model integration need separate verification.

First complete/build the published retrieval and model-contract starters. Install their wheels and this project in a development environment:

```sh
python -m venv .venv
.venv/bin/python -m pip install /path/to/retrieval.whl /path/to/model_contracts.whl
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest -q
.venv/bin/python -m mypy --strict src demo.py
.venv/bin/python -m ruff check src tests demo.py
.venv/bin/python -m build
```

All 70 public cases must pass without skips. References are outside the download. Build an archive and wheel, create another clean environment and install all three completed wheels plus pytest/mypy. Copy tests and demo.py to an unrelated directory; unset PYTHONPATH/MYPYPATH and run:

```sh
/path/to/installed/bin/python -I -m pip check
/path/to/installed/bin/python -I -m mypy --strict -p academy_rag
/path/to/installed/bin/python -I -m mypy --strict demo.py
/path/to/installed/bin/python -I -m pytest -q tests
/path/to/installed/bin/python -I demo.py --output rag.json
```

Verify actual import locations, quiet imports and installed py.typed markers. The guarded demo owns temporary local index files, executes publication/update/delete/reopen and controlled generation/failure/cancellation experiments, and reads saved JSON back. Never point the lab Index at the academy database; initialization is explicit and belongs to an independently chosen local file. SQLite evidence does not establish deployed PostgreSQL operations or production concurrency.

Submit commands/output, source revision, wheel/resource evidence and rag.json through `/projects#rag`. Add an original predicted regression (for example, permissions changing during a call, a deletion marker being lost, or unsupported quoted evidence), show it catches a wrong implementation, and explain a context/gating tradeoff. The required-term gate is application-supplied task policy, not a general relevance detector. Human/self review must judge originality, semantic appropriateness and production limitations. Reading, supplied tests and reported output never automatically award practical mastery; the academy stores reports and never executes uploads.
