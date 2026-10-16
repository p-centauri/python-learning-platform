"""Trusted authored artifact/database verification; never a learner-code evaluator."""

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
LAB = ROOT / "content/projects/ingestion-persistence"
INTEGRATION = """from importlib.resources import files
import os
import uuid
from typing import assert_type
import psycopg2
from psycopg2 import sql
from academy_ingest import Record
from academy_feed_objects import FeedKey, Reading as ObjectReading, Snapshot
from academy_typed_transforms import Row, decode_row, map_rows
from academy_ingestion_persistence import BatchResult, Reading, load_namespace, persist_batch

def main() -> None:
    records = (Record("api", 5), Record("worker", 10))
    def row(record: Record) -> Row:
        return decode_row({"id": record.id, "value": record.value})
    rows = map_rows(records, row)
    assert_type(rows, tuple[Row, ...])
    readings = tuple(Reading("adapter", item.id, 1, item.value) for item in rows)
    schema = "adapter_" + uuid.uuid4().hex
    conn = psycopg2.connect(os.environ["ACADEMY_PERSISTENCE_DSN"], connect_timeout=5)
    observer = psycopg2.connect(os.environ["ACADEMY_PERSISTENCE_DSN"], connect_timeout=5)
    try:
        for client in (conn, observer):
            client.set_session(isolation_level="READ COMMITTED", autocommit=False, readonly=False)
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
                cur.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
                cur.execute(files("academy_ingestion_persistence").joinpath("schema.sql").read_text())
        with observer:
            with observer.cursor() as cur:
                cur.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        first = persist_batch(conn, readings)
        assert_type(first, BatchResult)
        repeat = persist_batch(conn, readings)
        assert first == BatchResult(2, 2, 0) and repeat == BatchResult(2, 0, 2)
        saved = load_namespace(observer, "adapter")
        assert_type(saved, tuple[Reading, ...])
        assert saved == readings
        snapshot = Snapshot(ObjectReading(FeedKey(item.namespace, item.id), item.value) for item in saved)
        assert len(snapshot) == 2 and sum(item.value for item in snapshot) == 15
        assert conn.closed == observer.closed == 0
    finally:
        conn.close()
        observer.rollback()
        observer.autocommit = True
        try:
            with observer.cursor() as cur:
                cur.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
        finally:
            observer.close()
    print("installed strict-typed record/row/PostgreSQL/snapshot adapter passed")

if __name__ == "__main__":
    main()
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-persistence-artifacts-") as directory:
        temporary = Path(directory)
        wheels = []
        for name, package, names in [
            ("ingestion-package", "academy_ingest", ["parser.py", "http.py"]),
            ("feed-objects", "academy_feed_objects", ["objects.py"]),
            ("typed-transforms", "academy_typed_transforms", ["transform.py"]),
            ("ingestion-persistence", "academy_ingestion_persistence", ["store.py"]),
        ]:
            lab = ROOT / "content/projects" / name
            source = temporary / name
            shutil.copytree(
                lab / "starter",
                source,
                ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"),
            )
            for filename in names:
                shutil.copyfile(lab / "reference" / filename, source / "src" / package / filename)
            built = checked([sys.executable, "-m", "build", "--no-isolation"], source)
            assert "Building wheel from sdist" in built.stdout
            wheels.append(str(next((source / "dist").glob("*.whl"))))
        environment = temporary / "installed"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        outside = temporary / "outside"
        outside.mkdir()
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"PYTHONPATH", "PYTHONHOME", "MYPYPATH", "ACADEMY_PERSISTENCE_DSN"}
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
        quiet = checked([str(python), "-I", "-c", "import academy_ingestion_persistence"], outside, env)
        assert quiet.stdout == quiet.stderr == ""
        probe = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_ingestion_persistence; assert files('academy_ingestion_persistence').joinpath('schema.sql').is_file(); assert files('academy_ingestion_persistence').joinpath('py.typed').is_file(); print(academy_ingestion_persistence.__file__)",
            ],
            outside,
            env,
        )
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        shutil.copyfile(LAB / "starter/pyproject.toml", outside / "pyproject.toml")
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        (outside / "integration.py").write_text(INTEGRATION)
        checked([str(python), "-I", "-m", "mypy", "--strict", "integration.py", "demo.py"], outside, env)
        with disposable_postgres() as dsn:
            env["ACADEMY_PERSISTENCE_DSN"] = dsn
            tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
            assert "57 passed" in tests.stdout and "skipped" not in tests.stdout, tests.stdout
            print(tests.stdout, end="")
            demo = checked([str(python), "-I", "demo.py", "--output", "persistence.json"], outside, env)
            report = json.loads(demo.stdout)
            assert report == json.loads((outside / "persistence.json").read_text())
            assert report["schema"] == "2026.10-persistence-v1" and report["server_version"] // 10000 == 17
            assert report["first"] == {"observed": 2, "inserted": 2, "duplicates": 0}
            assert report["repeat"] == {"observed": 2, "inserted": 0, "duplicates": 2}
            assert report["sqlstates"] == {
                "foreign-key": "23503",
                "check": "23514",
                "not-null": "23502",
                "unique": "23505",
            }
            assert all(
                report[key] is True
                for key in [
                    "late_conflict_rejected",
                    "new_namespace_rolled_back",
                    "unchanged_after_failures",
                    "connection_open",
                    "transaction_idle",
                ]
            )
            assert demo.stderr == ""
            if args.report_output:
                args.report_output.write_text(json.dumps(report, indent=2) + "\n")
                assert json.loads(args.report_output.read_text()) == report
            result = checked([str(python), "-I", "integration.py"], outside, env)
            assert result.stderr == ""
            print(result.stdout, end="")
    print(
        "PASS: four source/wheel builds, fresh installation, pip check, 57 public cases on owned PostgreSQL 17, packaged schema/typing marker, quiet import, actual commit/rollback/SQLSTATE evidence and strict-typed earlier-package integration. Owned container and network removed."
    )


if __name__ == "__main__":
    main()
