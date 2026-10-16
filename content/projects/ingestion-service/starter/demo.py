"""Actual ASGI/PostgreSQL evidence in one uniquely owned disposable schema."""

import argparse
import asyncio
from importlib.metadata import version
import json
import os
from pathlib import Path
import secrets
import uuid
import httpx
import psycopg2
from psycopg2 import sql
from sqlalchemy import text
from sqlalchemy.pool import QueuePool
from academy_ingestion_service import check_migrations, create_app, downgrade, make_engine, upgrade
from academy_ingestion_service.database import url_from_dsn


async def main_async(dsn: str) -> dict[str, object]:
    schema = "demo_" + uuid.uuid4().hex
    admin = psycopg2.connect(dsn, connect_timeout=5)
    engine = None
    try:
        with admin:
            with admin.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        engine = make_engine(url_from_dsn(dsn).update_query_dict({"options": "-csearch_path=" + schema}))
        upgrade(engine, "service_001")
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO feed_source VALUES (:ns)"), {"ns": "legacy"})
            connection.execute(
                text("INSERT INTO feed_record VALUES (:ns,:id,:revision,:value)"),
                {"ns": "legacy", "id": "kept", "revision": 1, "value": 7},
            )
        upgrade(engine)
        check_migrations(engine)
        token = secrets.token_urlsafe(24)
        app = create_app(engine, {token: "feed"})
        headers = {"Authorization": "Bearer " + token}
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://local", headers=headers
        ) as client:
            payload = {
                "items": [
                    {"id": "a", "revision": 1, "value": 0},
                    {"id": "b", "revision": 1, "value": 10},
                    {"id": "c", "revision": 1, "value": 20},
                ]
            }
            first = await client.post("/namespaces/feed/readings", json=payload)
            repeat = await client.post("/namespaces/feed/readings", json=payload)
            page = await client.get("/namespaces/feed/readings", params={"limit": "2"})
            next_page = await client.get(
                "/namespaces/feed/readings", params={"limit": "2", "after_id": "b", "after_revision": "1"}
            )
            denied = await client.get("/namespaces/other/readings")
            invalid = await client.post(
                "/namespaces/feed/readings", json={"items": [{"id": "a", "revision": True, "value": 0}]}
            )
            conflict = await client.post(
                "/namespaces/feed/readings",
                json={
                    "items": [
                        {"id": "new", "revision": 1, "value": 4},
                        {"id": "a", "revision": 1, "value": 99},
                    ]
                },
            )
            after_failure = await client.get("/namespaces/feed/readings", params={"limit": "32"})
            ready = await client.get("/ready")
            with engine.connect() as observer:
                preserved_before = tuple(
                    observer.execute(
                        text("SELECT namespace,id,revision,value FROM feed_record WHERE namespace='legacy'")
                    ).one()
                )
            downgrade(engine, "service_001")
            old_ready = await client.get("/ready")
            with engine.connect() as observer:
                preserved_after = tuple(
                    observer.execute(
                        text("SELECT namespace,id,revision,value FROM feed_record WHERE namespace='legacy'")
                    ).one()
                )
            upgrade(engine)
            check_migrations(engine)
            ready_again = await client.get("/ready")
        report: dict[str, object] = {
            "schema": "2026.10-service-v1",
            "server_version": admin.server_version,
            "versions": {
                name: version(name)
                for name in ["fastapi", "pydantic", "SQLAlchemy", "alembic", "psycopg2-binary"]
            },
            "statuses": {
                "first": first.status_code,
                "repeat": repeat.status_code,
                "denied": denied.status_code,
                "invalid": invalid.status_code,
                "conflict": conflict.status_code,
                "ready": ready.status_code,
                "old_schema_ready": old_ready.status_code,
                "reupgraded_ready": ready_again.status_code,
            },
            "first": first.json(),
            "repeat": repeat.json(),
            "first_page": page.json(),
            "second_page": next_page.json(),
            "late_conflict_rolled_back": [r["id"] for r in after_failure.json()["items"]] == ["a", "b", "c"],
            "baseline_rows_preserved": preserved_before == preserved_after == ("legacy", "kept", 1, 7),
            "pooled_connections_returned": isinstance(engine.pool, QueuePool)
            and engine.pool.checkedout() == 0,
            "public_response_fields": list(page.json()["items"][0]),
            "transport": "in-process ASGI with real PostgreSQL; TCP/TLS not evaluated here",
        }
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
    dsn = os.environ.get("ACADEMY_SERVICE_DSN")
    if not dsn:
        parser.error("set ACADEMY_SERVICE_DSN to an explicitly disposable PostgreSQL database")
    report = asyncio.run(main_async(dsn))
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
