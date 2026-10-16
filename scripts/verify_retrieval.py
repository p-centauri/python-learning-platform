"""Trusted offline retrieval contract artifact checks, never learner upload execution."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import venv
from verify_ingestion_package import checked

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "content/projects/retrieval"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-retrieval-") as directory:
        area = Path(directory)
        source = area / "source"
        shutil.copytree(
            LAB / "starter",
            source,
            ignore=shutil.ignore_patterns(
                "__pycache__", ".ruff_cache", ".mypy_cache", ".pytest_cache", "dist", "*.egg-info"
            ),
        )
        shutil.copyfile(LAB / "reference/operations.py", source / "src/academy_retrieval/operations.py")
        build = checked([sys.executable, "-m", "build", "--no-isolation"], source)
        assert "Building wheel from sdist" in build.stdout
        wheel = next((source / "dist").glob("*.whl"))
        environment = area / "installed"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        outside = area / "outside"
        outside.mkdir()
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"PYTHONPATH", "PYTHONHOME", "MYPYPATH"} and not k.startswith("ACADEMY_")
        }
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        install = [str(python), "-m", "pip", "install"]
        if args.wheelhouse:
            install += ["--no-index", "--find-links", str(args.wheelhouse.resolve())]
        checked(install + [str(wheel), "pytest==9.0.3", "mypy==2.3.1"], outside, env)
        checked([str(python), "-m", "pip", "check"], outside, env)
        quiet = checked([str(python), "-I", "-c", "import academy_retrieval"], outside, env)
        assert quiet.stdout == quiet.stderr == ""
        probe = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_retrieval; assert files('academy_retrieval').joinpath('py.typed').is_file(); assert files('academy_retrieval').joinpath('fixture.json').is_file(); print(academy_retrieval.__file__)",
            ],
            outside,
            env,
        )
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        checked([str(python), "-I", "-m", "mypy", "--strict", "-p", "academy_retrieval"], outside, env)
        checked([str(python), "-I", "-m", "mypy", "--strict", "demo.py"], outside, env)
        tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
        assert "83 passed" in tests.stdout and "skipped" not in tests.stdout
        print(tests.stdout, end="")
        demo = checked([str(python), "-I", "demo.py", "--output", "retrieval.json"], outside, env)
        report = json.loads(demo.stdout)
        assert report == json.loads((outside / "retrieval.json").read_text()) and not demo.stderr
        assert report["package"] == "0.1.0" and report["dataset"] == "retrieval-fixture-v1"
        assert report["chunks"] == 15 and report["queries"] == 9
        assert report["model_mismatch_refused"] and report["stable_scoped_rankings"]
        assert "hand-supplied" in report["scope"] and "held-out" in report["scope"]
        evaluations = report["evaluations"]
        assert [(e["mode"], e["k"]) for e in evaluations] == [
            ("cosine", 1),
            ("cosine", 3),
            ("lexical", 1),
            ("lexical", 3),
        ]
        for entry in evaluations:
            assert entry["cases"] == 9 and entry["answerable"] == 7 and entry["no_labels"] == 2
            assert entry["unwanted_returns"] == min(entry["k"], 2)
            assert all(r["recall"] is None and r["reciprocal_rank"] is None for r in entry["results"][-2:])
            assert entry["results"][5]["hits"][0]["key"]["revision"] == 2
            assert entry["results"][6]["hits"][0]["key"]["tenant"] == "beta"
            assert entry["results"][7]["hits"] == []
            assert all(
                h["key"]["document"] not in {"private-admin", "inactive"}
                for r in entry["results"]
                for h in r["hits"]
            )
        assert evaluations[0]["results"][0]["hits"][0]["key"]["document"] == "python-errors"
        assert evaluations[2]["results"][0]["hits"][0]["key"]["document"] == "python-types"
        assert evaluations[0]["mrr_answerable"] > evaluations[2]["mrr_answerable"]
        assert "Administrator-only policy" not in demo.stdout
        if args.report_output:
            args.report_output.parent.mkdir(parents=True, exist_ok=True)
            args.report_output.write_text(json.dumps(report, indent=2) + "\n")
            assert json.loads(args.report_output.read_text()) == report
    print(
        "PASS: source archive/wheel, clean installed imports/types/resources, 83 public cases, scoped exact/lexical rankings, four computed reports and saved JSON readback. Hand-supplied fixture vectors do not establish real model quality."
    )


if __name__ == "__main__":
    main()
