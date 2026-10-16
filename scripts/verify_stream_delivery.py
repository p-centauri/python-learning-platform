"""Trusted installed Redis Streams delivery evidence on owned PostgreSQL; never learner-code execution."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import venv
from persistence_db import disposable_postgres
from stream_broker import disposable_broker
from verify_ingestion_package import checked

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "content/projects/stream-delivery"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-stream-artifacts-") as directory:
        area = Path(directory)
        wheels = []
        for name, package, references in [
            ("ingestion-service", "academy_ingestion_service", ["auth.py", "service.py"]),
            ("competing-ingestion", "academy_competing_ingestion", ["retry.py", "reconcile.py"]),
            ("durable-outbox", "academy_durable_outbox", ["core.py"]),
            ("leased-worker", "academy_leased_worker", ["core.py"]),
            ("stream-delivery", "academy_stream_delivery", ["envelope.py", "delivery.py"]),
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
                "ACADEMY_STREAM_DSN",
                "ACADEMY_STREAM_CHILD",
                "ACADEMY_BROKER_URL",
                "ACADEMY_BROKER_CONTAINER",
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
        quiet = checked([str(python), "-I", "-c", "import academy_stream_delivery"], outside, env)
        assert quiet.stdout == quiet.stderr == ""
        probe = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_stream_delivery; assert files('academy_stream_delivery').joinpath('py.typed').is_file(); assert files('academy_leased_worker').joinpath('schema.sql').is_file(); assert files('academy_ingestion_service').joinpath('migrations/versions/002_observed_at.py').is_file(); print(academy_stream_delivery.__file__)",
            ],
            outside,
            env,
        )
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        for filename in ["pyproject.toml", "demo.py", "worker_process.py"]:
            shutil.copyfile(LAB / "starter" / filename, outside / filename)
        checked([str(python), "-I", "-m", "mypy", "--strict", "demo.py", "worker_process.py"], outside, env)
        with disposable_postgres() as dsn, disposable_broker() as (url, container):
            env["ACADEMY_STREAM_DSN"] = dsn
            env["ACADEMY_BROKER_URL"] = url
            env["ACADEMY_BROKER_CONTAINER"] = container
            tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
            assert "74 passed" in tests.stdout and "skipped" not in tests.stdout, tests.stdout
            print(tests.stdout, end="")
            demo = checked([str(python), "-I", "demo.py", "--output", "streams.json"], outside, env)
            report = json.loads(demo.stdout)
            assert report == json.loads((outside / "streams.json").read_text()) and demo.stderr == ""
            assert report["schema"] == "2026.10-streams-v1" and report["server_version"] // 10000 == 17
            assert report["broker_version"] == "7.4.2" and report["versions"]["redis"] == "6.4.0"
            zero = dict(records=1, outbox=1, pending=1, inbox=0, total=0, applied=0)
            after = dict(records=1, outbox=1, pending=0, inbox=1, total=7, applied=1)
            acceptance = dict(records=1, outbox=1, pending=0, inbox=0, total=0, applied=0)
            local = dict(records=0, outbox=0, pending=0, inbox=1, total=7, applied=1)
            assert report["crashes"] == [
                dict(
                    boundary="after-append",
                    child_exit=91,
                    before_restart=zero,
                    after_broker_acceptance=acceptance,
                    stream_entries=2,
                    generation=2,
                    after_consumption=after,
                    pending=0,
                ),
                dict(
                    boundary="after-effect",
                    child_exit=92,
                    before_restart=local,
                    pending_before=1,
                    after_consumption=local,
                    pending=0,
                ),
            ]
            assert report["broker_restart"] == dict(
                entries=1,
                pending=0,
                state=dict(records=0, outbox=0, pending=0, inbox=1, total=0, applied=1),
                scope="controlled restart of the same AOF volume",
            )
            assert "same physical connection" in report["acceptance_scope"]
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
            assert "real broker delivery and consumer worker exits/replays" in report["durability_scope"]
            for package in [
                "academy-ingestion-service-lab",
                "academy-competing-ingestion-lab",
                "academy-durable-outbox-lab",
                "academy-leased-worker-lab",
                "academy-stream-delivery-lab",
            ]:
                assert report["versions"][package] == "0.1.0"
            if args.report_output:
                args.report_output.write_text(json.dumps(report, indent=2) + "\n")
                assert json.loads(args.report_output.read_text()) == report
    print(
        "PASS: five source/wheel builds, fresh installed resources/types/quiet imports, 74 public cases (15 live), "
        "actual AOF acceptance, pending reclaim, two real worker exits and controlled broker restart, "
        "versioned envelopes, one local effect and actual JSON. Prior API permissions pass. "
        "Owned broker/database resources removed; no learner execution or power-loss/exactly-once claim."
    )


if __name__ == "__main__":
    main()
