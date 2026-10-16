from collections import Counter
from fractions import Fraction
from pathlib import Path
from .contracts import HumanReview, Metrics, Observation, Policy, Suite, Variant, Verdict
from .dataset import candidate_digest, suite_digest
from .harness import one


async def observe(
    suite: Suite, directory: Path, variant: Variant = "task-gated-v1"
) -> tuple[Observation, ...]:
    if type(suite) is not Suite or variant not in ("raw-cosine-v1", "task-gated-v1"):
        raise ValueError("exact suite/candidate required")
    if not directory.is_dir() or any(directory.iterdir()):
        raise ValueError("empty owned workspace required")
    rows = []
    for case in suite.cases:
        area = directory / case.id
        area.mkdir()
        rows.append(await one(case, area, variant))
    return tuple(rows)


def measure(suite: Suite, observations: tuple[Observation, ...]) -> Metrics:
    if (
        type(suite) is not Suite
        or type(observations) is not tuple
        or any(type(o) is not Observation for o in observations)
    ):
        raise ValueError("exact observations required")
    if Counter(o.case_id for o in observations) != Counter(c.id for c in suite.cases):
        raise ValueError("complete unique case coverage required")
    if len({o.variant for o in observations}) != 1:
        raise ValueError("mixed candidate observations")
    by_id = {o.case_id: o for o in observations}
    precision = Fraction()
    recall = Fraction()
    mrr = Fraction()
    retrieval = positive = unlabelled = unwanted = answers = answer_ok = tools = tool_ok = boundary = 0
    for case in suite.cases:
        o = by_id[case.id]
        if len(o.selected) > o.k:
            raise ValueError("selection exceeds requested k")
        valid = (
            o.reason == case.reason
            and o.effects == case.effects
            and o.answered == case.answered
            and o.supported
        )
        boundary += int(not valid)
        if case.layer == "retrieval":
            retrieval += 1
            relevant = set(case.relevant)
            hits = sum(k in relevant for k in o.selected)
            precision += Fraction(hits, o.k)
            if relevant:
                positive += 1
                recall += Fraction(hits, len(relevant))
                mrr += next(
                    (Fraction(1, n) for n, k in enumerate(o.selected, 1) if k in relevant), Fraction()
                )
            else:
                unlabelled += 1
                unwanted += len(o.selected)
        elif case.layer == "rag":
            answers += 1
            answer_ok += int(valid)
        else:
            tools += 1
            tool_ok += int(valid)
    return Metrics(
        retrieval,
        positive,
        unlabelled,
        precision / retrieval,
        recall / positive,
        mrr / positive,
        unwanted,
        answers,
        Fraction(answer_ok, answers),
        tools,
        Fraction(tool_ok, tools),
        sum(o.unauthorized for o in observations),
        sum(o.leaked for o in observations),
        boundary,
    )


def decide(
    suite: Suite,
    observations: tuple[Observation, ...],
    policy: Policy = Policy(),
    reviews: tuple[HumanReview, ...] = (),
) -> Verdict:
    if (
        type(policy) is not Policy
        or type(reviews) is not tuple
        or any(type(r) is not HumanReview for r in reviews)
    ):
        raise ValueError("exact policy/manual reviews required")
    metrics = measure(suite, observations)
    sd = suite_digest(suite)
    cd = candidate_digest(observations)
    if policy.dataset_digest != sd:
        raise ValueError("dataset differs from pinned release policy")
    needed = {c.id for c in suite.cases if c.human}
    if len({r.case_id for r in reviews}) != len(reviews):
        raise ValueError("duplicate manual reviews")
    if any(r.case_id not in needed or r.suite_digest != sd or r.candidate_digest != cd for r in reviews):
        raise ValueError("stale or unexpected manual review")
    failed = []
    for name, value, minimum in [
        ("retrieval_precision", metrics.precision, policy.min_precision),
        ("positive_recall", metrics.recall, policy.min_recall),
        ("positive_mrr", metrics.mrr, policy.min_mrr),
        ("answer_contract", metrics.answer_contract, policy.min_answer_contract),
        ("tool_contract", metrics.tool_contract, policy.min_tool_contract),
    ]:
        if value < minimum:
            failed.append(name)
    if metrics.unwanted_hits > policy.max_unwanted_hits:
        failed.append("unlabelled_hits")
    if metrics.permission_failures:
        failed.append("permission")
    if metrics.privacy_failures:
        failed.append("privacy")
    if metrics.boundary_failures:
        failed.append("case_boundaries")
    pending = tuple(sorted(needed - {r.case_id for r in reviews}))
    decision = (
        "objective_failed"
        if failed
        else "manual_review_rejected"
        if any(r.verdict == "reject" for r in reviews)
        else "manual_review_pending"
        if pending
        else "controlled_fixture_ready"
    )
    return Verdict(
        "failed" if failed else "passed",
        decision,
        tuple(failed),
        pending,
        len(reviews),
        sd,
        cd,
        policy.version,
    )
