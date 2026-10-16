from dataclasses import replace
import pytest
from academy_retrieval import Chunk, Document, Filters, Principal, Query, Spec, make_chunks, retrieve
import academy_retrieval.operations as operations
from academy_retrieval.support import cosine

SPEC = Spec(dimensions=2)
Q = Query(SPEC, "retry request", (1.0, 0.0))
P = Principal("alpha")


def row(id="public", values=(1.0, 0.0), **kwargs):
    doc = Document(
        kwargs.pop("tenant", "alpha"),
        id,
        kwargs.pop("revision", 1),
        kwargs.pop("text", "retry request"),
        **kwargs,
    )
    return Chunk(make_chunks(doc)[0], SPEC, values, doc.topic, doc.groups, doc.active)


def test_filter_before_scoring_and_top_k(monkeypatch):
    forbidden = row("private", groups=("admin",))
    foreign = row("foreign", tenant="beta")
    available = row("visible", values=(0.1, 1.0))
    observed = []

    def score(left, right):
        observed.append(left)
        return cosine(left, right)

    monkeypatch.setattr(operations, "cosine", score)
    hits = retrieve((forbidden, foreign, available), Q, P, k=1)
    assert [h.key.document for h in hits] == ["visible"]
    assert observed == [available.values]
    assert not hasattr(hits[0], "text") and not hasattr(hits[0], "values")


def test_latest_before_access_and_active_no_old_fallback():
    old = row("same", revision=1)
    private = row("same", revision=2, groups=("admin",))
    assert retrieve((old, private), Q, P) == ()
    assert [h.key.revision for h in retrieve((old, private), Q, Principal("alpha", ("admin",)))] == [2]
    assert retrieve((old, replace(private, active=False)), Q, Principal("alpha", ("admin",))) == ()


def test_revision_scope_includes_tenant_and_document():
    alpha = row("same", revision=1)
    beta = row("same", tenant="beta", revision=9)
    other = row("other", revision=7)
    assert {h.key.document for h in retrieve((alpha, beta, other), Q, P)} == {"same", "other"}


def test_metadata_filters_and_any_group():
    a = row("one", topic="python", groups=("ops", "review"))
    b = row("two", topic="http")
    assert [
        h.key.document
        for h in retrieve((a, b), Q, Principal("alpha", ("review",)), Filters(topic="python", document="one"))
    ] == ["one"]
    assert retrieve((a, b), Q, P, Filters(topic="python")) == ()
    assert retrieve((a, b), Q, P, Filters(document="missing")) == ()


def test_lexical_uses_text_and_same_access_order():
    rows = (
        row("vector-best", text="different words"),
        row("text-best", values=(0.0, 1.0)),
        row("private", groups=("admin",)),
    )
    assert retrieve(rows, Q, P, k=1)[0].key.document == "vector-best"
    assert retrieve(rows, Q, P, mode="lexical", k=1)[0].key.document == "text-best"
    assert retrieve((row(text="RETRY, request!"),), Q, P, mode="lexical")[0].score == 1


def test_full_key_ties_deterministic_and_inputs_unchanged():
    rows = (row("z"), row("a"))
    assert retrieve(rows, Q, P) == retrieve(tuple(reversed(rows)), Q, P)
    assert [h.key.document for h in retrieve(rows, Q, P)] == ["a", "z"]
    assert rows[0].span.key.document == "z"


@pytest.mark.parametrize(
    "values, expected", [((2.0, 0.0), 1.0), ((-1.0, 0.0), -1.0), ((0.0, 1.0), 0.0), ((1e6, 0.0), 1.0)]
)
def test_normalized_scores_are_not_probabilities(values, expected):
    assert retrieve((row(values=values),), Q, P)[0].score == pytest.approx(expected)


def test_threshold_inclusive_and_negative():
    negative = row(values=(-1.0, 0.0))
    assert retrieve((negative,), Q, P, Filters(min_score=-1))[0].score == -1
    assert retrieve((negative,), Q, P, Filters(min_score=0)) == ()
    assert retrieve((row(),), Q, P, Filters(min_score=1))[0].score == 1


@pytest.mark.parametrize(
    "values",
    [
        (0, 0),
        (True, 0),
        (float("nan"), 1),
        (float("inf"), 1),
        (1000001, 0),
        (10**1000, 0),
        (1e-13, 0),
        (1,),
        [1, 0],
    ],
)
def test_invalid_vectors_rejected(values):
    with pytest.raises(ValueError):
        Query(SPEC, "question", values)


@pytest.mark.parametrize(
    "spec", [Spec(model="other", dimensions=2), Spec(version="other", dimensions=2), Spec(dimensions=3)]
)
def test_model_version_dimension_mismatch_rejected(spec):
    query = Query(spec, "question", (1.0,) + (0.0,) * (spec.dimensions - 1))
    with pytest.raises(ValueError, match="mismatch"):
        retrieve((row(),), query, P)


@pytest.mark.parametrize(
    "changes",
    [
        {"topic": "unknown"},
        {"min_score": True},
        {"min_score": float("nan")},
        {"min_score": 1.1},
        {"min_score": 10**1000},
        {"document": "../path"},
    ],
)
def test_invalid_filter(changes):
    with pytest.raises(ValueError):
        Filters(**changes)


@pytest.mark.parametrize("k", [0, 11, True, 1.0])
def test_invalid_requested_k(k):
    with pytest.raises(ValueError):
        retrieve((row(),), Q, P, k=k)


def test_duplicate_key_and_corpus_cap_and_mixed_spec():
    with pytest.raises(ValueError, match="duplicate"):
        retrieve((row(), row()), Q, P)
    with pytest.raises(ValueError, match="bounded"):
        retrieve(tuple(row("d" + str(n)) for n in range(65)), Q, P)
    with pytest.raises(ValueError, match="mismatch"):
        retrieve((row(), replace(row("other"), spec=replace(SPEC, version="other"))), Q, P)


def test_empty_corpus_still_rejects_invalid_query():
    object.__setattr__(Q, "values", (0.0, 0.0))
    try:
        with pytest.raises(ValueError):
            retrieve((), Q, P)
    finally:
        object.__setattr__(Q, "values", (1.0, 0.0))
