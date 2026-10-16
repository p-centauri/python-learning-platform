import asyncio
from dataclasses import replace
from fractions import Fraction
import pytest
from academy_ai_evaluation import load_suite, observe, measure, candidate_digest


@pytest.fixture(scope="module")
def observations(tmp_path_factory):
    return asyncio.run(observe(load_suite(), tmp_path_factory.mktemp("metrics")))


def test_exact_denominators_no_label_counts_and_reordering(observations):
    s = load_suite()
    m = measure(s, observations)
    assert (m.retrieval_cases, m.positive_cases, m.unlabelled_cases) == (4, 2, 2)
    assert (m.precision, m.recall, m.mrr) == (Fraction(1, 4), Fraction(1, 2), Fraction(1, 2))
    assert m.unwanted_hits == 0 and m.answer_contract == m.tool_contract == 1
    assert (
        m.answer_cases == m.tool_cases == 7
        and m.permission_failures == m.privacy_failures == m.boundary_failures == 0
    )
    reverse = tuple(reversed(observations))
    assert measure(s, reverse) == m
    assert candidate_digest(reverse) == candidate_digest(observations)


def test_actual_raw_baseline_has_unlabelled_unwanted_hit(tmp_path):
    s = load_suite()
    raw = asyncio.run(observe(s, tmp_path, "raw-cosine-v1"))
    m = measure(s, raw)
    assert m.unwanted_hits == 1 and m.precision == Fraction(1, 4)
    assert (m.recall, m.mrr) == (Fraction(1, 2), Fraction(1, 2))


@pytest.mark.parametrize("change", ["missing", "duplicate", "unknown-id", "mixed", "k"])
def test_coverage_and_candidate_alignment(observations, change):
    rows = list(observations)
    if change == "missing":
        rows.pop()
    if change == "duplicate":
        rows[-1] = rows[0]
    if change == "unknown-id":
        rows[0] = replace(rows[0], case_id="unknown")
    if change == "mixed":
        rows[0] = replace(rows[0], variant="raw-cosine-v1")
    if change == "k":
        rows[0] = replace(rows[0], selected=("alpha:files:1:0", "alpha:other:1:0"))
    with pytest.raises(ValueError):
        measure(load_suite(), tuple(rows))


def test_requested_k_not_returned_count(observations):
    rows = list(observations)
    rows[0] = replace(rows[0], k=3)
    assert measure(load_suite(), tuple(rows)).precision == Fraction(1, 12)


@pytest.mark.parametrize(
    "field,value",
    [
        ("requests", True),
        ("effects", -1),
        ("answered", 1),
        ("source_digests", ("bad",)),
        ("selected", ("private text",)),
        ("variant", "unknown"),
    ],
)
def test_strict_observation_values(observations, field, value):
    with pytest.raises(ValueError):
        replace(observations[0], **{field: value})
