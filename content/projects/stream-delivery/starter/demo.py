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
from academy_ingestion_service import Datum, create_app, make_engine, upgrade
from academy_ingestion_service.database import url_from_dsn
from academy_durable_outbox import Event, install as outbox_install, record
from academy_leased_worker import Policy, claim, install, settle
from academy_leased_worker.evidence import wait_due
from academy_stream_delivery import RedisBroker, deliver, encode, publisher
from academy_stream_delivery.contracts import stream
from academy_stream_delivery.evidence import crash, pending, restart_owned, wait_idle
from redis import Redis
from redis.backoff import NoBackoff
from redis.retry import Retry
from academy_durable_outbox.evidence import state


def run_demo() -> dict[str, object]:
    dsn = os.environ.get("ACADEMY_STREAM_DSN")
    if not dsn:
        raise RuntimeError("configure an explicitly disposable PostgreSQL database")
    admin = psycopg2.connect(dsn, connect_timeout=5)
    schema = "stream_demo_" + uuid.uuid4().hex
    engine = None
    client = Redis.from_url(
        os.environ["ACADEMY_BROKER_URL"],
        decode_responses=False,
        socket_timeout=2,
        socket_connect_timeout=2,
        retry=Retry(NoBackoff(), 0),
    )
    broker = RedisBroker(client)
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
        namespaces = [
            "append-" + uuid.uuid4().hex[:16],
            "effect-" + uuid.uuid4().hex[:16],
            "restart-" + uuid.uuid4().hex[:16],
        ]
        for namespace in namespaces:
            broker.setup(namespace, "effects")
        ns = namespaces[0]
        record(engine, ns, [Datum("a", 1, 7)])
        code = crash(engine, broker, Path(__file__).with_name("worker_process.py"), "after-append", ns)
        before = state(engine, ns)
        assert broker.client.xlen(stream(ns)) == 1
        wait_due(engine, ns)
        lease = claim(engine, ns, Policy(100, 3, (0, 0)))
        assert lease is not None and lease.generation == 2
        assert settle(engine, lease, publisher(broker)(lease.event))
        acceptance = state(engine, ns)
        entries = broker.client.xlen(stream(ns))
        for who in ("first", "second"):
            assert deliver(engine, broker, ns, "effects", who).acknowledged
        observations.append(
            dict(
                boundary="after-append",
                child_exit=code,
                before_restart=before,
                after_broker_acceptance=acceptance,
                stream_entries=entries,
                generation=lease.generation,
                after_consumption=state(engine, ns),
                pending=pending(broker, ns),
            )
        )
        ns = namespaces[1]
        broker.append(ns, encode(Event(ns, "a", 1, 7), version=1))
        code = crash(engine, broker, Path(__file__).with_name("worker_process.py"), "after-effect", ns)
        before = state(engine, ns)
        pending_before = pending(broker, ns)
        wait_idle(broker, ns)
        assert deliver(engine, broker, ns, "effects", "second", recover=True).acknowledged
        observations.append(
            dict(
                boundary="after-effect",
                child_exit=code,
                before_restart=before,
                pending_before=pending_before,
                after_consumption=state(engine, ns),
                pending=pending(broker, ns),
            )
        )
        ns = namespaces[2]
        broker.append(ns, encode(Event(ns, "a", 1, 0)))
        broker.take(ns, "effects", "first", recover=False, idle_ms=100, cursor=b"0-0")
        restart_owned(broker)
        assert broker.client.xlen(stream(ns)) == 1 and pending(broker, ns) == 1
        assert deliver(engine, broker, ns, "effects", "second", recover=True, idle_ms=0).acknowledged
        restarted = dict(
            entries=broker.client.xlen(stream(ns)),
            pending=pending(broker, ns),
            state=state(engine, ns),
            scope="controlled restart of the same AOF volume",
        )
        for namespace in namespaces:
            client.delete(stream(namespace))
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
        info: object = client.info("server")
        assert type(info) is dict and type(info["redis_version"]) is str
        return {
            "schema": "2026.10-streams-v1",
            "server_version": admin.server_version,
            "versions": {
                name: version(name)
                for name in [
                    "academy-ingestion-service-lab",
                    "academy-competing-ingestion-lab",
                    "academy-durable-outbox-lab",
                    "academy-leased-worker-lab",
                    "academy-stream-delivery-lab",
                    "redis",
                    "SQLAlchemy",
                ]
            },
            "crashes": observations,
            "broker_restart": restarted,
            "broker_version": info["redis_version"],
            "acceptance_scope": "XADD and WAITAOF local AOF flush on the same physical connection",
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
            "durability_scope": "real broker delivery and consumer worker exits/replays while PostgreSQL stays running; not power loss or backup recovery",
        }
    finally:
        client.close()
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
