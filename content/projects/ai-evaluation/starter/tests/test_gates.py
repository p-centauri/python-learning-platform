import asyncio
from dataclasses import replace
from fractions import Fraction
import pytest
from academy_ai_evaluation import (
    HumanReview,
    Policy,
    load_suite,
    observe,
    decide,
    suite_digest,
    candidate_digest,
)


@pytest.fixture(scope="module")
def candidate(tmp_path_factory):
    s = load_suite()
    return s, asyncio.run(observe(s, tmp_path_factory.mktemp("gate")))


def reviews(s, rows, verdict="approve"):
    return tuple(
        HumanReview(
            c.id,
            suite_digest(s),
            candidate_digest(rows),
            "reviewer-fixture",
            "self",
            verdict,
            "Reported finite fixture review; no real semantic benchmark.",
        )
        for c in s.cases
        if c.human
    )


def test_objective_pass_does_not_invent_manual_quality(candidate):
    s, rows = candidate
    v = decide(s, rows)
    assert v.objective == "passed" and v.decision == "manual_review_pending"
    assert v.pending_reviews == ("rag-malicious-source", "rag-public") and v.recorded_reviews == 0


def test_recorded_manual_approval_and_rejection_are_separate(candidate):
    s, rows = candidate
    v = decide(s, rows, reviews=reviews(s, rows))
    assert v.decision == "controlled_fixture_ready" and v.recorded_reviews == 2
    reject = decide(s, rows, reviews=reviews(s, rows, "reject"))
    assert reject.objective == "passed" and reject.decision == "manual_review_rejected"
    assert decide(s, rows, reviews=reviews(s, rows)[:1]).decision == "manual_review_pending"


@pytest.mark.parametrize("change", ["candidate", "dataset", "duplicate", "unexpected"])
def test_stale_and_unexpected_manual_reviews(candidate, change):
    s, rows = candidate
    manual = list(reviews(s, rows))
    if change == "candidate":
        manual[0] = replace(manual[0], candidate_digest="a" * 64)
    if change == "dataset":
        manual[0] = replace(manual[0], suite_digest="b" * 64)
    if change == "duplicate":
        manual[1] = manual[0]
    if change == "unexpected":
        manual[0] = replace(manual[0], case_id="tools-normal")
    with pytest.raises(ValueError):
        decide(s, rows, reviews=tuple(manual))


@pytest.mark.parametrize(
    "field,value,check",
    [
        ("unauthorized", True, "permission"),
        ("leaked", True, "privacy"),
        ("supported", False, "case_boundaries"),
        ("reason", "invented", "case_boundaries"),
        ("effects", 2, "case_boundaries"),
    ],
)
def test_finite_regression_facts_fail_closed(candidate, field, value, check):
    s, rows = candidate
    changed = list(rows)
    changed[4] = replace(changed[4], **{field: value})
    result = decide(s, tuple(changed))
    assert (
        result.objective == "failed"
        and result.decision == "objective_failed"
        and check in result.failed_checks
    )


def test_inclusive_exact_thresholds_and_stricter_policy(candidate):
    s, rows = candidate
    assert decide(s, rows).objective == "passed"
    policy = Policy(min_precision=Fraction(1, 4) + Fraction(1, 1000))
    assert "retrieval_precision" in decide(s, rows, policy).failed_checks


@pytest.mark.parametrize("value", [True, 0.5, Fraction(-1, 2), Fraction(3, 2)])
def test_invalid_threshold_types_and_ranges(value):
    with pytest.raises(ValueError):
        Policy(min_recall=value)


def test_changed_dataset_cannot_reuse_pinned_release_policy(candidate):
    s, rows = candidate
    cases = list(s.cases)
    cases[0] = replace(cases[0], relevant=("alpha:other:1:0",))
    with pytest.raises(ValueError):
        decide(replace(s, cases=tuple(cases)), rows)
