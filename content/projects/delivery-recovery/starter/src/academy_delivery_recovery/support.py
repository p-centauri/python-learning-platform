"""Supplied byte-client adapter. Script guards only the current Redis groups, not PostgreSQL."""

from importlib.resources import files
from typing import cast
from academy_stream_delivery import RedisBroker
from academy_stream_delivery.contracts import Entry, entry_id, stream
from academy_stream_delivery.transport import Command, one_entry
from .contracts import Pruned


def selected_entry(broker: RedisBroker, namespace: str, id: bytes) -> Entry | None:
    if type(broker) is not RedisBroker:
        raise ValueError("expected the supplied exact RedisBroker")
    entry_id(id)
    return one_entry(broker.client.xrange(stream(namespace), min=id, max=id, count=1))


def remove_payload(broker: RedisBroker, namespace: str, entry: Entry) -> Pruned:
    script = files("academy_delivery_recovery").joinpath("prune.lua").read_text()
    command = cast(Command, broker.client.execute_command)
    reply = command("EVAL", script, 1, stream(namespace), entry.id, entry.payload)
    if type(reply) is not bytes:
        raise ValueError("unexpected broker guard reply")
    return Pruned(reply.decode("ascii"))
