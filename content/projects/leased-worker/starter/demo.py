"""Actual worker restart evidence in a separately owned disposable schema."""

import argparse
import asyncio
import json
import os
from pathlib import Path
import secrets
import uuid
from importlib.metadata import version
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import make_dsn, parse_dsn
import httpx
from sqlalchemy.pool import QueuePool
from sqlalchemy import text
from academy_ingestion_service import Datum, create_app, make_engine, upgrade
from academy_ingestion_service.database import url_from_dsn
from academy_durable_outbox import consume, install as outbox_install, record
from academy_leased_worker import Failure, Policy, claim, install, run, settle
from academy_leased_worker.evidence import process, wait_due
from threading import Event as StopEvent
from dataclasses import asdict
from academy_durable_outbox.evidence import state


def run_demo() -> dict[str, object]:
    dsn = os.environ.get("ACADEMY_WORKER_DSN")
    if not dsn:
        raise RuntimeError("configure an explicitly disposable PostgreSQL database")
    admin = psycopg2.connect(dsn, connect_timeout=5)
    schema = "worker_demo_" + uuid.uuid4().hex
    engine = None
    try:
        with admin, admin.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        values = parse_dsn(dsn)
        values["options"] = "-csearch_path=" + schema
        engine = make_engine(url_from_dsn(make_dsn(**values)))
        upgrade(engine)
        outbox_install(engine)
        install(engine)
        observations = []
        for stage in ["after-claim", "after-accept"]:
            namespace = stage
            record(engine, namespace, [Datum("a", 1, 7)])
            evidence = process(engine, Path(__file__).with_name("worker_process.py"), stage, namespace)
            before = state(engine, namespace)
            wait_due(engine, namespace)
            lease = claim(engine, namespace, Policy(100, 3, (0, 0)))
            assert lease is not None and lease.generation == 2
            assert settle(engine, lease, consume(engine, lease.event))
            observations.append(
                dict(
                    boundary=stage,
                    process=evidence,
                    before_restart=before,
                    generation=lease.generation,
                    after_restart=state(engine, namespace),
                )
            )
        record(engine, "graceful", [Datum("a", 1, 7), Datum("b", 1, 8)])
        graceful = process(engine, Path(__file__).with_name("worker_process.py"), "graceful", "graceful")
        graceful["state"] = state(engine, "graceful")
        record(engine, "poison", [Datum("a", 1, 7)])
        poison = run(engine, "poison", Policy(), lambda _: Failure.POISON, StopEvent())
        with engine.connect() as connection:
            quarantined = connection.execute(
                text("SELECT reason FROM delivery_job WHERE namespace='poison'")
            ).scalar_one()
        result = record(engine, "scope", [Datum("a", 1, 0), Datum("a", 1, 0), Datum("a", 2, 9)])
        repeat = record(engine, "scope", [Datum("a", 1, 0), Datum("a", 2, 9)])
        token = secrets.token_urlsafe(32)

        async def previous_api() -> tuple[int, int, int, list[dict[str, int | str]]]:
            transport = httpx.ASGITransport(app=create_app(engine, {token: "scope"}))
            async with httpx.AsyncClient(transport=transport, base_url="http://local.test") as client:
                headers = {"Authorization": "Bearer " + token}
                unauthorized = await client.get("/namespaces/scope/readings")
                forbidden = await client.get("/namespaces/other/readings", headers=headers)
                allowed = await client.get("/namespaces/scope/readings", headers=headers)
                items: list[dict[str, int | str]] = allowed.json()["items"]
                return unauthorized.status_code, forbidden.status_code, allowed.status_code, items

        unauthorized, forbidden, allowed, items = asyncio.run(previous_api())
        assert isinstance(engine.pool, QueuePool)
        return {
            "schema": "2026.10-leases-v1",
            "server_version": admin.server_version,
            "versions": {
                name: version(name)
                for name in [
                    "academy-ingestion-service-lab",
                    "academy-competing-ingestion-lab",
                    "academy-durable-outbox-lab",
                    "academy-leased-worker-lab",
                    "SQLAlchemy",
                ]
            },
            "crashes": observations,
            "graceful": graceful,
            "poison": dict(report=asdict(poison), reason=quarantined, state=state(engine, "poison")),
            "stable_batch": {
                "observed": result.receipt.observed,
                "inserted": result.receipt.inserted,
                "duplicates": result.receipt.duplicates,
                "enqueued": result.enqueued,
                "repeat_enqueued": repeat.enqueued,
            },
            "previous_api": {
                "unauthorized": unauthorized,
                "forbidden": forbidden,
                "allowed": allowed,
                "items": items,
                "transport": "in-process ASGI with PostgreSQL; no broker/TCP/TLS claim",
            },
            "checked_out_connections": engine.pool.checkedout(),
            "durability_scope": "leased worker exits/reclaims and cooperative SIGTERM while PostgreSQL stays running; not power loss or backup recovery",
        }
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_demo()
    data = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(data)
    print(data, end="")
