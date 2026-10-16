"""Owned subprocess evidence; private DSN only in environment, never in returned reports."""

import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time
import uuid
from psycopg2.extensions import make_dsn
from sqlalchemy import Engine, text


def wait_due(engine: Engine, namespace: str) -> None:
    until = time.monotonic() + 3
    while time.monotonic() < until:
        with engine.connect() as connection:
            due = connection.execute(
                text("""
                SELECT bool_and(lease_until <= clock_timestamp()) FROM delivery_job
                WHERE namespace=:ns AND state='leased'
            """),
                dict(ns=namespace),
            ).scalar_one()
        if due is True:
            return
        time.sleep(0.01)  # Pace a real database-clock observation, not an assumed ordering.
    raise AssertionError("database lease expiry was not observed")


def process(engine: Engine, script: Path, stage: str, namespace: str) -> dict[str, object]:
    if stage not in ("after-claim", "after-accept", "graceful"):
        raise ValueError("unknown authored process boundary")
    name = "lease-child-" + uuid.uuid4().hex
    url = engine.url
    dsn = make_dsn(
        host=url.host,
        port=url.port or 5432,
        dbname=url.database,
        user=url.username,
        password=url.password,
        options=url.query.get("options", ""),
    )
    env = {**os.environ, "ACADEMY_WORKER_DSN": dsn, "ACADEMY_WORKER_CHILD": name}
    child = subprocess.Popen(
        [sys.executable, str(script), stage, namespace],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    admitted = None
    try:
        if stage == "graceful":
            assert child.stdout is not None
            with selectors.DefaultSelector() as selector:
                selector.register(child.stdout, selectors.EVENT_READ)
                if not selector.select(10):
                    raise AssertionError("worker admission was not observed")
            admitted = json.loads(child.stdout.readline())
            if admitted != {"admitted": [namespace, "a", 1]}:
                raise AssertionError("unexpected admitted event")
            child.send_signal(signal.SIGTERM)
        output, errors = child.communicate(timeout=15)
        expected = {"after-claim": 81, "after-accept": 82, "graceful": 0}[stage]
        if child.returncode != expected or errors:
            raise AssertionError("worker did not reach the requested owned process boundary")
        report: dict[str, object] = {"exit": child.returncode}
        if stage == "graceful":
            report.update(json.loads(output))
            report["admitted"] = admitted["admitted"] if admitted else None
        elif output:
            raise AssertionError("crash boundary must be quiet")
        until = time.monotonic() + 3
        while time.monotonic() < until:
            with engine.connect() as c:
                active = c.execute(
                    text("SELECT count(*) FROM pg_stat_activity WHERE application_name=:name"),
                    dict(name=name),
                ).scalar_one()
            if active == 0:
                report["connections_gone"] = True
                return report
            time.sleep(0.01)
        raise AssertionError("child database connections remain active")
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=5)  # Reap even if readiness or communication failed.
