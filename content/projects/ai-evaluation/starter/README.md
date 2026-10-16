# Controlled AI release evaluation lab

Complete `observe`, `measure` and `decide` in src/academy_ai_evaluation/operations.py. Read RELEASE_CONTRACT.md first. The untouched starter deliberately raises NotImplementedError. Supplied strict value/resource contracts and a real composed local harness remain part of the exercise; maintained solutions are excluded from the download.

The packaged ai-release-fixture-v1 contains 18 original development cases: four retrieval, seven RAG and seven tools. Compare raw-cosine-v1 with task-gated-v1. Both execute the published packages rather than fabricating a result table. Observe current source/permission boundaries, injected fields/roles/URLs, invalid or missing evidence, refusal, timeouts and a local tool timeout after commit. This is controlled code and hand vectors, with no provider account or network tool.

Python 3.13 or newer is required. Learn asyncio, dataclasses/typing, importlib.resources/metadata, json, hashlib, fractions, pathlib and tempfile alongside the four completed local packages. pytest/mypy/Ruff/build/setuptools/wheel support verification. No judge-model SDK is required. Do not treat local formats, lexical gating, exact excerpts or a self-reported review as real semantic quality.

Complete and build model, retrieval, RAG and tools first. Install their wheels with this project in a clean development environment:

```sh
python -m venv .venv
.venv/bin/python -m pip install /path/to/model.whl /path/to/retrieval.whl /path/to/rag.whl /path/to/tools.whl '.[dev]'
.venv/bin/python -m pytest -q
.venv/bin/python -m mypy --strict src demo.py
.venv/bin/python -m build
.venv/bin/python demo.py --output release.json
```

Use an empty owned workspace for observations and separate temporary source/note databases, never the academy database. Each case gets its own directory. The guarded demo removes its temporary databases and saves/reads back a redacted report. It records exact rational metrics with explicit positive/unlabelled denominators, actual requests/effects/digests and configured model/prompt/schema. Raw retrieval's unwanted hit fails the fixture gate; the task gate passes objective checks but keeps two semantic reviews pending. The separately named simulated regression mutates an observed permission fact; it is not another provider experiment.

Dataset, candidate and versioned gate policy are pinned. Omitted/duplicated cases, mixed candidate versions, stale reviews and changed data under the old policy fail closed. HumanReview records are separately reported judgments tied to dataset and candidate digests, with explicit reviewer/source/verdict/note; the package does not authenticate the reviewer. The demo creates no manual approvals. Exact quotations can faithfully repeat a malicious source, which is why semantic usefulness/truth needs independent human scrutiny.

Submit source/wheel versions, commands/output, release.json, an original predicted regression and an explained threshold/coverage decision at /projects#ai-evaluation. Review the ordinary and malicious-source answers explicitly. Reported tests, checklist completion and self/human feedback are not automatic mastery. The academy stores reports and never executes uploaded code. Real learned models, held-out/adversarial population coverage, deployed authority, remote effects and release operations require separate evidence.
