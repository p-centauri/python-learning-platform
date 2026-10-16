from sqlalchemy import Engine
from academy_durable_outbox import consume
from academy_ingestion_service.contracts import field
from .contracts import Broker, Result, entry_id
from .envelope import decode


def deliver(
    engine: Engine,
    broker: Broker,
    namespace: str,
    group: str,
    consumer: str,
    /,
    *,
    recover: bool = False,
    idle_ms: int = 100,
    cursor: bytes = b"0-0",
) -> Result:
    field(namespace)
    field(group)
    field(consumer)
    entry_id(cursor)
    if type(recover) is not bool or type(idle_ms) is not int or not 0 <= idle_ms <= 60000:
        raise ValueError("invalid recovery policy")
    batch = broker.take(namespace, group, consumer, recover=recover, idle_ms=idle_ms, cursor=cursor)
    if batch.entry is None:
        return Result(None, None, False, batch.cursor, batch.deleted)
    item = decode(batch.entry.payload, namespace)
    consume(engine, item)  # Owned inbox/effect transaction commits before stream acknowledgment.
    confirmed = broker.ack(namespace, group, batch.entry.id)
    return Result(item, batch.entry.id, confirmed, batch.cursor, batch.deleted)
