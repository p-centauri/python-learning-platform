"""Verify trusted authored recovery artifacts on owned stores; never run learner uploads."""

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
LAB = ROOT / "content/projects/delivery-recovery"
PACKAGES = [
    ("ingestion-service", "academy_ingestion_service", ["auth.py", "service.py"]),
    ("competing-ingestion", "academy_competing_ingestion", ["retry.py", "reconcile.py"]),
    ("durable-outbox", "academy_durable_outbox", ["core.py"]),
    ("leased-worker", "academy_leased_worker", ["core.py"]),
    ("stream-delivery", "academy_stream_delivery", ["envelope.py", "delivery.py"]),
    ("delivery-schema", "academy_delivery_schema", ["operations.py"]),
    ("delivery-recovery", "academy_delivery_recovery", ["operations.py"]),
]


def completed_sources(area):
    roots = []
    for name, package, references in PACKAGES:
        source = area / name
        lab = ROOT / "content/projects" / name
        shutil.copytree(
            lab / "starter",
            source,
            ignore=shutil.ignore_patterns(
                "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", "dist", "*.egg-info"
            ),
        )
        for filename in references:
            shutil.copyfile(lab / "reference" / filename, source / "src" / package / filename)
        roots.append(source)
    return roots


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-recovery-artifacts-") as directory:
        area = Path(directory)
        wheels = []
        for source in completed_sources(area):
            built = checked([sys.executable, "-m", "build", "--no-isolation"], source)
            assert "Building wheel from sdist" in built.stdout
            wheels.append(str(next((source / "dist").glob("*.whl"))))
        environment = area / "installed"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        outside = area / "outside"
        outside.mkdir()
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in ("PYTHONPATH", "PYTHONHOME", "MYPYPATH") and not key.startswith("ACADEMY_")
        }
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        install = [str(python), "-m", "pip", "install"]
        if args.wheelhouse:
            install += ["--no-index", "--find-links", str(args.wheelhouse.resolve())]
        checked(
            install + wheels + ["pytest==9.0.3", "mypy==2.3.1", "types-psycopg2==2.9.21.20260911"],
            outside,
            env,
        )
        checked([str(python), "-m", "pip", "check"], outside, env)
        quiet = checked([str(python), "-I", "-c", "import academy_delivery_recovery"], outside, env)
        assert quiet.stdout == quiet.stderr == ""
        probe = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_delivery_recovery; "
                "assert files('academy_delivery_recovery').joinpath('prune.lua').is_file(); "
                "assert files('academy_delivery_recovery').joinpath('py.typed').is_file(); "
                "print(academy_delivery_recovery.__file__)",
            ],
            outside,
            env,
        )
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        checked(
            [str(python), "-I", "-m", "mypy", "--strict", "-p", "academy_delivery_recovery"], outside, env
        )
        checked([str(python), "-I", "-m", "mypy", "--strict", "demo.py"], outside, env)
        with disposable_postgres() as dsn, disposable_broker() as (url, _):
            env["ACADEMY_RECOVERY_DSN"], env["ACADEMY_BROKER_URL"] = dsn, url
            tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
            assert "36 passed" in tests.stdout and "skipped" not in tests.stdout, tests.stdout
            print(tests.stdout, end="")
            demo = checked([str(python), "-I", "demo.py", "--output", "recovery.json"], outside, env)
            report = json.loads(demo.stdout)
            assert report == json.loads((outside / "recovery.json").read_text()) and not demo.stderr
            assert report["head"] == ["delivery_004"] and report["server_version"] // 10000 == 17
            assert report["redrive"] == dict(
                before=1, ready=1, claimed=2, state="done", repeated=False, stale_settlement=False, maximum=3
            )
            assert report["pruning"] == dict(
                before_effect="blocked",
                unread_group="blocked",
                result="removed",
                length=0,
                repeated="missing",
            )
            assert report["retained"] == dict(
                feed_record=1, delivery_outbox=1, delivery_inbox=1, delivery_job=1
            )
            assert report["replay"] == dict(total=7, applied=1, inbox_unchanged=True)
            assert report["checked_out_connections"] == 0
            if args.report_output:
                args.report_output.parent.mkdir(parents=True, exist_ok=True)
                args.report_output.write_text(json.dumps(report, indent=2) + "\n")
                assert json.loads(args.report_output.read_text()) == report
    print(
        "PASS: seven built/installed artifacts, 36 public cases (22 live), actual guarded redrive, "
        "all-current-group pruning, retained history and duplicate-safe broker replay. Owned stores removed."
    )


if __name__ == "__main__":
    main()
