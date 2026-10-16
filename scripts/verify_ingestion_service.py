"""Trusted authored service artifacts and disposable integration; never learner-code evaluation."""

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
LAB = ROOT / "content/projects/ingestion-service"
INTEGRATION = """import asyncio
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from typing import assert_type
import urllib.request
import uuid
import httpx
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import parse_dsn
from sqlalchemy.orm import Session
from academy_ingest import Record
from academy_feed_objects import FeedKey, Reading as ObjectReading, Snapshot
from academy_typed_transforms import Row, decode_row, map_rows
from academy_ingestion_persistence import Reading, persist_batch
from academy_ingestion_service import Cursor, Datum, Page, create_app, make_engine, read_page, upgrade
from academy_ingestion_service.database import url_from_dsn

def main() -> None:
    records = (Record("api", 5), Record("worker", 10))
    def row(record: Record) -> Row:
        return decode_row({"id": record.id, "value": record.value})
    rows = map_rows(records, row)
    assert_type(rows, tuple[Row, ...])
    previous = tuple(Reading("adapter", item.id, 1, item.value) for item in rows)
    schema = "adapter_" + uuid.uuid4().hex
    dsn = os.environ["ACADEMY_SERVICE_DSN"]
    admin = psycopg2.connect(dsn, connect_timeout=5)
    engine = None
    server: subprocess.Popen[bytes] | None = None
    try:
        with admin:
            with admin.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        options = "-csearch_path=" + schema
        values = parse_dsn(dsn)
        values["options"] = options
        configured = psycopg2.extensions.make_dsn(**values)
        engine = make_engine(url_from_dsn(configured))
        upgrade(engine)
        legacy = psycopg2.connect(configured, connect_timeout=5)
        try:
            legacy.set_session(isolation_level="READ COMMITTED", autocommit=False)
            old_result = persist_batch(legacy, previous)
            assert old_result.inserted == 2
        finally:
            legacy.close()
        with Session(engine) as session:
            page = read_page(session, "adapter", limit=1)
            assert_type(page, Page)
            assert page.items == (Datum("api", 1, 5),) and page.next_cursor == Cursor("api", 1)
            rest = read_page(session, "adapter", after=page.next_cursor)
            assert rest.items == (Datum("worker", 1, 10),)
        snapshot = Snapshot(ObjectReading(FeedKey(item.namespace, item.id), item.value) for item in previous)
        assert sum(item.value for item in snapshot) == 15
        token = secrets.token_urlsafe(24)
        app = create_app(engine, {token: "adapter"})
        async def asgi() -> None:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://local", headers={"Authorization":"Bearer " + token}) as client:
                response = await client.post("/namespaces/adapter/readings", json={"items":[{"id": r.id, "revision": r.revision, "value": r.value} for r in previous]})
                assert response.json() == {"observed":2,"inserted":0,"duplicates":2}
        asyncio.run(asgi())
        # A local port probe followed by server bind has a small ordinary allocation race;
        # failure is reported, never passed. No production listener is touched.
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        env = {**os.environ, "ACADEMY_SERVICE_DSN":configured, "ACADEMY_SERVICE_TOKENS":json.dumps({token:"adapter"})}
        server = subprocess.Popen([sys.executable, "-I", "serve.py", "--port", str(port)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        address = "http://127.0.0.1:" + str(port)
        ready = False
        for _ in range(100):
            if server.poll() is not None:
                raise RuntimeError("installed loopback server exited before readiness")
            try:
                with urllib.request.urlopen(address + "/ready", timeout=1) as response:
                    ready = response.status == 200 and json.load(response) == {"status":"ready"}
                if ready:
                    break
            except OSError:
                pass
            time.sleep(0.1)
        assert ready, "installed loopback server never became ready"
        request = urllib.request.Request(address + "/namespaces/adapter/readings", headers={"Authorization":"Bearer " + token})
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.load(response)
            assert response.status == 200 and len(result["items"]) == 2
            assert response.headers["Cache-Control"] == "no-store" and len(response.headers["X-Request-ID"]) == 32
        print("installed typed Record/Row/legacy-Reading/service/Snapshot composition and actual loopback TCP readiness/read passed")
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
        if engine is not None:
            engine.dispose()
        admin.rollback()
        admin.autocommit = True
        try:
            with admin.cursor() as cursor:
                cursor.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
        finally:
            admin.close()

if __name__ == "__main__":
    main()
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-service-artifacts-") as directory:
        temporary = Path(directory)
        wheels = []
        for name, package, files in [
            ("ingestion-package", "academy_ingest", ["parser.py", "http.py"]),
            ("feed-objects", "academy_feed_objects", ["objects.py"]),
            ("typed-transforms", "academy_typed_transforms", ["transform.py"]),
            ("ingestion-persistence", "academy_ingestion_persistence", ["store.py"]),
            ("ingestion-service", "academy_ingestion_service", ["auth.py", "service.py"]),
        ]:
            lab = ROOT / "content/projects" / name
            source = temporary / name
            shutil.copytree(
                lab / "starter",
                source,
                ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"),
            )
            for filename in files:
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
            if k
            not in {"PYTHONPATH", "PYTHONHOME", "MYPYPATH", "ACADEMY_SERVICE_DSN", "ACADEMY_SERVICE_TOKENS"}
        }
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        install = [str(python), "-m", "pip", "install"]
        if args.wheelhouse:
            install += ["--no-index", "--find-links", str(args.wheelhouse.resolve())]
        checked(
            install
            + wheels
            + [
                "httpx==0.28.1",
                "uvicorn==0.35.0",
                "pytest==9.0.3",
                "mypy==2.3.1",
                "types-psycopg2==2.9.21.20260911",
            ],
            outside,
            env,
        )
        checked([str(python), "-m", "pip", "check"], outside, env)
        quiet = checked([str(python), "-I", "-c", "import academy_ingestion_service"], outside, env)
        assert quiet.stdout == quiet.stderr == ""
        probe = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_ingestion_service; p=files('academy_ingestion_service'); assert p.joinpath('py.typed').is_file(); assert p.joinpath('migrations/env.py').is_file(); assert p.joinpath('migrations/versions/001_initial.py').is_file(); assert p.joinpath('migrations/versions/002_observed_at.py').is_file(); print(academy_ingestion_service.__file__)",
            ],
            outside,
            env,
        )
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        for filename in ["pyproject.toml", "demo.py", "serve.py"]:
            shutil.copyfile(LAB / "starter" / filename, outside / filename)
        (outside / "integration.py").write_text(INTEGRATION)
        checked(
            [str(python), "-I", "-m", "mypy", "--strict", "integration.py", "demo.py", "serve.py"],
            outside,
            env,
        )
        with disposable_postgres() as dsn:
            env["ACADEMY_SERVICE_DSN"] = dsn
            tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
            assert "70 passed" in tests.stdout and "skipped" not in tests.stdout, tests.stdout
            print(tests.stdout, end="")
            demo = checked([str(python), "-I", "demo.py", "--output", "service.json"], outside, env)
            report = json.loads(demo.stdout)
            assert report == json.loads((outside / "service.json").read_text())
            assert report["schema"] == "2026.10-service-v1" and report["server_version"] // 10000 == 17
            assert report["statuses"] == {
                "first": 200,
                "repeat": 200,
                "denied": 403,
                "invalid": 422,
                "conflict": 409,
                "ready": 200,
                "old_schema_ready": 503,
                "reupgraded_ready": 200,
            }
            assert report["first"] == {"observed": 3, "inserted": 3, "duplicates": 0}
            assert report["repeat"] == {"observed": 3, "inserted": 0, "duplicates": 3}
            assert all(
                report[key] is True
                for key in [
                    "late_conflict_rolled_back",
                    "baseline_rows_preserved",
                    "pooled_connections_returned",
                ]
            )
            assert demo.stderr == ""
            if args.report_output:
                args.report_output.write_text(json.dumps(report, indent=2) + "\n")
                assert json.loads(args.report_output.read_text()) == report
            adapter = checked([str(python), "-I", "integration.py"], outside, env)
            assert adapter.stderr == ""
            print(adapter.stdout, end="")
    print(
        "PASS: five source/wheel builds, fresh installation, resources/quiet import/types, 70 cases on PostgreSQL 17, actual ASGI/transaction/migration JSON, prior-package composition and real loopback TCP server. Owned resources removed; no learner execution."
    )


if __name__ == "__main__":
    main()
