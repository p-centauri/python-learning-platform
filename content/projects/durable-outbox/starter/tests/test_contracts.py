from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock
from sqlalchemy import Engine, create_engine
import pytest
from academy_ingestion_service import Datum
from academy_ingestion_service.contracts import ConflictingDatum
from academy_durable_outbox import Accepted, Event, consume, publish_one, record
from academy_durable_outbox.contracts import validated


class TextSubclass(str):
    pass


class EventSubclass(Event):
    pass


@pytest.mark.parametrize("field", ["namespace", "id"])
@pytest.mark.parametrize("bad", ["", "Upper", "-a", "a_b", "a" * 33, TextSubclass("abc")])
def test_strict_identity_fields(field, bad):
    values = dict(namespace="scope", id="a", revision=1, value=0)
    values[field] = bad
    with pytest.raises(ValueError):
        Event(**values)


@pytest.mark.parametrize("bad", [True, 0, 9, 1.0, "1"])
def test_strict_revision(bad):
    with pytest.raises(ValueError):
        Event("scope", "a", bad, 0)


@pytest.mark.parametrize("bad", [True, -1, 1000001, 0.0, "0"])
def test_strict_value(bad):
    with pytest.raises(ValueError):
        Event("scope", "a", 1, bad)


@pytest.mark.parametrize("bad", [None, Datum("a", 1, 0), {}, EventSubclass("scope", "a", 1, 0)])
def test_confirmation_requires_exact_event(bad):
    with pytest.raises(ValueError):
        Accepted(bad)


@pytest.mark.parametrize("revision,value", [(1, 0), (8, 1000000), (2, 7)])
def test_stable_identity_excludes_delivery_attempt(revision, value):
    item = Event("scope", "a", revision, value)
    assert item.key == ("scope", "a", revision)
    assert validated(item) == item and validated(item) is not item
    assert Accepted(item).event == item


def test_frozen_is_not_a_validation_boundary():
    item = Event("scope", "a", 1, 0)
    with pytest.raises(FrozenInstanceError):
        item.value = 7
    object.__setattr__(item, "value", True)
    with pytest.raises(ValueError):
        validated(item)
    with pytest.raises(ValueError):
        Accepted(item)


@pytest.mark.parametrize("bad", [None, {}, iter(()), [Datum("a", 1, 0)] * 65, [object()]])
def test_record_validates_batch_before_sql(bad):
    engine = MagicMock(spec=Engine)
    with pytest.raises(ValueError):
        record(engine, "scope", bad)
    engine.connect.assert_not_called()


def test_contradictory_batch_rejected_before_sql():
    engine = MagicMock(spec=Engine)
    with pytest.raises(ConflictingDatum):
        record(engine, "scope", [Datum("a", 1, 0), Datum("a", 1, 7)])
    engine.connect.assert_not_called()


@pytest.mark.parametrize("bad", [None, {}, Datum("a", 1, 0), EventSubclass("scope", "a", 1, 0)])
def test_consume_validates_before_sql(bad):
    engine = MagicMock(spec=Engine)
    with pytest.raises(ValueError):
        consume(engine, bad)
    engine.connect.assert_not_called()


@pytest.mark.parametrize(
    "namespace,publisher",
    [("Upper", lambda x: Accepted(x)), ("", lambda x: Accepted(x)), ("scope", None), ("scope", 1)],
)
def test_publish_validates_before_sql(namespace, publisher):
    engine = MagicMock(spec=Engine)
    with pytest.raises(ValueError):
        publish_one(engine, namespace, publisher)
    engine.connect.assert_not_called()


def test_empty_record_does_not_open_connection_but_requires_postgres():
    engine = MagicMock(spec=Engine)
    engine.dialect = MagicMock()
    engine.dialect.name = "postgresql"
    engine.dialect.driver = "psycopg2"
    result = record(engine, "scope", [])
    assert (result.receipt.observed, result.enqueued) == (0, 0)
    engine.connect.assert_not_called()
    sqlite = create_engine("sqlite://")
    try:
        with pytest.raises(ValueError):
            record(sqlite, "scope", [])
    finally:
        sqlite.dispose()
