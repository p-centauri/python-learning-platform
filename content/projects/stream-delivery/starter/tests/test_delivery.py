from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import Engine
from redis import Redis
from academy_durable_outbox import Event
from academy_stream_delivery import Batch, Entry, InvalidEnvelope, RedisBroker, UnconfirmedAppend
from academy_stream_delivery import deliver, encode, publisher


class FakeBroker:
    def __init__(self, payload=None):
        self.batch = Batch(Entry(b"1-0", payload)) if payload else Batch(None, b"8-0")
        self.calls = []

    def append(self, namespace, payload):
        self.calls.append("append")
        return b"1-0"

    def take(self, namespace, group, consumer, **policy):
        self.calls.append(("take", namespace, policy))
        return self.batch

    def ack(self, namespace, group, id):
        self.calls.append("ack")
        return True


def test_effect_commits_before_ack():
    item = Event("scope", "a", 1, 7)
    broker = FakeBroker(encode(item))
    engine = MagicMock(spec=Engine)
    with patch(
        "academy_stream_delivery.delivery.consume", side_effect=lambda *_: broker.calls.append("effect")
    ):
        result = deliver(engine, broker, "scope", "effects", "first")
    assert result.event == item and result.acknowledged and result.entry_id == b"1-0"
    assert broker.calls[-2:] == ["effect", "ack"]
    engine.dispose.assert_not_called()


def test_effect_failure_is_original_and_not_acknowledged():
    broker = FakeBroker(encode(Event("scope", "a", 1, 7)))
    failure = RuntimeError("owned effect failure")
    with patch("academy_stream_delivery.delivery.consume", side_effect=failure):
        with pytest.raises(RuntimeError) as caught:
            deliver(MagicMock(spec=Engine), broker, "scope", "effects", "first")
    assert caught.value is failure and "ack" not in broker.calls


def test_invalid_envelope_never_reaches_effect_or_ack():
    broker = FakeBroker(b"{}")
    with patch("academy_stream_delivery.delivery.consume") as consume:
        with pytest.raises(InvalidEnvelope):
            deliver(MagicMock(spec=Engine), broker, "scope", "effects", "first")
        consume.assert_not_called()
    assert "ack" not in broker.calls


def test_no_returned_entry_preserves_recovery_cursor():
    broker = FakeBroker()
    result = deliver(
        MagicMock(spec=Engine), broker, "scope", "effects", "first", recover=True, idle_ms=100, cursor=b"7-0"
    )
    assert result.event is None and result.cursor == b"8-0" and not result.acknowledged
    assert broker.calls[0][2] == dict(recover=True, idle_ms=100, cursor=b"7-0")


@pytest.mark.parametrize(
    "options", [{"recover": 1}, {"idle_ms": True}, {"idle_ms": -1}, {"idle_ms": 60001}, {"cursor": b"bad"}]
)
def test_policy_invalid_before_broker(options):
    broker = FakeBroker()
    with pytest.raises(ValueError):
        deliver(MagicMock(spec=Engine), broker, "scope", "effects", "first", **options)
    assert broker.calls == []


def test_append_and_flush_share_owned_connection():
    client = MagicMock(spec=Redis)
    client.connection_pool = MagicMock()
    one = MagicMock(spec=Redis)
    one.execute_command.side_effect = [b"1-0", [1, 0]]
    broker = RedisBroker(client)
    with patch("academy_stream_delivery.transport.Redis", return_value=one) as factory:
        assert publisher(broker)(Event("scope", "a", 1, 0)).event.value == 0
        factory.assert_called_once_with(connection_pool=client.connection_pool, single_connection_client=True)
    assert [call.args[0] for call in one.execute_command.call_args_list] == ["XADD", "WAITAOF"]
    client.close.assert_not_called()
    one.close.assert_called_once()


@pytest.mark.parametrize("reply", [[0, 0], [True, 0], [], None])
def test_unconfirmed_flush_cannot_authorize_acceptance(reply):
    client = MagicMock(spec=Redis)
    client.connection_pool = MagicMock()
    one = MagicMock(spec=Redis)
    one.execute_command.side_effect = [b"1-0", reply]
    with patch("academy_stream_delivery.transport.Redis", return_value=one):
        with pytest.raises((ValueError, UnconfirmedAppend)):
            publisher(RedisBroker(client))(Event("scope", "a", 1, 7))
    assert one.execute_command.call_count == 2


@pytest.mark.parametrize("id", [None, 1, b"", b"bad"])
def test_missing_stream_receipt_cannot_authorize_acceptance(id):
    client = MagicMock(spec=Redis)
    client.connection_pool = MagicMock()
    one = MagicMock(spec=Redis)
    one.execute_command.return_value = id
    with patch("academy_stream_delivery.transport.Redis", return_value=one):
        with pytest.raises((ValueError, UnconfirmedAppend)):
            publisher(RedisBroker(client))(Event("scope", "a", 1, 7))
    assert one.execute_command.call_count == 1


def test_invalid_event_does_not_open_publish_connection():
    client = MagicMock(spec=Redis)
    client.connection_pool = MagicMock()
    with pytest.raises(ValueError):
        publisher(RedisBroker(client))(object())
    client.execute_command.assert_not_called()
