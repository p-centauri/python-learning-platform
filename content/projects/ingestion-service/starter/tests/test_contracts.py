import asyncio
from dataclasses import FrozenInstanceError
import json
import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import URL, event
from academy_ingestion_service import Cursor, Datum, create_app, make_engine
from academy_ingestion_service.auth import authorize
from academy_ingestion_service.contracts import AuthenticationRequired, BatchInput, PermissionDenied

TOKEN = "a" * 32
OTHER = "b" * 32


def request(app, method, path, *, token=TOKEN, body=None, params=None, authorization=None):
    async def send():
        headers = {}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        if authorization is not None:
            headers["Authorization"] = authorization
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://local"
        ) as client:
            return await client.request(method, path, headers=headers, json=body, params=params)

    return asyncio.run(send())


@pytest.mark.parametrize(
    "payload",
    [
        {"items": [{"id": "a", "revision": True, "value": 1}]},
        {"items": [{"id": "a", "revision": "1", "value": 1}]},
        {"items": [{"id": "a", "revision": 1.0, "value": 1}]},
        {"items": [{"id": "a", "revision": 0, "value": 1}]},
        {"items": [{"id": "a", "revision": 9, "value": 1}]},
        {"items": [{"id": "a", "revision": 1, "value": False}]},
        {"items": [{"id": "a", "revision": 1, "value": -1}]},
        {"items": [{"id": "a", "revision": 1, "value": 1000001}]},
        {"items": [{"id": "a", "revision": 1, "value": "5"}]},
        {"items": [{"id": "a", "revision": 1, "value": 1.0}]},
        {"items": [{"id": "", "revision": 1, "value": 1}]},
        {"items": [{"id": "A", "revision": 1, "value": 1}]},
        {"items": [{"id": "a\n", "revision": 1, "value": 1}]},
        {"items": [{"id": "a" * 33, "revision": 1, "value": 1}]},
        {"items": [{"id": "a", "revision": 1, "value": None}]},
        {"items": [{"id": "a", "revision": 1, "value": 1, "namespace": "other"}]},
        {"items": [], "extra": 1},
        {"items": {}},
        {},
        {"items": [{"id": "a", "revision": 1, "value": 1}] * 65},
    ],
)
def test_strict_payload(payload):
    with pytest.raises(ValidationError):
        BatchInput.model_validate_json(json.dumps(payload))


def test_zero_empty_and_frozen_domains():
    assert BatchInput.model_validate({"items": []}).items == []
    row = Datum("a", 1, 0)
    cursor = Cursor("a", 8)
    assert row.value == 0 and cursor.revision == 8
    with pytest.raises(FrozenInstanceError):
        row.value = 9


@pytest.mark.parametrize(
    "id,revision,value", [("A", 1, 0), ("a", True, 0), ("a", 1, False), ("a", 9, 0), ("a", 1, -1)]
)
def test_domain_validation(id, revision, value):
    with pytest.raises(ValueError):
        Datum(id, revision, value)


@pytest.mark.parametrize(
    "header",
    [
        None,
        "",
        "Basic " + TOKEN,
        "Bearer unknown",
        "Bearer " + OTHER,
        "Bearer  " + TOKEN,
        "Bearer " + TOKEN + " ",
        "Bearer é" * 20,
    ],
)
def test_authentication_required(header):
    with pytest.raises(AuthenticationRequired):
        authorize({TOKEN: "feed"}, header, "feed")


def test_authentication_and_permission_are_separate():
    assert authorize({TOKEN: "feed"}, "bearer " + TOKEN, "feed") == "feed"
    with pytest.raises(PermissionDenied):
        authorize({TOKEN: "feed"}, "Bearer " + TOKEN, "other")
    with pytest.raises(ValueError):
        authorize({TOKEN: "feed"}, "Bearer " + TOKEN, "Invalid")


@pytest.mark.parametrize(
    "tokens",
    [{}, {"short": "feed"}, {TOKEN: "Invalid"}, {TOKEN: ""}, {str(n) * 32: "feed" for n in range(9)}],
)
def test_bad_configuration(tokens):
    engine = make_engine(URL.create("postgresql+psycopg2", host="127.0.0.1", port=1))
    try:
        with pytest.raises(ValueError):
            create_app(engine, tokens)
    finally:
        engine.dispose()


def test_factory_and_rejected_requests_do_not_touch_database(caplog):
    engine = make_engine(URL.create("postgresql+psycopg2", host="127.0.0.1", port=1))
    touched = []

    @event.listens_for(engine, "do_connect")
    def connect(*args):
        touched.append(True)
        raise AssertionError("unauthorized request reached the database")

    original = {TOKEN: "feed"}
    try:
        app = create_app(engine, original)
        original.clear()
        assert not touched
        health = request(app, "GET", "/health", token=None)
        assert health.status_code == 200 and health.json() == {"status": "alive"}
        missing = request(app, "GET", "/namespaces/feed/readings", token=None)
        assert missing.status_code == 401 and missing.headers["www-authenticate"] == "Bearer"
        denied = request(app, "POST", "/namespaces/other/readings", body={"items": []})
        assert denied.status_code == 403
        invalid = request(app, "POST", "/namespaces/feed/readings", body={"items": [{"value": TOKEN}]})
        assert invalid.status_code == 422 and invalid.json() == {"detail": "invalid request"}
        with caplog.at_level("INFO", logger="academy_ingestion_service"):
            empty = request(app, "POST", "/namespaces/feed/readings", body={"items": []})
        assert empty.status_code == 200 and empty.json() == {"observed": 0, "inserted": 0, "duplicates": 0}
        assert not touched
        assert len(empty.headers["x-request-id"]) == 32 and empty.headers["cache-control"] == "no-store"
        assert TOKEN not in empty.text + str(caplog.records) + json.dumps(app.openapi())
        assert all(record.getMessage() == "request_completed" for record in caplog.records)
    finally:
        engine.dispose()


def test_engine_rejects_sqlite():
    with pytest.raises(ValueError):
        make_engine(URL.create("sqlite", database=":memory:"))


def test_local_dsn_options_are_not_silently_dropped():
    from academy_ingestion_service.database import url_from_dsn

    with pytest.raises(ValueError):
        url_from_dsn("host=127.0.0.1 user=lab dbname=disposable sslmode=require")
    with pytest.raises(ValueError):
        url_from_dsn("user=lab")
    url = url_from_dsn("host=127.0.0.1 user=lab dbname=disposable options=-csearch_path=owned")
    assert url.query["options"] == "-csearch_path=owned"
