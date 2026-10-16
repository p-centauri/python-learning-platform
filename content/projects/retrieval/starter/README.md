# Scoped retrieval lab

Implement three functions in `src/academy_retrieval/operations.py`: `make_chunks`, `retrieve`, `evaluate`. Supplied contracts, resource loader and scoring helpers are part of the exercise. Read RETRIEVAL_CONTRACT.md before changing behavior. Start after the model-contract lessons at `/lessons/retrieval-chunk-identities`.

This original development fixture has 12 document revisions, 15 chunks and nine queries: seven have relevant labels and two have none. Six-dimensional vectors are supplied by hand. There is no embedding model, provider, network, vector database or generation. Exact cosine and simple keyword Jaccard rankings use the same labels and access rules. Results measure this finite fixture only.

Python 3.13 or newer is required. Runtime uses only the standard library. Learn dataclasses, hashlib, math, re, json, importlib.resources and importlib.metadata. Development tools are pytest, mypy, Ruff, build, setuptools and wheel; versions are pinned in pyproject.toml. Later production work may need a verified embedding SDK, PostgreSQL/pgvector and ANN indexing. Those are not requirements for passing this lab.

From the completed starter:

```sh
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest -q
.venv/bin/python -m mypy --strict src demo.py
.venv/bin/python -m ruff check src tests demo.py
.venv/bin/python -m build
```

All 83 supplied cases must pass without skips. The untouched starter deliberately fails because its three functions are unfinished. Build produces a source archive and wheel. Create another virtual environment, install the wheel and pytest/mypy, then copy `tests/` and `demo.py` into an unrelated directory. Run from there with PYTHONPATH/MYPYPATH unset:

```sh
/path/to/installed/bin/python -I -m pip check
/path/to/installed/bin/python -I -m mypy --strict -p academy_retrieval
/path/to/installed/bin/python -I -m mypy --strict demo.py
/path/to/installed/bin/python -I -m pytest -q tests
/path/to/installed/bin/python -I demo.py --output retrieval.json
```

Confirm imports come from that environment, `py.typed` and `fixture.json` are installed, and importing the package prints nothing. The guarded demo computes four reports (cosine/lexical at k=1/3), records versions and scoped stable rankings, and reads the saved JSON back. Do not replace calculations with fixed scores. Review per-case hits before explaining aggregate results.

Submit exact commands/output, source revision, wheel evidence and retrieval.json through `/projects#retrieval`. Add an independently designed regression: first predict a permission/revision/ranking failure, introduce or describe a wrong implementation, then show your test catches it. Explain a chunking/threshold choice and its tradeoff. Supplied tests and reported output cannot establish originality, model quality or practical mastery. Project criteria require human/self review; the academy stores your report and never executes your uploaded code.
