import json
import pytest
from academy_durable_outbox import Event
from academy_stream_delivery import InvalidEnvelope, decode, encode


@pytest.mark.parametrize("version", [1, 2])
@pytest.mark.parametrize("revision,value", [(1, 0), (8, 1000000), (2, 7)])
def test_versions_preserve_the_same_fact(version, revision, value):
    item = Event("scope", "a", revision, value)
    payload = encode(item, version=version)
    assert type(payload) is bytes and len(payload) <= 1024
    result = decode(payload, "scope")
    assert result == item and result is not item and result.key == item.key
    assert payload == encode(item, version=version)


@pytest.mark.parametrize("bad", [True, 0, 3, 1.0, "2"])
def test_encode_supported_exact_versions(bad):
    with pytest.raises(ValueError):
        encode(Event("scope", "a", 1, 7), version=bad)


@pytest.mark.parametrize(
    "bad",
    [
        b"",
        b" " * 1025,
        "{}",
        None,
        b"\xff",
        b"[]",
        b"null",
        b"{}",
        b"{",
        b'{"schema":true}',
        b'{"schema":3}',
        b'{"schema":1.0}',
        b'{"schema":1,"schema":1,"namespace":"scope","id":"a","revision":1,"value":7}',
        b'{"schema":1,"namespace":"scope","id":"a","revision":1,"value":NaN}',
        b'{"schema":1,"namespace":"scope","id":"a","revision":1,"value":Infinity}',
        b'{"schema":1,"namespace":"scope","id":"a","revision":1,"value":7,"extra":0}',
        b'{"schema":2,"kind":"unknown","key":{},"data":{}}',
        b'{"schema":2,"kind":"reading","key":{"namespace":"scope","id":"a","revision":1},"data":{"value":7,"value":8}}',
    ],
)
def test_invalid_bounded_json_and_shapes(bad):
    with pytest.raises(InvalidEnvelope):
        decode(bad, "scope")


@pytest.mark.parametrize(
    "field,bad",
    [
        ("namespace", "Upper"),
        ("namespace", "other"),
        ("id", "a_b"),
        ("revision", True),
        ("revision", 0),
        ("revision", 9),
        ("value", True),
        ("value", -1),
        ("value", 1000001),
    ],
)
def test_v1_exact_fields_and_scope(field, bad):
    value = dict(schema=1, namespace="scope", id="a", revision=1, value=7)
    value[field] = bad
    with pytest.raises(InvalidEnvelope):
        decode(json.dumps(value).encode(), "scope")


def test_frozen_bypass_is_revalidated_before_encoding():
    item = Event("scope", "a", 1, 7)
    object.__setattr__(item, "value", True)
    with pytest.raises(ValueError):
        encode(item)


def test_version_two_extra_nested_field_is_rejected():
    value = json.loads(encode(Event("scope", "a", 1, 7)))
    value["key"]["tenant"] = "other"
    with pytest.raises(InvalidEnvelope):
        decode(json.dumps(value).encode(), "scope")
