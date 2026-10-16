from dataclasses import FrozenInstanceError
import pytest
from academy_ingestion_persistence import Reading, snapshot_batch


@pytest.mark.parametrize(
    "namespace,id,revision,value",
    [
        ("", "a", 1, 0),
        ("A", "a", 1, 0),
        ("a_", "a", 1, 0),
        ("é", "a", 1, 0),
        ("a" * 33, "a", 1, 0),
        (None, "a", 1, 0),
        ("a", "", 1, 0),
        ("a", "X", 1, 0),
        ("a", "a\n", 1, 0),
        ("a", "a", True, 0),
        ("a", "a", 0, 0),
        ("a", "a", 9, 0),
        ("a", "a", 1.0, 0),
        ("a", "a", 1, False),
        ("a", "a", 1, -1),
        ("a", "a", 1, 1000001),
        ("a", "a", 1, 1.0),
        ("a", "a", 1, "1"),
    ],
)
def test_invalid_fields(namespace, id, revision, value):
    with pytest.raises(ValueError):
        Reading(namespace, id, revision, value)


@pytest.mark.parametrize("revision,value", [(1, 0), (8, 1000000), (2, 5)])
def test_boundary_values_and_frozen(revision, value):
    row = Reading("feed", "a", revision, value)
    assert snapshot_batch([row]) == (row,)
    assert snapshot_batch([row])[0] is row
    with pytest.raises(FrozenInstanceError):
        row.value = 2


def test_empty_and_one_pass():
    assert snapshot_batch([]) == ()
    row = Reading("feed", "a", 1, 0)
    source = iter([row, row])
    assert snapshot_batch(source) == (row, row)
    assert list(source) == []


def test_overflow_observes_65_without_closing():
    calls = []
    closed = []

    def values():
        try:
            for n in range(66):
                calls.append(n)
                yield Reading("feed", "a", 1, n)
        finally:
            closed.append(True)

    source = values()
    with pytest.raises(ValueError):
        snapshot_batch(source)
    assert calls == list(range(65)) and not closed
    source.close()
    assert closed == [True]


def test_original_iterator_error():
    error = RuntimeError("input failure")

    def values():
        yield Reading("feed", "a", 1, 0)
        raise error

    with pytest.raises(RuntimeError) as result:
        snapshot_batch(values())
    assert result.value is error


@pytest.mark.parametrize("item", [None, {}, ("feed", "a", 1, 0), 1])
def test_reject_wrong_row(item):
    with pytest.raises(ValueError):
        snapshot_batch([item])


def test_revalidate_tampered_fields():
    row = Reading("feed", "a", 1, 1)
    object.__setattr__(row, "value", -1)
    with pytest.raises(ValueError):
        snapshot_batch([row])


def test_subclass_rejected():
    class Child(Reading):
        pass

    with pytest.raises(ValueError):
        snapshot_batch([Child("feed", "a", 1, 1)])


def test_no_database_touch_on_invalid_input():
    from academy_ingestion_persistence import persist_batch

    with pytest.raises(ValueError):
        persist_batch(None, [None])


def test_exact_64_accepted():
    rows = [Reading("feed", f"id-{n}", 1, n) for n in range(64)]
    assert snapshot_batch(iter(rows)) == tuple(rows)
