"""Trusted installed leased worker evidence on owned PostgreSQL; never learner-code execution."""

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
LAB = ROOT / "content/projects/leased-worker"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-leases-artifacts-") as directory:
        area = Path(directory)
        wheels = []
        for name, package, references in [
            ("ingestion-service", "academy_ingestion_service", ["auth.py", "service.py"]),
            ("competing-ingestion", "academy_competing_ingestion", ["retry.py", "reconcile.py"]),
            ("durable-outbox", "academy_durable_outbox", ["core.py"]),
            ("leased-worker", "academy_leased_worker", ["core.py"]),
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
                "ACADEMY_WORKER_DSN",
                "ACADEMY_WORKER_CHILD",
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
        quiet = checked([str(python), "-I", "-c", "import academy_leased_worker"], outside, env)
        assert quiet.stdout == quiet.stderr == ""
        probe = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_leased_worker; assert files('academy_leased_worker').joinpath('py.typed').is_file(); assert files('academy_leased_worker').joinpath('schema.sql').is_file(); assert files('academy_ingestion_service').joinpath('migrations/versions/002_observed_at.py').is_file(); print(academy_leased_worker.__file__)",
            ],
            outside,
            env,
        )
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        for filename in ["pyproject.toml", "demo.py", "worker_process.py"]:
            shutil.copyfile(LAB / "starter" / filename, outside / filename)
        checked([str(python), "-I", "-m", "mypy", "--strict", "demo.py", "worker_process.py"], outside, env)
        with disposable_postgres() as dsn:
            env["ACADEMY_WORKER_DSN"] = dsn
            tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
            assert "59 passed" in tests.stdout and "skipped" not in tests.stdout, tests.stdout
            print(tests.stdout, end="")
            demo = checked([str(python), "-I", "demo.py", "--output", "leases.json"], outside, env)
            report = json.loads(demo.stdout)
            assert report == json.loads((outside / "leases.json").read_text()) and demo.stderr == ""
            assert report["schema"] == "2026.10-leases-v1" and report["server_version"] // 10000 == 17
            after = dict(records=1, outbox=1, pending=0, inbox=1, total=7, applied=1)
            assert len(report["crashes"]) == 2
            for item, stage, code, applied in zip(
                report["crashes"], ["after-claim", "after-accept"], [81, 82], [0, 1], strict=True
            ):
                assert item == dict(
                    boundary=stage,
                    process=dict(exit=code, connections_gone=True),
                    before_restart=dict(
                        records=1, outbox=1, pending=1, inbox=applied, total=7 * applied, applied=applied
                    ),
                    generation=2,
                    after_restart=after,
                )
            assert report["graceful"] == dict(
                exit=0,
                connections_gone=True,
                admitted=["graceful", "a", 1],
                report=dict(attempted=1, settled=1, stale=0),
                state=dict(records=2, outbox=2, pending=1, inbox=1, total=7, applied=1),
            )
            assert report["poison"] == dict(
                reason="poison",
                report=dict(attempted=1, settled=1, stale=0),
                state=dict(records=1, outbox=1, pending=1, inbox=0, total=0, applied=0),
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
            assert "leased worker exits/reclaims and cooperative SIGTERM" in report["durability_scope"]
            for package in [
                "academy-ingestion-service-lab",
                "academy-competing-ingestion-lab",
                "academy-durable-outbox-lab",
                "academy-leased-worker-lab",
            ]:
                assert report["versions"][package] == "0.1.0"
            if args.report_output:
                args.report_output.write_text(json.dumps(report, indent=2) + "\n")
                assert json.loads(args.report_output.read_text()) == report
    print(
        "PASS: four source/wheel builds, fresh installed resources/quiet import/types, 59 PostgreSQL cases, "
        "two actual worker exits/lease reclaims, cooperative SIGTERM, quarantine, one local effect and actual JSON. "
        "Prior service permissions pass. Owned resources removed; no learner execution or broker/power-loss claim."
    )


if __name__ == "__main__":
    main()
