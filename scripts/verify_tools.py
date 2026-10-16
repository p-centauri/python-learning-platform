"""Trusted four-package local tool verification; never learner-upload execution."""

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
LAB = ROOT / "content/projects/tools"
PACKAGES = [
    ("model-contracts", "academy_model_contracts"),
    ("retrieval", "academy_retrieval"),
    ("rag", "academy_rag"),
    ("tools", "academy_tools"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-tools-") as directory:
        area = Path(directory)
        sources = []
        wheels = []
        for name, package in PACKAGES:
            source = area / name
            lab = ROOT / "content/projects" / name
            shutil.copytree(
                lab / "starter",
                source,
                ignore=shutil.ignore_patterns(
                    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "*.egg-info"
                ),
            )
            shutil.copyfile(lab / "reference/operations.py", source / "src" / package / "operations.py")
            build = checked([sys.executable, "-m", "build", "--no-isolation"], source)
            assert "Building wheel from sdist" in build.stdout
            wheels.append(next((source / "dist").glob("*.whl")))
            sources.append(source)
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
        checked(install + [str(wheel) for wheel in wheels] + ["pytest==9.0.3", "mypy==2.3.1"], outside, env)
        checked([str(python), "-I", "-m", "pip", "check"], outside, env)
        for _, package in PACKAGES:
            quiet = checked([str(python), "-I", "-c", f"import {package}"], outside, env)
            assert quiet.stdout == quiet.stderr == ""
            probe = checked(
                [
                    str(python),
                    "-I",
                    "-c",
                    f"from importlib.resources import files; import {package}; assert files('{package}').joinpath('py.typed').is_file(); print({package}.__file__)",
                ],
                outside,
                env,
            )
            assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
            checked([str(python), "-I", "-m", "mypy", "--strict", "-p", package], outside, env)
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        checked([str(python), "-I", "-m", "mypy", "--strict", "demo.py"], outside, env)
        tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
        assert "81 passed" in tests.stdout and "skipped" not in tests.stdout
        print(tests.stdout, end="")
        # Exercise the same maintained source with installed dependency metadata available.
        source_env = dict(env)
        source_env["PYTHONPATH"] = os.pathsep.join(str(p / "src") for p in sources)
        source_tests = checked([str(python), "-m", "pytest", "-q", "tests"], sources[-1], source_env)
        assert "81 passed" in source_tests.stdout and "skipped" not in source_tests.stdout
        print("SOURCE: " + source_tests.stdout, end="")
        source_env["MYPYPATH"] = source_env["PYTHONPATH"]
        checked([str(python), "-m", "mypy", "--strict", "src", "demo.py"], sources[-1], source_env)
        # Prior package public checks in this same clean installation preserve composed behavior.
        for name, expected in [
            ("model-contracts", "84 passed"),
            ("retrieval", "83 passed"),
            ("rag", "70 passed"),
        ]:
            folder = outside / (name + "-tests")
            shutil.copytree(ROOT / "content/projects" / name / "starter/tests", folder)
            previous = checked([str(python), "-I", "-m", "pytest", "-q", str(folder)], outside, env)
            assert expected in previous.stdout and "skipped" not in previous.stdout
            print(name + ": " + previous.stdout, end="")
        demo = checked([str(python), "-I", "demo.py", "--output", "tools.json"], outside, env)
        report = json.loads(demo.stdout)
        assert report == json.loads((outside / "tools.json").read_text()) and not demo.stderr
        assert report["package"] == "0.1.0" and report["fixture"] == "tools-fixture-v1"
        assert report["schema"] == "tool-proposals-v1" and report["store"] == "tool-store-v1"
        assert report["dependencies"] == dict(model="0.1.0", retrieval="0.1.0", rag="0.1.0")
        examples = report["examples"]
        assert len(examples) == 17
        assert examples["normal"]["report"]["stopped"] == "finished"
        assert examples["normal"]["notes_receipts"] == [1, 1] and examples["normal"]["requests"] == 3
        assert examples["duplicate-new-id"]["notes_receipts"] == [1, 1]
        assert examples["duplicate-new-id"]["report"]["steps"][1]["outcome"]["replayed"]
        for name in ["cost-blocked", "context-blocked"]:
            assert examples[name]["requests"] == 0 and examples[name]["notes_receipts"] == [0, 0]
        for name in [
            "unknown-tool",
            "extra-authority",
            "permission-change",
            "source-change",
            "unapproved-change",
        ]:
            assert examples[name]["notes_receipts"] == [0, 0]
        late = examples["tool-after-timeout"]
        assert late["report"]["stopped"] == "tool_timeout" and late["cleanup"]
        assert late["notes_receipts"] == late["after_replay_notes_receipts"] == [1, 1]
        assert late["explicit_replay"]["replayed"]
        cancel = examples["external-cancellation"]
        assert cancel["propagated"] and cancel["cleanup"] and cancel["notes_receipts"] == [1, 1]
        assert cancel["replay"] == "replayed" and not cancel["durable_provider_cost_ledger"]
        assert "controlled-private-error" not in demo.stdout and "Release the file" not in demo.stdout
        if args.report_output:
            args.report_output.parent.mkdir(parents=True, exist_ok=True)
            args.report_output.write_text(json.dumps(report, indent=2) + "\n")
            assert json.loads(args.report_output.read_text()) == report
    print(
        "PASS: four archive/wheel installs, quiet typed imports, 81 installed/source tool cases, 84 model/83 retrieval/70 RAG cases, exact authority/approval, atomic local receipts, stable-ID replay, bounded whole-loop deadline, uncertain committed effects/cancellation and computed saved JSON. Controlled local tools are not real model quality or distributed exactly-once."
    )


if __name__ == "__main__":
    main()
