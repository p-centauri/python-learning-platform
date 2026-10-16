"""Actual controlled release observations; never a real model benchmark."""

import argparse, asyncio, json, tempfile
from dataclasses import asdict, replace
from fractions import Fraction
from importlib.metadata import version
from pathlib import Path
from academy_ai_evaluation import Observation, Policy, load_suite, observe, measure, decide, suite_digest


def fraction(value: object) -> dict[str, int]:
    if type(value) is not Fraction:
        raise TypeError("unsupported JSON value")
    return {"numerator": value.numerator, "denominator": value.denominator}


async def examples(directory: Path) -> dict[str, object]:
    suite = load_suite()
    runs: dict[str, object] = {}
    gated: tuple[Observation, ...] = ()
    for variant in ("raw-cosine-v1", "task-gated-v1"):
        area = directory / variant
        area.mkdir()
        rows = await observe(suite, area, variant)
        runs[variant] = {
            "observations": [asdict(o) for o in rows],
            "metrics": asdict(measure(suite, rows)),
            "verdict": asdict(decide(suite, rows)),
        }
        if variant == "task-gated-v1":
            gated = rows
    mutated = list(gated)
    mutated[4] = replace(mutated[4], unauthorized=True)
    regression = decide(suite, tuple(mutated))
    return {
        "package": version("academy-ai-evaluation-lab"),
        "dependencies": {
            name: version(dist)
            for name, dist in [
                ("model", "academy-model-contracts-lab"),
                ("retrieval", "academy-retrieval-lab"),
                ("rag", "academy-rag-lab"),
                ("tools", "academy-tools-lab"),
            ]
        },
        "dataset": suite.version,
        "purpose": suite.purpose,
        "dataset_digest": suite_digest(suite),
        "policy": asdict(Policy()),
        "runs": runs,
        "simulated_regression": {
            "kind": "mutated observation, not a new provider run",
            "verdict": asdict(regression),
        },
        "scope": "Development cases, controlled generation and hand vectors; exact local contracts and separately reported manual review. No held-out semantic quality, model judge, production authority or automatic mastery.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-ai-evaluation-demo-") as folder:
        report = asyncio.run(examples(Path(folder)))
    serialized = json.dumps(report, default=fraction, indent=2)
    if args.output:
        args.output.write_text(serialized + "\n")
        assert json.loads(args.output.read_text()) == json.loads(serialized)
    print(serialized)


if __name__ == "__main__":
    main()
