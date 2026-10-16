"""Supplied trusted adapter; borrow the configured client, own each append connection."""

from typing import Protocol, cast
from redis import Redis
from redis.exceptions import ResponseError
from .contracts import Batch, Entry, UnconfirmedAppend, entry_id, stream
from academy_ingestion_service.contracts import field


class Command(Protocol):
    def __call__(self, *args: str | bytes | int) -> object: ...


def array(value: object) -> list[object] | tuple[object, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("unexpected broker array")
    return value


def one_entry(value: object) -> Entry | None:
    entries = array(value)
    if not entries:
        return None
    if len(entries) != 1:
        raise ValueError("expected at most one entry")
    row = array(entries[0])
    if len(row) != 2 or type(row[0]) is not bytes or type(row[1]) is not dict:
        raise ValueError("unexpected stream entry")
    fields = row[1]
    if set(fields) != {b"payload"} or type(fields[b"payload"]) is not bytes:
        raise ValueError("expected one exact payload field")
    return Entry(row[0], fields[b"payload"])


class RedisBroker:
    def __init__(self, client: Redis) -> None:
        self.client = client

    def setup(self, namespace: str, group: str) -> None:
        field(group)
        try:
            self.client.xgroup_create(stream(namespace), group, id="0-0", mkstream=True)
        except ResponseError as error:
            if not str(error).startswith("BUSYGROUP "):
                raise

    def append(self, namespace: str, payload: bytes) -> bytes:
        key = stream(namespace)
        Entry(b"0-0", payload)
        connection = Redis(connection_pool=self.client.connection_pool, single_connection_client=True)
        try:
            command = cast(Command, connection.execute_command)  # Narrow untyped redis-py boundary.
            # Dedicated physical connection: WAITAOF covers this XADD's preceding write.
            id: object = command("XADD", key, "*", "payload", payload)
            if type(id) is not bytes:
                raise UnconfirmedAppend("broker did not return a stream id")
            entry_id(id)
            reply: object = command("WAITAOF", 1, 0, 1000)
            counts = array(reply)
            if len(counts) != 2 or type(counts[0]) is not int or counts[0] < 1:
                raise UnconfirmedAppend("local AOF flush was not confirmed; append may exist")
            return id

        finally:
            connection.close()  # Release the dedicated lease; leave the borrowed pool open.

    def take(
        self, namespace: str, group: str, consumer: str, *, recover: bool, idle_ms: int, cursor: bytes
    ) -> Batch:
        key = stream(namespace)
        field(group)
        field(consumer)
        entry_id(cursor)
        if type(recover) is not bool or type(idle_ms) is not int or not 0 <= idle_ms <= 60000:
            raise ValueError("invalid recovery policy")
        if recover:
            reply: object = self.client.xautoclaim(key, group, consumer, idle_ms, cursor, count=1)
            items = array(reply)
            if len(items) != 3 or type(items[0]) is not bytes:
                raise ValueError("unexpected recovery reply")
            entry_id(items[0])
            deleted = array(items[2])
            ids = []
            for id in deleted:
                if type(id) is not bytes:
                    raise ValueError("invalid deleted entry id")
                entry_id(id)
                ids.append(id)
            return Batch(one_entry(items[1]), items[0], tuple(ids))
        reply = self.client.xreadgroup(group, consumer, {key: ">"}, count=1)
        streams = array(reply)
        if not streams:
            return Batch(None)
        if len(streams) != 1:
            raise ValueError("expected one scoped stream")
        row = array(streams[0])
        if len(row) != 2 or row[0] != key.encode("ascii"):
            raise ValueError("broker returned another scope")
        return Batch(one_entry(row[1]))

    def ack(self, namespace: str, group: str, id: bytes) -> bool:
        field(group)
        entry_id(id)
        count: object = self.client.xack(stream(namespace), group, id)
        if type(count) is not int or count not in (0, 1):
            raise ValueError("unexpected acknowledgment count")
        return count == 1
