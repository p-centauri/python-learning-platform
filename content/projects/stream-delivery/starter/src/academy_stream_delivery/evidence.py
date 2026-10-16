"""Supplied owned POSIX process/restart observations; secrets never enter reports."""

import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
from psycopg2.extensions import make_dsn
from sqlalchemy import Engine, text
from .transport import RedisBroker, array
from .contracts import stream


def pending(broker: RedisBroker, namespace: str) -> int:
    result: object = broker.client.xpending(stream(namespace), "effects")
    if type(result) is not dict or type(result.get("pending")) is not int:
        raise ValueError("unexpected pending report")
    count: int = result["pending"]
    return count


def wait_idle(broker: RedisBroker, namespace: str, minimum: int = 100) -> None:
    until = time.monotonic() + 3
    while time.monotonic() < until:
        reply: object = broker.client.xpending_range(stream(namespace), "effects", "-", "+", 1)
        rows = array(reply)
        if rows and type(rows[0]) is dict:
            elapsed = rows[0].get("time_since_delivered")
            if type(elapsed) is int and elapsed >= minimum:
                return
        time.sleep(0.01)  # Pace an actual broker observation, not assumed scheduling.
    raise AssertionError("pending idle time was not observed")


def restart_owned(broker: RedisBroker) -> None:
    name = os.environ.get("ACADEMY_BROKER_CONTAINER", "")
    if not re.fullmatch(r"academy-stream-[a-f0-9]{32}", name):
        raise ValueError("restart requires the explicitly owned broker container")
    subprocess.run(["docker", "restart", "--timeout", "5", name], check=True, capture_output=True, timeout=20)
    broker.client.connection_pool.disconnect()
    until = time.monotonic() + 5
    while time.monotonic() < until:
        try:
            if broker.client.ping():
                return
        except Exception:
            pass
        time.sleep(0.05)
    raise AssertionError("owned broker restart did not become ready")


def crash(engine: Engine, broker: RedisBroker, script: Path, stage: str, namespace: str) -> int:
    expected = {"after-append": 91, "after-effect": 92}[stage]
    name = "stream-child-" + uuid.uuid4().hex
    url = engine.url
    dsn = make_dsn(
        host=url.host,
        port=url.port or 5432,
        dbname=url.database,
        user=url.username,
        password=url.password,
        options=url.query.get("options", ""),
    )
    env = {**os.environ, "ACADEMY_STREAM_DSN": dsn, "ACADEMY_STREAM_CHILD": name}
    result = subprocess.run(
        [sys.executable, str(script), stage, namespace], env=env, capture_output=True, text=True, timeout=15
    )
    if result.returncode != expected or result.stdout or result.stderr:
        raise AssertionError("child did not reach the specified quiet exit boundary")
    until = time.monotonic() + 3
    while time.monotonic() < until:
        with engine.connect() as connection:
            active = connection.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE application_name=:name"), dict(name=name)
            ).scalar_one()
        clients: object = broker.client.client_list()
        broker_active = any(type(item) is dict and item.get("name") == name for item in array(clients))
        if active == 0 and not broker_active:
            return result.returncode
        time.sleep(0.01)
    raise AssertionError("child database/broker connections remain active")
