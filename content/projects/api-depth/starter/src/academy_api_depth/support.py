from dataclasses import asdict
from hashlib import sha256
import hmac
import json
import re
from typing import Any
from sqlalchemy import Engine, select, text
from academy_ingestion_service import Datum
from academy_ingestion_service.contracts import field
from academy_ingestion_service.models import RecordRow


def key(secret: bytes) -> bytes:
    if type(secret) is not bytes or not 32 <= len(secret) <= 64:
        raise ValueError("invalid signing configuration")
    return secret


def message(namespace: str, delivery: str, timestamp: str, body: bytes) -> bytes:
    field(namespace)
    field(delivery)
    if type(timestamp) is not str or re.fullmatch(r"[1-9][0-9]{0,9}", timestamp) is None:
        raise ValueError("invalid timestamp")
    if type(body) is not bytes or not 1 <= len(body) <= 4096:
        raise ValueError("invalid body size")
    return ("academy-webhook-v1\n" + namespace + "\n" + delivery + "\n" + timestamp + "\n").encode(
        "ascii"
    ) + body


def sign(secret: bytes, namespace: str, delivery: str, timestamp: str, body: bytes) -> str:
    """Sender helper for this academy protocol; not a GitHub/Stripe signature format."""
    return "v1=" + hmac.new(key(secret), message(namespace, delivery, timestamp, body), "sha256").hexdigest()


def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate JSON key")
        result[name] = value
    return result


def parse(body: bytes) -> Datum:
    if type(body) is not bytes or not 1 <= len(body) <= 4096:
        raise ValueError("invalid body size")
    try:
        value = json.loads(body.decode("utf-8"), object_pairs_hook=unique)
    except (ValueError, RecursionError) as error:
        raise ValueError("invalid event") from error
    if type(value) is not dict or set(value) != {"version", "id", "revision", "value"}:
        raise ValueError("invalid event fields")
    if type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("unsupported event version")
    return Datum(value["id"], value["revision"], value["value"])


def representation(engine: Engine, namespace: str, limit: int) -> tuple[bytes, str]:
    field(namespace)
    if type(limit) is not int or not 1 <= limit <= 32:
        raise ValueError("invalid page limit")
    with engine.connect() as connection, connection.begin():
        connection.execute(text("SET TRANSACTION READ ONLY"))
        connection.execute(text("SET LOCAL lock_timeout = '250ms'"))
        connection.execute(text("SET LOCAL statement_timeout = '1000ms'"))
        rows = connection.execute(
            select(RecordRow.id, RecordRow.revision, RecordRow.value)
            .where(RecordRow.namespace == namespace)
            .order_by(RecordRow.id, RecordRow.revision)
            .limit(limit + 1)
        ).all()
        items = [asdict(Datum(row.id, row.revision, row.value)) for row in rows[:limit]]
        cursor = dict(id=items[-1]["id"], revision=items[-1]["revision"]) if len(rows) > limit else None
        body = json.dumps(
            dict(version=1, namespace=namespace, limit=limit, items=items, next_cursor=cursor),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
    return body, '"' + sha256(body).hexdigest() + '"'
