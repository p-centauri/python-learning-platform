"""Trusted installed versioned schema migration evidence on owned PostgreSQL; never learner-code execution."""

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
LAB = ROOT / "content/projects/delivery-schema"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-schema-artifacts-") as directory:
        area = Path(directory)
        wheels = []
        for name, package, references in [
            ("ingestion-service", "academy_ingestion_service", ["auth.py", "service.py"]),
            ("competing-ingestion", "academy_competing_ingestion", ["retry.py", "reconcile.py"]),
            ("durable-outbox", "academy_durable_outbox", ["core.py"]),
            ("leased-worker", "academy_leased_worker", ["core.py"]),
            ("stream-delivery", "academy_stream_delivery", ["envelope.py", "delivery.py"]),
            ("delivery-schema", "academy_delivery_schema", ["operations.py"]),
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
                "ACADEMY_SCHEMA_DSN",
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
        quiet = checked([str(python), "-I", "-c", "import academy_delivery_schema"], outside, env)
        assert quiet.stdout == quiet.stderr == ""
        probe = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_delivery_schema; assert files('academy_delivery_schema').joinpath('py.typed').is_file(); assert files('academy_delivery_schema').joinpath('migrations/versions/004_worker.py').is_file(); assert files('academy_ingestion_service').joinpath('migrations/versions/002_observed_at.py').is_file(); print(academy_delivery_schema.__file__)",
            ],
            outside,
            env,
        )
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        for filename in ["pyproject.toml", "demo.py"]:
            shutil.copyfile(LAB / "starter" / filename, outside / filename)
        checked([str(python), "-I", "-m", "mypy", "--strict", "demo.py"], outside, env)
        with disposable_postgres() as dsn, disposable_broker() as (url, container):
            env["ACADEMY_SCHEMA_DSN"] = dsn
            env["ACADEMY_BROKER_URL"] = url
            env["ACADEMY_BROKER_CONTAINER"] = container
            tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
            assert "44 passed" in tests.stdout and "skipped" not in tests.stdout, tests.stdout
            print(tests.stdout, end="")
            demo = checked([str(python), "-I", "demo.py", "--output", "schema.json"], outside, env)
            report = json.loads(demo.stdout)
            assert report == json.loads((outside / "schema.json").read_text()) and demo.stderr == ""
            assert (
                report["schema"] == "2026.10-delivery-schema-v1" and report["server_version"] // 10000 == 17
            )
            assert report["before_facts"] == report["after_facts"] == report["final_facts"]
            assert len(report["before_facts"]) == 2
            assert [(r["revision"], r["value"], r["ingested_at"]) for r in report["before_facts"]] == [
                (1, 0, "2020-01-01 00:00:00+00:00"),
                (2, 9, "2020-01-02 00:00:00+00:00"),
            ]
            assert report["head"] == ["delivery_004"]
            assert report["adoption"] == dict(inserted=0, duplicates=2, enqueued=2)
            assert report["delivered"] == dict(records=2, outbox=2, pending=0, inbox=2, total=9, applied=2)
            assert report["drift"]["head_only"] is True and report["drift"]["missing_index_detected"] is True
            assert report["worker_rollback"]["revisions"] == ["delivery_003"]
            assert report["worker_rollback"]["facts_preserved"] is True
            assert report["worker_rollback"]["state"] == report["delivered"]
            assert report["history_rollback"] == dict(
                revisions=["service_002"],
                tables=["alembic_version", "feed_record", "feed_source"],
                facts_preserved=True,
            )
            assert report["after_reupgrade"] == dict(
                records=2, outbox=0, pending=0, inbox=0, total=0, applied=0
            )
            assert report["same_key_can_apply_after_history_loss"] is True
            assert report["previous_api"] == dict(
                unauthorized=401,
                forbidden=403,
                allowed=200,
                old_ready=503,
                items=[dict(id="a", revision=1, value=0), dict(id="a", revision=2, value=9)],
            )
            assert report["checked_out_connections"] == 0
            assert report["versions"]["alembic"] == "1.16.5"
            for name in [
                "academy-ingestion-service-lab",
                "academy-competing-ingestion-lab",
                "academy-durable-outbox-lab",
                "academy-leased-worker-lab",
                "academy-stream-delivery-lab",
                "academy-delivery-schema-lab",
            ]:
                assert report["versions"][name] == "0.1.0"
            if args.report_output:
                args.report_output.write_text(json.dumps(report, indent=2) + "\n")
                assert json.loads(args.report_output.read_text()) == report
    print(
        "PASS: six source/wheel builds, fresh installed migration resources/types, 44 public cases (19 live), actual PostgreSQL transactional rollback/locks, drift boundaries, preserved timestamped facts, explicit lost history and real Redis composition. Owned resources removed; no learner execution, deployment or backup claim."
    )


if __name__ == "__main__":
    main()
