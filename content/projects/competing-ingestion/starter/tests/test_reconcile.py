import pytest
from academy_ingestion_service import Datum
from academy_competing_ingestion import Reconciliation, reconcile
from academy_ingestion_service.contracts import ConflictingDatum


def test_observation_states_prioritize_conflict():
    row = Datum("a", 1, 0)
    assert Reconciliation(1, (), ()).state == "complete"
    assert Reconciliation(0, (row,), ()).state == "missing"
    assert Reconciliation(0, (row,), (row,)).state == "conflict"


@pytest.mark.parametrize(
    "namespace,rows", [("Bad", []), ("feed", [object()]), ("feed", [Datum("a", 1, 0)] * 65)]
)
def test_validation_before_database(namespace, rows):
    with pytest.raises(ValueError):
        reconcile(object(), namespace, rows)


def test_contradictory_reconciliation_before_database():
    with pytest.raises(ConflictingDatum):
        reconcile(object(), "feed", [Datum("a", 1, 1), Datum("a", 1, 2)])
