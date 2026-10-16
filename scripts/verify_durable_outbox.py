"""Trusted installed outbox evidence on owned PostgreSQL; never learner-code execution."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import venv
from persistence_db import disposable_postgres
from verify_ingestion_package import checked

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "content/projects/durable-outbox"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-outbox-artifacts-") as directory:
        area = Path(directory)
        wheels = []
        for name, package, references in [
            ("ingestion-service", "academy_ingestion_service", ["auth.py", "service.py"]),
            ("competing-ingestion", "academy_competing_ingestion", ["retry.py", "reconcile.py"]),
            ("durable-outbox", "academy_durable_outbox", ["core.py"]),
        ]:
            source = area / name
            lab = ROOT / "content/projects" / name
            shutil.copytree(
                lab / "starter",
                source,
                ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"),
            )
            for filename in references:
                shutil.copyfile(lab / "reference" / filename, source / "src" / package / filename)
            built = checked([sys.executable, "-m", "build", "--no-isolation"], source)
            assert "Building wheel from sdist" in built.stdout
            wheels.append(str(next((source / "dist").glob("*.whl"))))
        environment = area / "installed"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        outside = area / "outside"
        outside.mkdir()
        env = {
            k: v
            for k, v in os.environ.items()
            if k
            not in {
                "PYTHONPATH",
                "PYTHONHOME",
                "MYPYPATH",
                "ACADEMY_SERVICE_DSN",
                "ACADEMY_SERVICE_TOKENS",
                "ACADEMY_COMPETITION_DSN",
                "ACADEMY_OUTBOX_DSN",
                "ACADEMY_OUTBOX_CHILD",
            }
        }
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        install = [str(python), "-m", "pip", "install"]
        if args.wheelhouse:
            install += ["--no-index", "--find-links", str(args.wheelhouse.resolve())]
        checked(
            install
            + wheels
            + ["pytest==9.0.3", "mypy==2.3.1", "types-psycopg2==2.9.21.20260911", "httpx==0.28.1"],
            outside,
            env,
        )
        checked([str(python), "-m", "pip", "check"], outside, env)
        quiet = checked([str(python), "-I", "-c", "import academy_durable_outbox"], outside, env)
        assert quiet.stdout == quiet.stderr == ""
        probe = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_durable_outbox; assert files('academy_durable_outbox').joinpath('py.typed').is_file(); assert files('academy_durable_outbox').joinpath('schema.sql').is_file(); assert files('academy_ingestion_service').joinpath('migrations/versions/002_observed_at.py').is_file(); print(academy_durable_outbox.__file__)",
            ],
            outside,
            env,
        )
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        for filename in ["pyproject.toml", "demo.py", "crash_worker.py"]:
            shutil.copyfile(LAB / "starter" / filename, outside / filename)
        checked([str(python), "-I", "-m", "mypy", "--strict", "demo.py", "crash_worker.py"], outside, env)
        with disposable_postgres() as dsn:
            env["ACADEMY_OUTBOX_DSN"] = dsn
            tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
            assert "67 passed" in tests.stdout and "skipped" not in tests.stdout, tests.stdout
            print(tests.stdout, end="")
            demo = checked([str(python), "-I", "demo.py", "--output", "outbox.json"], outside, env)
            report = json.loads(demo.stdout)
            assert report == json.loads((outside / "outbox.json").read_text()) and demo.stderr == ""
            assert report["schema"] == "2026.10-outbox-v1" and report["server_version"] // 10000 == 17
            stages = ["before-record-commit", "after-record-commit", "after-consume-commit"]
            before = [
                dict(records=0, outbox=0, pending=0, inbox=0, total=0, applied=0),
                dict(records=1, outbox=1, pending=1, inbox=0, total=0, applied=0),
                dict(records=1, outbox=1, pending=1, inbox=1, total=7, applied=1),
            ]
            after = dict(records=1, outbox=1, pending=0, inbox=1, total=7, applied=1)
            assert len(report["crashes"]) == 3
            for item, stage, code, state in zip(report["crashes"], stages, [71, 72, 73], before, strict=True):
                assert item == dict(
                    boundary=stage,
                    child_exit=code,
                    before_restart=state,
                    delivered_key=[stage, "a", 1],
                    after_restart=after,
                )
            assert report["stable_batch"] == dict(
                observed=3, inserted=2, duplicates=1, enqueued=2, repeat_enqueued=0
            )
            assert report["previous_api"]["unauthorized"] == 401
            assert report["previous_api"]["forbidden"] == 403 and report["previous_api"]["allowed"] == 200
            assert report["previous_api"]["items"] == [
                {"id": "a", "revision": 1, "value": 0},
                {"id": "a", "revision": 2, "value": 9},
            ]
            assert report["checked_out_connections"] == 0
            assert "worker process exits/restarts" in report["durability_scope"]
            for package in [
                "academy-ingestion-service-lab",
                "academy-competing-ingestion-lab",
                "academy-durable-outbox-lab",
            ]:
                assert report["versions"][package] == "0.1.0"
            if args.report_output:
                args.report_output.write_text(json.dumps(report, indent=2) + "\n")
                assert json.loads(args.report_output.read_text()) == report
    print(
        "PASS: three source/wheel builds, fresh installed resources/quiet import/types, 67 PostgreSQL cases, three real worker exits/replay, one local effect, actual JSON and previous-service permissions. No broker/power-loss claim. Owned resources removed; no learner execution."
    )


if __name__ == "__main__":
    main()
