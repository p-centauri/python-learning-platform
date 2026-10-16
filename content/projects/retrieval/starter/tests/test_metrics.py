from dataclasses import replace
import pytest
from academy_retrieval import (
    Case,
    Chunk,
    Document,
    Filters,
    Key,
    Principal,
    Query,
    Spec,
    evaluate,
    make_chunks,
)


def setup():
    spec = Spec(dimensions=2)
    rows = tuple(
        Chunk(make_chunks(Document("alpha", name, 1, name))[0], spec, values)
        for name, values in [("a", (1.0, 0.0)), ("b", (0.8, 0.6)), ("c", (0.0, 1.0))]
    )
    case = Case(
        "q",
        Query(spec, "question", (1.0, 0.0)),
        Principal("alpha"),
        Filters(),
        (rows[1].span.key, rows[2].span.key),
    )
    return rows, case


def test_literal_denominators_and_first_relevant_rank():
    rows, case = setup()
    report = evaluate(rows, (case,), k=2)
    result = report.results[0]
    assert result.matched == 1 and result.relevant == 2
    assert result.precision_k == 0.5 and result.recall == 0.5 and result.reciprocal_rank == 0.5
    assert report.precision_all == report.recall_answerable == report.mrr_answerable == 0.5


def test_requested_k_denominator_with_fewer_results():
    rows, case = setup()
    case = replace(case, filters=Filters(document="b"), relevant=(rows[1].span.key,))
    result = evaluate(rows, (case,), k=3).results[0]
    assert len(result.hits) == 1 and result.precision_k == pytest.approx(1 / 3)
    assert result.recall == 1 and result.reciprocal_rank == 1


def test_threshold_miss_is_zero_recall_not_invalid_judgment():
    rows, case = setup()
    case = replace(case, filters=Filters(min_score=1))
    result = evaluate(rows, (case,), k=1).results[0]
    assert result.matched == 0 and result.recall == 0 and result.reciprocal_rank == 0


def test_no_label_cases_report_unwanted_hits_and_separate_denominators():
    rows, case = setup()
    empty = replace(case, id="empty", relevant=())
    missing = replace(empty, id="missing", filters=Filters(document="missing"))
    report = evaluate(rows, (case, empty, missing), k=2)
    assert report.cases == 3 and report.answerable == 1 and report.no_labels == 2
    assert report.precision_all == pytest.approx(1 / 6)
    assert report.recall_answerable == 0.5 and report.mrr_answerable == 0.5
    assert report.unwanted_returns == 2
    assert all(r.recall is None and r.reciprocal_rank is None for r in report.results[1:])


def test_no_cases_or_no_positive_labels_never_claim_perfect_recall():
    rows, case = setup()
    report = evaluate(rows, ())
    assert report.precision_all is report.recall_answerable is report.mrr_answerable is None
    no_labels = evaluate(rows, (replace(case, relevant=()),))
    assert no_labels.precision_all == 0 and no_labels.recall_answerable is no_labels.mrr_answerable is None


@pytest.mark.parametrize(
    "key", [Key("alpha", "missing", 1, 0), Key("beta", "a", 1, 0), Key("alpha", "a", 2, 0)]
)
def test_missing_foreign_and_obsolete_labels_rejected(key):
    rows, case = setup()
    with pytest.raises(ValueError, match="ineligible"):
        evaluate(rows, (replace(case, relevant=(key,)),))


def test_acl_and_latest_labels_cannot_be_used_as_relevance():
    rows, case = setup()
    newer = replace(
        rows[1], span=replace(rows[1].span, key=replace(rows[1].span.key, revision=2)), groups=("admin",)
    )
    for key in (rows[1].span.key, newer.span.key):
        with pytest.raises(ValueError, match="ineligible"):
            evaluate(rows + (newer,), (replace(case, relevant=(key,)),))


def test_duplicate_case_and_relevance_rejected():
    rows, case = setup()
    with pytest.raises(ValueError, match="duplicate case"):
        evaluate(rows, (case, case))
    with pytest.raises(ValueError, match="relevance"):
        replace(case, relevant=(rows[0].span.key, rows[0].span.key))


@pytest.mark.parametrize("mode", ["hybrid", "bm25", "approximate"])
def test_unsupported_mode_rejected(mode):
    rows, case = setup()
    with pytest.raises(ValueError):
        evaluate(rows, (case,), mode=mode)
