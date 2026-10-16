"""Trusted offline model contract artifact checks, never learner upload execution."""

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
LAB = ROOT / "content/projects/model-contracts"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-model-contracts-") as directory:
        area = Path(directory)
        source = area / "source"
        shutil.copytree(
            LAB / "starter",
            source,
            ignore=shutil.ignore_patterns(
                "__pycache__", ".ruff_cache", ".mypy_cache", ".pytest_cache", "dist", "*.egg-info"
            ),
        )
        shutil.copyfile(LAB / "reference/operations.py", source / "src/academy_model_contracts/operations.py")
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
        quiet = checked([str(python), "-I", "-c", "import academy_model_contracts"], outside, env)
        assert quiet.stdout == quiet.stderr == ""
        probe = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_model_contracts; assert files('academy_model_contracts').joinpath('py.typed').is_file(); print(academy_model_contracts.__file__)",
            ],
            outside,
            env,
        )
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        checked([str(python), "-I", "-m", "mypy", "--strict", "-p", "academy_model_contracts"], outside, env)
        checked([str(python), "-I", "-m", "mypy", "--strict", "demo.py"], outside, env)
        tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
        assert "84 passed" in tests.stdout and "skipped" not in tests.stdout
        print(tests.stdout, end="")
        demo = checked([str(python), "-I", "demo.py", "--output", "model-contracts.json"], outside, env)
        report = json.loads(demo.stdout)
        assert report == json.loads((outside / "model-contracts.json").read_text()) and not demo.stderr
        assert report["package"] == "0.1.0" and report["context_overflow_refused"]
        assert "no network or model" in report["transport"] and "fictional" in report["accounting"]
        examples = report["examples"]
        assert len(examples) == 11
        for dialect in ["message-v1", "completion-v1"]:
            entry = examples[dialect]
            assert entry["fixture_only"] and entry["requests"] == 2
            assert entry["report"]["stopped"] == "finished" and entry["report"]["charged"] == 240
            assert len(entry["report"]["steps"]) == 2
        for name, kind in [
            ("refusal", "refused"),
            ("incomplete", "incomplete"),
            ("malformed", "invalid_response"),
            ("provider-error", "provider_error"),
            ("wrong-model", "invalid_response"),
        ]:
            entry = examples[name]
            assert entry["requests"] == 1 and entry["report"]["stopped"] == kind
            step = entry["report"]["steps"][0]
            assert step["decision"] is None
            if kind in ("invalid_response", "provider_error"):
                assert step["usage"] is None and step["charged"] == step["reserved"] > 120
        assert (
            examples["cost-blocked"]["requests"] == 0 and examples["cost-blocked"]["report"]["charged"] == 0
        )
        assert (
            examples["step-limited"]["requests"] == 2
            and examples["step-limited"]["report"]["stopped"] == "step_limit"
        )
        assert (
            examples["timeout"]["cleanup_awaited"] and examples["timeout"]["report"]["stopped"] == "timeout"
        )
        assert examples["external-cancellation"] == dict(
            propagated=True, cleanup_awaited=True, requests=1, durable_ledger=False
        )
        assert "private-fixture-marker" not in demo.stdout
        if args.report_output:
            args.report_output.parent.mkdir(parents=True, exist_ok=True)
            args.report_output.write_text(json.dumps(report, indent=2) + "\n")
            assert json.loads(args.report_output.read_text()) == report
    print(
        "PASS: source archive/wheel, clean installed imports/types, 84 public cases, two offline adapters, strict outcomes, budget/deadline/cancellation JSON evidence and owned temporary cleanup. No provider/model/network behavior claimed."
    )


if __name__ == "__main__":
    main()
