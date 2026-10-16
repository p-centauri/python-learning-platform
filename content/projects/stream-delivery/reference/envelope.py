import json
from academy_durable_outbox import Event
from academy_durable_outbox.contracts import validated
from academy_ingestion_service.contracts import field
from .contracts import InvalidEnvelope


def encode(event: Event, *, version: int = 2) -> bytes:
    item = validated(event)
    if type(version) is not int or version not in (1, 2):
        raise InvalidEnvelope("unsupported exact envelope version")
    value: dict[str, object]
    if version == 1:
        value = dict(schema=1, namespace=item.namespace, id=item.id, revision=item.revision, value=item.value)
    else:
        value = dict(
            schema=2,
            kind="reading",
            key=dict(namespace=item.namespace, id=item.id, revision=item.revision),
            data=dict(value=item.value),
        )
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in items:
        if key in result:
            raise InvalidEnvelope("duplicate JSON field")
        result[key] = value
    return result


def constant(value: str) -> object:
    raise InvalidEnvelope("non-finite JSON constant")


def mapping(value: object, keys: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise InvalidEnvelope("unexpected envelope shape")
    return value


def decode(payload: bytes, namespace: str, /) -> Event:
    field(namespace)
    if type(payload) is not bytes or not 1 <= len(payload) <= 1024:
        raise InvalidEnvelope("expected 1..1024 exact bytes")
    try:
        value: object = json.loads(payload.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
        if type(value) is not dict or type(value.get("schema")) is not int:
            raise InvalidEnvelope("expected exact integer schema")
        if value["schema"] == 1:
            source = mapping(value, {"schema", "namespace", "id", "revision", "value"})
            number = source["value"]
        elif value["schema"] == 2:
            outer = mapping(value, {"schema", "kind", "key", "data"})
            if outer["kind"] != "reading":
                raise InvalidEnvelope("unsupported event kind")
            source = mapping(outer["key"], {"namespace", "id", "revision"})
            number = mapping(outer["data"], {"value"})["value"]
        else:
            raise InvalidEnvelope("unsupported envelope version")
        # Runtime narrowing, followed by the prior exact-value Event contract.
        ns, id, rev = source["namespace"], source["id"], source["revision"]
        if type(ns) is not str or type(id) is not str or type(rev) is not int or type(number) is not int:
            raise InvalidEnvelope("wrong event field types")
        item = Event(ns, id, rev, number)
        if item.namespace != namespace:
            raise InvalidEnvelope("event scope differs from the authorized stream")
        return item
    except (ValueError, RecursionError) as error:
        raise InvalidEnvelope("invalid bounded event envelope") from error
