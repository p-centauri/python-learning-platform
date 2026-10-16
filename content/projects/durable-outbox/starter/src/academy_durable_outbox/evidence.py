"""Supplied actual subprocess/observer helpers for trusted disposable fixtures."""

import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from psycopg2.extensions import make_dsn
from sqlalchemy import Engine, text


def crash(engine: Engine, script: Path, stage: str, namespace: str) -> int:
    name = "outbox-child-" + uuid.uuid4().hex
    url = engine.url
    dsn = make_dsn(
        host=url.host,
        port=url.port or 5432,
        dbname=url.database,
        user=url.username,
        password=url.password,
        options=url.query.get("options", ""),
    )
    env = {**os.environ, "ACADEMY_OUTBOX_DSN": dsn, "ACADEMY_OUTBOX_CHILD": name}
    result = subprocess.run(
        [sys.executable, str(script), stage, namespace], env=env, capture_output=True, text=True, timeout=15
    )
    expected = {"before-record-commit": 71, "after-record-commit": 72, "after-consume-commit": 73}[stage]
    if result.returncode != expected or result.stdout or result.stderr:
        raise AssertionError("crash fixture did not reach its specified quiet exit boundary")
    until = time.monotonic() + 3
    while time.monotonic() < until:
        with engine.connect() as connection:
            active = connection.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE application_name=:name"), {"name": name}
            ).scalar_one()
        if active == 0:
            return result.returncode
        time.sleep(0.01)  # Pace observed backend cleanup, not a claimed ordering guarantee.
    raise AssertionError("crashed worker database connections have not closed")


def state(engine: Engine, namespace: str) -> dict[str, int]:
    with engine.connect() as connection:
        result = {}
        for key, statement in {
            "records": "SELECT count(*) FROM feed_record WHERE namespace=:namespace",
            "outbox": "SELECT count(*) FROM delivery_outbox WHERE namespace=:namespace",
            "pending": "SELECT count(*) FROM delivery_outbox WHERE namespace=:namespace AND NOT acknowledged",
            "inbox": "SELECT count(*) FROM delivery_inbox WHERE namespace=:namespace",
            "total": "SELECT coalesce(sum(total),0) FROM delivery_effect WHERE namespace=:namespace",
            "applied": "SELECT coalesce(sum(applied),0) FROM delivery_effect WHERE namespace=:namespace",
        }.items():
            result[key] = int(connection.execute(text(statement), {"namespace": namespace}).scalar_one())
    return result
