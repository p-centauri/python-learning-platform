"""Compute actual finite rankings; import stays quiet and never accesses a provider."""

import argparse
from dataclasses import asdict, replace
from importlib.metadata import version
import json
from pathlib import Path
from academy_retrieval import evaluate, retrieve
from academy_retrieval.dataset import load_fixture


def run() -> dict[str, object]:
    data = load_fixture()
    results = [
        asdict(evaluate(data.chunks, data.cases, k=k, mode=mode))
        for mode in ("cosine", "lexical")
        for k in (1, 3)
    ]
    example = data.cases[0]
    refused = False
    try:
        retrieve(
            data.chunks, replace(example.query, spec=replace(data.spec, version="other")), example.principal
        )
    except ValueError:
        refused = True
    assert refused
    for case in data.cases:
        hits = retrieve(data.chunks, case.query, case.principal, case.filters)
        assert hits == retrieve(tuple(reversed(data.chunks)), case.query, case.principal, case.filters)
        assert all(hit.key.tenant == case.principal.tenant for hit in hits)
        assert all(hit.key.document not in {"private-admin", "inactive"} for hit in hits)
    assert results[0]["answerable"] == 7 and results[0]["no_labels"] == 2
    return {
        "package": version("academy-retrieval-lab"),
        "dataset": data.version,
        "spec": asdict(data.spec),
        "chunks": len(data.chunks),
        "queries": len(data.cases),
        "model_mismatch_refused": refused,
        "stable_scoped_rankings": True,
        "scope": "Original development fixture, hand-supplied vectors; no model, network, ANN, held-out quality or automatic mastery",
        "evaluations": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run()
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
        assert json.loads(args.output.read_text()) == json.loads(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
