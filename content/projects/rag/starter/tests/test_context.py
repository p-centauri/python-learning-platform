from dataclasses import FrozenInstanceError, replace
import pytest
from academy_retrieval import Filters, Principal
from academy_rag import Index, Policy, prepare, publish
from academy_rag.fixtures import PRINCIPAL, QUERY, REQUIRED, SPEC, record
from academy_rag.support import evidence_bytes


def store(tmp_path):
    index = Index(tmp_path / "index.db", SPEC)
    index.initialize()
    return index


def test_filters_before_context_and_no_old_public_fallback(tmp_path):
    index = store(tmp_path)
    for item in [record(), record(id="private", groups=("admin",)), record(id="foreign", tenant="beta")]:
        publish(index, item)
    bundle = prepare(index, PRINCIPAL, QUERY, REQUIRED)
    assert [e.span.key.document for e in bundle.evidence] == ["files"]
    serialized = evidence_bytes(bundle.evidence)
    assert b"private" not in serialized and b"foreign" not in serialized
    publish(index, record(revision=2, groups=("admin",)))
    assert prepare(index, PRINCIPAL, QUERY, REQUIRED).evidence == ()
    publish(index, record(revision=3, active=False))
    assert (
        prepare(index, Principal("alpha", ("admin",)), QUERY, REQUIRED, Filters(document="files")).evidence
        == ()
    )


def test_task_gate_is_explicit_and_not_a_general_semantic_checker(tmp_path):
    index = store(tmp_path)
    publish(index, record())
    assert prepare(index, PRINCIPAL, QUERY, ("moon",)).evidence == ()
    assert prepare(index, PRINCIPAL, QUERY, REQUIRED, Filters(document="missing")).evidence == ()
    assert prepare(index, PRINCIPAL, QUERY, REQUIRED, Filters(topic="http")).evidence == ()
    assert prepare(index, PRINCIPAL, replace(QUERY, values=(-1.0, 0.0)), REQUIRED).evidence == ()


def test_lexical_reranking_and_full_key_ties(tmp_path):
    index = store(tmp_path)
    publish(
        index, record(id="a", text="The file failure needs a report and another report.", values=(1.0, 0.0))
    )
    publish(index, record(id="b", text="Release a file after a failure.", values=(0.8, 0.6)))
    bundle = prepare(index, PRINCIPAL, QUERY, REQUIRED)
    assert bundle.evidence[0].span.key.document == "b"
    publish(index, record(id="c", text="Release a file after a failure.", values=(0.8, 0.6)))
    assert [e.span.key.document for e in prepare(index, PRINCIPAL, QUERY, REQUIRED).evidence][:2] == [
        "b",
        "c",
    ]


def test_exact_utf8_budget_never_slices_evidence(tmp_path):
    index = store(tmp_path)
    publish(index, record(text="Release the file after a failure. é🙂"))
    initial = prepare(index, PRINCIPAL, QUERY, REQUIRED)
    size = len(evidence_bytes(initial.evidence))
    fits = prepare(index, PRINCIPAL, QUERY, REQUIRED, policy=Policy(context_bytes=size))
    assert fits.evidence == initial.evidence
    too_small = prepare(index, PRINCIPAL, QUERY, REQUIRED, policy=Policy(context_bytes=size - 1))
    assert too_small.evidence == () and too_small.omitted == 1
    assert size > len(evidence_bytes(initial.evidence).decode())


def test_selected_count_bounded_and_values_frozen(tmp_path):
    index = store(tmp_path)
    for n in range(4):
        publish(index, record(id="d" + str(n)))
    bundle = prepare(index, PRINCIPAL, QUERY, REQUIRED, policy=Policy(passages=2))
    assert len(bundle.evidence) == 2 and bundle.omitted == 2
    assert [e.id for e in bundle.evidence] == ["e0", "e1"]
    with pytest.raises(FrozenInstanceError):
        bundle.epoch = 999


@pytest.mark.parametrize(
    "required", [(), ("file", "file"), ("File",), ("x",), ("file failure",), ["file"], (True,)]
)
def test_invalid_application_term_gate(required, tmp_path):
    with pytest.raises(ValueError):
        prepare(store(tmp_path), PRINCIPAL, QUERY, required)


@pytest.mark.parametrize(
    "changes",
    [
        {"candidates": 0},
        {"passages": 4},
        {"context_bytes": 15},
        {"context_bytes": 4097},
        {"candidates": True},
        {"candidates": 1, "passages": 2},
    ],
)
def test_invalid_policy(changes):
    with pytest.raises(ValueError):
        Policy(**changes)


def test_query_vector_spec_must_match_index_even_when_empty(tmp_path):
    with pytest.raises(ValueError, match="mismatch"):
        prepare(store(tmp_path), PRINCIPAL, replace(QUERY, spec=replace(SPEC, model="different")), REQUIRED)
