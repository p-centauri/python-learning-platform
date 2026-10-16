import hmac
import re
from sqlalchemy import Engine, select, text
from sqlalchemy.dialects.postgresql import insert
from academy_ingestion_service import Datum
from academy_ingestion_service.contracts import ConflictingDatum, field
from academy_ingestion_service.models import RecordRow, SourceRow
from .contracts import DeliveryConflict, InvalidSignature
from .support import key, message


_TAG = re.compile(r'(?:W/)?"[\x21\x23-\x7e\x80-\xff]*"')


def matches(header: str | None, etag: str) -> bool:
    if type(etag) is not str or _TAG.fullmatch(etag) is None or etag.startswith("W/"):
        raise ValueError("expected strong representation tag")
    if header is None:
        return False
    if type(header) is not str or len(header) > 1024:
        raise ValueError("invalid conditional header")
    value = header.strip(" \t")
    if value == "*":
        return True
    if not value:
        raise ValueError("invalid conditional header")
    tags: list[str] = []
    position = 0
    for _ in range(16):
        found = _TAG.match(value, position)
        if found is None:
            raise ValueError("invalid conditional header")
        tags.append(found.group().removeprefix("W/"))
        position = found.end()
        while position < len(value) and value[position] in " \t":
            position += 1
        if position == len(value):
            return etag in tags
        if value[position] != ",":
            raise ValueError("invalid conditional header")
        position += 1
        while position < len(value) and value[position] in " \t":
            position += 1
    raise ValueError("too many conditional tags")


def verify(
    secret: bytes, namespace: str, delivery: str, timestamp: str, signature: str, body: bytes, *, now: int
) -> None:
    key(secret)  # Configuration/programmer errors remain errors, not forged-client failures.
    if type(now) is not int or now < 1:
        raise ValueError("invalid clock")
    try:
        payload = message(namespace, delivery, timestamp, body)
    except ValueError:
        raise InvalidSignature() from None
    if type(signature) is not str or re.fullmatch(r"v1=[0-9a-f]{64}", signature) is None:
        raise InvalidSignature()
    if abs(now - int(timestamp)) > 300:
        raise InvalidSignature()
    expected = hmac.new(secret, payload, "sha256").hexdigest()
    if not hmac.compare_digest(expected, signature[3:]):
        raise InvalidSignature()


def accept(engine: Engine, namespace: str, delivery: str, digest: str, datum: Datum) -> bool:
    field(namespace)
    field(delivery)
    if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError("invalid body digest")
    if type(datum) is not Datum:
        raise ValueError("expected exact Datum")
    Datum(datum.id, datum.revision, datum.value)
    if engine.dialect.name != "postgresql":
        raise ValueError("PostgreSQL required")
    with engine.begin() as connection:
        connection.execute(text("SET LOCAL lock_timeout = '250ms'"))
        connection.execute(text("SET LOCAL statement_timeout = '1000ms'"))
        inserted = connection.execute(
            text("""INSERT INTO api_webhook_receipt
            (namespace, delivery_id, body_digest) VALUES (:n,:d,:h)
            ON CONFLICT (namespace,delivery_id) DO NOTHING RETURNING body_digest"""),
            dict(n=namespace, d=delivery, h=digest),
        ).scalar_one_or_none()
        if inserted is None:
            stored = connection.execute(
                text("""SELECT body_digest FROM api_webhook_receipt
                WHERE namespace=:n AND delivery_id=:d FOR KEY SHARE"""),
                dict(n=namespace, d=delivery),
            ).scalar_one_or_none()
            if stored != digest:
                raise DeliveryConflict()
            return True
        connection.execute(insert(SourceRow).values(namespace=namespace).on_conflict_do_nothing())
        value = connection.execute(
            insert(RecordRow)
            .values(namespace=namespace, id=datum.id, revision=datum.revision, value=datum.value)
            .on_conflict_do_nothing(index_elements=[RecordRow.namespace, RecordRow.id, RecordRow.revision])
            .returning(RecordRow.value)
        ).scalar_one_or_none()
        if value is None:
            stored_value = connection.execute(
                select(RecordRow.value)
                .where(
                    RecordRow.namespace == namespace,
                    RecordRow.id == datum.id,
                    RecordRow.revision == datum.revision,
                )
                .with_for_update(read=True)
            ).scalar_one_or_none()
            if stored_value != datum.value:
                raise ConflictingDatum()
    return False
