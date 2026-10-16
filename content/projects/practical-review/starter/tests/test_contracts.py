import json
from dataclasses import asdict
import pytest
from academy_ingestion_service import Cursor, Datum, Page
from academy_ingestion_service.contracts import ConflictingDatum
from academy_practical_review import Item, analyse, decode_page, prepare
from academy_practical_review.evidence import compare, review_case
from academy_practical_review.support import fingerprint


def page(rows=(), cursor=None):
    return dict(items=[asdict(r) for r in rows], next_cursor=cursor)


@pytest.mark.parametrize("value", [0, 60000, 1000000])
def test_decode_preserves_service_domain_and_copies(value):
    payload = page([Datum("a", 1, value)], dict(id="a", revision=1))
    result = decode_page(payload)
    assert result == Page((Datum("a", 1, value),), Cursor("a", 1))
    payload["items"][0]["value"] = 7
    assert result.items[0].value == value


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        dict(items=[], next_cursor=None, private="secret"),
        dict(items=(), next_cursor=None),
        dict(items=[dict(id="a", revision=True, value=0)], next_cursor=None),
        dict(items=[dict(id="a", revision=1, value=0, namespace="other")], next_cursor=None),
        page([Datum("a", 1, 0), Datum("a", 1, 0)]),
        page([Datum("b", 1, 0), Datum("a", 1, 0)]),
        page([], dict(id="a", revision=1)),
        page([Datum("a", 1, 0)], dict(id="b", revision=1)),
        page([Datum("a", 1, 0)], dict(id="a", revision=1, extra=1)),
        page([Datum("item-" + str(i).zfill(2), 1, 0) for i in range(33)]),
    ],
)
def test_decode_rejects_shape_cursor_order_and_bounds(payload):
    with pytest.raises(ValueError):
        decode_page(payload)


def test_prepare_latest_full_key_conflict_zero_and_detached_inputs():
    rows = [Datum("b", 1, 4), Datum("a", 8, 0), Datum("a", 1, 7), Datum("a", 8, 0)]
    result = prepare("north", rows)
    assert result == (Item("north", Datum("a", 8, 0)), Item("north", Datum("b", 1, 4)))
    rows.clear()
    assert result[0].datum.value == 0
    with pytest.raises(ConflictingDatum):
        prepare("north", [Datum("a", 8, 0), Datum("a", 1, 7), Datum("a", 1, 9)])
    assert prepare("north", []) == ()


def test_prepare_does_not_widen_earlier_library_domain_or_close_borrowed_iterator():
    with pytest.raises(ValueError):
        prepare("north", [Datum("a", 1, 60001), Datum("a", 8, 0)])
    closed = []

    def values():
        try:
            for _ in range(300):
                yield Datum("a", 1, 0)
        finally:
            closed.append(True)

    iterator = values()
    with pytest.raises(ValueError):
        prepare("north", iterator)
    assert closed == []
    assert next(iterator) == Datum("a", 1, 0)
    iterator.close()
    assert closed == [True]
    with pytest.raises(ValueError):
        prepare("north", [Datum("item-" + str(i), 1, 0) for i in range(65)])


@pytest.mark.parametrize("rows", [[object()], [dict(id="a", revision=1, value=0)]])
def test_prepare_requires_real_immutable_service_datums(rows):
    with pytest.raises(ValueError):
        prepare("north", rows)


@pytest.mark.parametrize("requests,computations,hits", [((0, 0, 1, 0), 2, 2), ((), 0, 0), ((0, 1), 2, 0)])
def test_equivalent_ordered_fingerprints_and_actual_cache_counts(requests, computations, hits):
    items = prepare("north", [Datum("a", 1, 0), Datum("b", 1, 5)])
    before = analyse(items, requests)
    after = analyse(items, requests, cached=True)
    assert before.snapshot == after.snapshot and before.fingerprints == after.fingerprints
    assert before.computations == len(requests) and after.computations == computations and after.hits == hits
    assert before.fingerprints == tuple(fingerprint(items[i]) for i in requests)
    assert sum(row.value for row in after.snapshot) == 5
    assert analyse(items, requests, cached=True).computations == computations  # Cache is fresh each call.


def test_cache_eviction_revision_namespace_and_changed_new_call():
    items = tuple(Item("north", Datum("item-" + str(i), 1, i)) for i in range(9))
    result = analyse(items, tuple(range(9)) + (0,), cached=True)
    assert result.computations == 10 and result.hits == 0 and result.cache_size == 8
    other = (Item("north", Datum("a", 1, 0)), Item("south", Datum("a", 1, 5)))
    assert analyse(other, (0, 1, 0), cached=True).computations == 2
    one = analyse((Item("north", Datum("a", 1, 0)),), (0,), cached=True)
    changed = analyse((Item("north", Datum("a", 2, 0)),), (0,), cached=True)
    assert one.fingerprints != changed.fingerprints


@pytest.mark.parametrize(
    "items,requests,mode",
    [
        ((), (0,), False),
        ((), (), 1),
        ([], (), False),
        ((Item("north", Datum("a", 1, 0)),), [0], False),
        ((Item("north", Datum("a", 1, 0)),), (True,), False),
        ((Item("north", Datum("a", 1, 0)),), (-1,), False),
        ((Item("north", Datum("a", 1, 0)),), (0,) * 257, False),
        ((Item("north", Datum("a", 1, 0)), Item("north", Datum("a", 2, 0))), (), False),
    ],
)
def test_reporting_shape_positions_and_distinct_snapshot_keys(items, requests, mode):
    with pytest.raises(ValueError):
        analyse(items, requests, cached=mode)


def case():
    return dict(
        case_id="independent-example",
        namespace="north",
        purpose="Assessor example, not learner originality.",
        rows=[
            dict(id="b", revision=1, value=5),
            dict(id="a", revision=3, value=0),
            dict(id="a", revision=1, value=9),
        ],
        requests=[0, 1, 0],
        expected_latest=[dict(id="a", revision=3, value=0), dict(id="b", revision=1, value=5)],
        expected_computations=dict(baseline=3, cached=2),
    )


def test_bounded_reviewer_data_checks_claims_without_claiming_originality(tmp_path):
    path = tmp_path / "case.json"
    path.write_text(json.dumps(case()))
    report = review_case(path)
    assert report["equivalent"] and report["originality"] == "requires manual review"
    bad = case()
    bad["expected_computations"]["cached"] = 1
    path.write_text(json.dumps(bad))
    with pytest.raises(ValueError):
        review_case(path)
    path.write_text(" " * 8193)
    with pytest.raises(ValueError):
        review_case(path)


def test_review_case_does_not_accept_boolean_expectations_or_duplicate_keys(tmp_path):
    path = tmp_path / "case.json"
    bad = case()
    bad["expected_computations"]["cached"] = True
    path.write_text(json.dumps(bad))
    with pytest.raises(ValueError):
        review_case(path)
    path.write_text(json.dumps(case())[:-1] + ',"case_id":"other"}')
    with pytest.raises(ValueError):
        review_case(path)


def test_actual_profile_counts_equivalence_and_borrowed_tracer_protection():
    import tracemalloc

    items = prepare("north", [Datum("a", 1, 0), Datum("b", 1, 5)])
    report = compare(items, (0, 1, 0))
    assert (
        report["equivalent"] and report["baseline_computations"] == 3 and report["cached_computations"] == 2
    )
    assert report["profiles"]["baseline"]["fingerprint_calls"] == 3
    assert report["profiles"]["cached"]["fingerprint_calls"] == 2
    assert all(len(samples) == 3 for samples in report["timings_ns"].values())
    assert not tracemalloc.is_tracing()
    tracemalloc.start()
    try:
        with pytest.raises(RuntimeError):
            compare(items, (0,))
        assert tracemalloc.is_tracing()
    finally:
        tracemalloc.stop()
