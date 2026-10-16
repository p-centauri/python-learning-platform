import hashlib
import pytest
from sqlalchemy import create_engine
from academy_api_depth import InvalidSignature, create_app, matches, verify
from academy_api_depth.support import parse, sign

SECRET = b"s" * 32
BODY = b'{"version":1,"id":"a","revision":1,"value":0}'
NOW = 1700000000


@pytest.mark.parametrize(
    "header,expected",
    [
        (None, False),
        ('"a"', True),
        ('W/"a"', True),
        ("*", True),
        (' "b", W/"a" ', True),
        ('"b"', False),
        ('"a,b"', False),
        ('"a,b", "a"', True),
    ],
)
def test_conditional_comparison(header, expected):
    assert matches(header, '"a"') is expected


@pytest.mark.parametrize(
    "header",
    [
        "",
        "a",
        '*, "a"',
        '"a",',
        '"a" junk',
        'w/"a"',
        '"bad\n"',
        ',"a"',
        ",".join(['"a"'] * 17),
        '"' + ("a" * 1024) + '"',
    ],
)
def test_malformed_bounded_lists_rejected(header):
    with pytest.raises(ValueError):
        matches(header, '"a"')


def test_signature_known_independent_vector_and_raw_bytes():
    import hmac

    message = b"academy-webhook-v1\nn\nd\n1700000000\n" + BODY
    expected = "v1=" + hmac.new(SECRET, message, "sha256").hexdigest()
    assert sign(SECRET, "n", "d", str(NOW), BODY) == expected
    verify(SECRET, "n", "d", str(NOW), expected, BODY, now=NOW)
    with pytest.raises(InvalidSignature):
        verify(SECRET, "n", "d", str(NOW), expected, BODY + b" ", now=NOW)
    assert hashlib.sha256(BODY).hexdigest() != hashlib.sha256(BODY + b" ").hexdigest()


@pytest.mark.parametrize("change", ["namespace", "delivery", "time", "secret", "signature", "old", "future"])
def test_tamper_scope_metadata_and_freshness(change):
    signature = sign(SECRET, "n", "d", str(NOW), BODY)
    values = dict(
        secret=SECRET,
        namespace="n",
        delivery="d",
        timestamp=str(NOW),
        signature=signature,
        body=BODY,
        now=NOW,
    )
    if change == "namespace":
        values["namespace"] = "other"
    if change == "delivery":
        values["delivery"] = "other"
    if change == "time":
        values["timestamp"] = str(NOW + 1)
    if change == "secret":
        values["secret"] = b"x" * 32
    if change == "signature":
        values["signature"] = "v2=" + signature[3:]
    if change == "old":
        values["now"] = NOW + 301
    if change == "future":
        values["now"] = NOW - 301
    with pytest.raises(InvalidSignature):
        verify(**values)


@pytest.mark.parametrize("offset", [-300, 300])
def test_exact_freshness_edges(offset):
    verify(SECRET, "n", "d", str(NOW), sign(SECRET, "n", "d", str(NOW), BODY), BODY, now=NOW + offset)


@pytest.mark.parametrize(
    "body",
    [
        b"[]",
        b'{"version":2,"id":"a","revision":1,"value":0}',
        BODY.replace(b'"value":0', b'"value":true'),
        BODY.replace(b'"revision":1', b'"revision":1.0'),
        BODY.replace(b'"version":1', b'"version":true'),
        BODY[:-1] + b',"value":1}',
        BODY[:-1] + b',"namespace":"other"}',
        b"{",
        b"\xff",
        b" " * 4097,
    ],
)
def test_strict_event_rejection(body):
    with pytest.raises(ValueError):
        parse(body)


def test_zero_valid_exact_datum_and_configuration_no_connection():
    assert parse(BODY).value == 0
    engine = create_engine("postgresql+psycopg2://invalid.invalid/unreachable")
    try:
        tokens = {"local_test_token_12345": "n"}
        secrets = {"n": SECRET}
        app = create_app(engine, tokens, secrets, clock=lambda: NOW)
        tokens.clear()
        secrets.clear()
        assert app and engine.pool.checkedout() == 0
        with pytest.raises(ValueError):
            create_app(engine, {}, {"n": SECRET})
        with pytest.raises(ValueError):
            create_app(engine, {"local_test_token_12345": "n"}, {"n": b"short"})
    finally:
        engine.dispose()
