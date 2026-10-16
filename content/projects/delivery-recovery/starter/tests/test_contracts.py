from unittest.mock import Mock
import pytest
from academy_durable_outbox import Event
from academy_delivery_recovery import DeadJob, Pruned, inspect_dead, prune, redrive


@pytest.mark.parametrize("limit", [True, 0, 65, 1.0])
def test_inspection_rejects_unbounded_or_wrong_type_before_connection(limit):
    engine = Mock()
    with pytest.raises(ValueError):
        inspect_dead(engine, "feed", limit=limit)
    engine.connect.assert_not_called()


@pytest.mark.parametrize("approval", [False, 1, "yes", None])
def test_explicit_approval_before_connection(approval):
    engine = Mock()
    with pytest.raises(ValueError):
        redrive(engine, DeadJob(Event("feed", "a", 1, 0), 1, "poison", 3), approve=approval)
    engine.connect.assert_not_called()


@pytest.mark.parametrize("loss", [False, 1, "yes"])
def test_explicit_retention_loss_before_broker_or_database(loss):
    with pytest.raises(ValueError):
        prune(Mock(), Mock(), "feed", b"1-0", allow_loss=loss)


def test_exhausted_budget_is_not_reset_or_connected():
    engine = Mock()
    assert not redrive(engine, DeadJob(Event("feed", "a", 1, 0), 3, "exhausted", 3), approve=True)
    engine.connect.assert_not_called()


def test_tampered_frozen_snapshot_revalidated_before_connection():
    job = DeadJob(Event("feed", "a", 1, 0), 1, "poison", 3)
    object.__setattr__(job.event, "value", True)
    with pytest.raises(ValueError):
        redrive(Mock(), job, approve=True)


def test_unknown_snapshot_class_and_reply_are_not_accepted():
    with pytest.raises(ValueError):
        redrive(Mock(), Mock(), approve=True)
    with pytest.raises(ValueError):
        Pruned("success")
