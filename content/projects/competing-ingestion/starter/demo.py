"""Actual disposable PostgreSQL observations; no server starts on import."""

import argparse
import asyncio
from importlib.metadata import version
import json
import os
from pathlib import Path
import secrets
from unittest.mock import patch
import uuid
import httpx
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import make_dsn, parse_dsn
from sqlalchemy import insert, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool
from academy_ingestion_service import Datum, create_app, ingest, make_engine, upgrade
from academy_ingestion_service.database import url_from_dsn
from academy_ingestion_service.models import RecordRow
from academy_competing_ingestion import UnknownOutcome, reconcile, retry_ingest
from academy_competing_ingestion.contracts import RetryPolicy, owned_session
from academy_competing_ingestion.experiments import (
    competing_insert,
    deadlock_retry,
    lock_timeout,
    serializable_gate,
    snapshot_visibility,
    source,
)


def run_demo() -> dict[str, object]:
    dsn = os.environ.get("ACADEMY_COMPETITION_DSN")
    if not dsn:
        raise RuntimeError("configure an explicitly disposable PostgreSQL database")
    admin = psycopg2.connect(dsn, connect_timeout=5)
    schema = "competition_demo_" + uuid.uuid4().hex
    engine = None
    try:
        with admin, admin.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        values = parse_dsn(dsn)
        values["options"] = "-csearch_path=" + schema
        engine = make_engine(url_from_dsn(make_dsn(**values)))
        upgrade(engine)
        report: dict[str, object] = {
            "schema": "2026.10-competition-v1",
            "server_version": admin.server_version,
            "versions": {
                name: version(name)
                for name in [
                    "academy-ingestion-service-lab",
                    "academy-competing-ingestion-lab",
                    "SQLAlchemy",
                    "psycopg2-binary",
                ]
            },
        }
        report["races"] = [
            competing_insert(engine, commit_holder=commit, challenger_value=value)
            for commit, value in [(True, 5), (True, 9), (False, 5), (False, 9)]
        ]
        report["snapshots"] = [
            snapshot_visibility(engine, isolation) for isolation in ["READ COMMITTED", "REPEATABLE READ"]
        ]
        report["serializable"] = serializable_gate(engine)
        report["deadlock"] = deadlock_retry(engine)
        report["lock_timeout"] = lock_timeout(engine)
        with owned_session(engine, RetryPolicy(lock_timeout_ms=50, statement_timeout_ms=100)) as session:
            try:
                with session.begin():
                    session.execute(text("SELECT pg_sleep(0.2)"))
            except DBAPIError as error:
                report["statement_timeout"] = {
                    "sqlstate": getattr(error.orig, "pgcode", None),
                    "transaction_idle": not session.in_transaction(),
                }
            else:
                raise AssertionError("statement timeout did not fire")
        source(engine, "pending")
        with Session(engine) as writer, writer.begin():
            writer.execute(insert(RecordRow).values(namespace="pending", id="a", revision=1, value=0))
            missing = reconcile(engine, "pending", [Datum("a", 1, 0)])
        complete = reconcile(engine, "pending", [Datum("a", 1, 0)])
        report["inflight_reconciliation"] = {"before_commit": missing.state, "after_commit": complete.state}
        calls: list[int] = []

        def lost_ack(session: Session, namespace: str, rows: tuple[Datum, ...]) -> object:
            calls.append(1)
            ingest(session, namespace, rows)
            raise DBAPIError(
                "modeled statement",
                {},
                RuntimeError("modeled acknowledgment loss"),
                connection_invalidated=True,
            )

        with patch("academy_competing_ingestion.retry.ingest", lost_ack):
            try:
                retry_ingest(engine, "modeled", [Datum("a", 1, 0)])
            except UnknownOutcome as error:
                report["modeled_loss"] = {
                    "kind": "modeled missing response after actual commit",
                    "attempts": error.attempts,
                    "calls": len(calls),
                    "reconciliation": reconcile(engine, "modeled", [Datum("a", 1, 0)]).state,
                }
            else:
                raise AssertionError("modeled unknown outcome did not stop")
        token = secrets.token_urlsafe(24)
        app = create_app(engine, {token: "modeled"})

        async def api() -> dict[str, object]:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://local"
            ) as client:
                unauthorized = await client.get("/namespaces/modeled/readings")
                client.headers["Authorization"] = "Bearer " + token
                forbidden = await client.get("/namespaces/other/readings")
                allowed = await client.get("/namespaces/modeled/readings")
                return {
                    "unauthorized": unauthorized.status_code,
                    "forbidden": forbidden.status_code,
                    "allowed": allowed.status_code,
                    "items": allowed.json()["items"],
                    "transport": "in-process ASGI; no DNS/TLS/proxy claim",
                }

        report["previous_api"] = asyncio.run(api())
        with engine.connect() as connection:
            report["local_settings_reset"] = {
                "lock_timeout": connection.execute(text("SHOW lock_timeout")).scalar_one(),
                "statement_timeout": connection.execute(text("SHOW statement_timeout")).scalar_one(),
            }
        assert isinstance(engine.pool, QueuePool)
        report["checked_out_connections"] = engine.pool.checkedout()
        return report
    finally:
        if engine is not None:
            engine.dispose()
        admin.rollback()
        admin.autocommit = True
        try:
            with admin.cursor() as cursor:
                cursor.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
        finally:
            admin.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_demo()
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
