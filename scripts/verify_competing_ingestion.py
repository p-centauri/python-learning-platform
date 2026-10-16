"""Trusted installed competition evidence on owned PostgreSQL; never learner-code execution."""

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
LAB = ROOT / "content/projects/competing-ingestion"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-competition-artifacts-") as directory:
        area = Path(directory)
        wheels = []
        for name, package, references in [
            ("ingestion-service", "academy_ingestion_service", ["auth.py", "service.py"]),
            ("competing-ingestion", "academy_competing_ingestion", ["retry.py", "reconcile.py"]),
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
        quiet = checked([str(python), "-I", "-c", "import academy_competing_ingestion"], outside, env)
        assert quiet.stdout == quiet.stderr == ""
        probe = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_competing_ingestion; assert files('academy_competing_ingestion').joinpath('py.typed').is_file(); assert files('academy_ingestion_service').joinpath('migrations/versions/002_observed_at.py').is_file(); print(academy_competing_ingestion.__file__)",
            ],
            outside,
            env,
        )
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        for filename in ["pyproject.toml", "demo.py"]:
            shutil.copyfile(LAB / "starter" / filename, outside / filename)
        checked([str(python), "-I", "-m", "mypy", "--strict", "demo.py"], outside, env)
        with disposable_postgres() as dsn:
            env["ACADEMY_COMPETITION_DSN"] = dsn
            tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
            assert "70 passed" in tests.stdout and "skipped" not in tests.stdout, tests.stdout
            print(tests.stdout, end="")
            demo = checked([str(python), "-I", "demo.py", "--output", "competition.json"], outside, env)
            report = json.loads(demo.stdout)
            assert report == json.loads((outside / "competition.json").read_text()) and demo.stderr == ""
            assert report["schema"] == "2026.10-competition-v1" and report["server_version"] // 10000 == 17
            assert report["races"] == [
                {"wait_observed": True, "holder": "committed", "challenger": "duplicate", "stored_value": 5},
                {"wait_observed": True, "holder": "committed", "challenger": "conflict", "stored_value": 5},
                {"wait_observed": True, "holder": "rolled-back", "challenger": "inserted", "stored_value": 5},
                {"wait_observed": True, "holder": "rolled-back", "challenger": "inserted", "stored_value": 9},
            ]
            assert report["snapshots"] == [
                {"isolation": "READ COMMITTED", "before": 0, "during": 1, "after": 1},
                {"isolation": "REPEATABLE READ", "before": 0, "during": 0, "after": 1},
            ]
            assert sorted(report["serializable"]["outcomes"]) == ["40001", "committed"]
            assert (
                report["serializable"]["fresh_count"] == 1
                and report["serializable"]["fresh_decision"] == "skip-already-admitted"
            )
            assert report["deadlock"] == {
                "observed_sqlstates": ["40P01"],
                "attempts": [1, 2],
                "inserted": [0, 2],
                "duplicates": [0, 2],
                "stored": [["a", 5], ["b", 10]],
            }
            assert report["lock_timeout"] == {
                "sqlstate": "55P03",
                "stored_count": 0,
                "attempts": 1,
                "automatic_retry": False,
            }
            assert report["statement_timeout"] == {"sqlstate": "57014", "transaction_idle": True}
            assert report["inflight_reconciliation"] == {
                "before_commit": "missing",
                "after_commit": "complete",
            }
            assert (
                report["modeled_loss"]["attempts"] == report["modeled_loss"]["calls"] == 1
                and report["modeled_loss"]["reconciliation"] == "complete"
            )
            assert (
                report["previous_api"]["unauthorized"] == 401
                and report["previous_api"]["forbidden"] == 403
                and report["previous_api"]["allowed"] == 200
            )
            assert report["previous_api"]["items"] == [{"id": "a", "revision": 1, "value": 0}]
            assert (
                report["local_settings_reset"] == {"lock_timeout": "0", "statement_timeout": "0"}
                and report["checked_out_connections"] == 0
            )
            if args.report_output:
                args.report_output.write_text(json.dumps(report, indent=2) + "\n")
                assert json.loads(args.report_output.read_text()) == report
    print(
        "PASS: two source/wheel builds, fresh installed resources/quiet import/types, 70 PostgreSQL cases, actual wait/snapshot/40001/40P01/55P03/57014/reconciliation JSON and previous-service permissions. Modeled acknowledgment loss is labeled. Owned resources removed; no learner execution."
    )


if __name__ == "__main__":
    main()
