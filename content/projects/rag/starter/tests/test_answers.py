import asyncio
from dataclasses import replace
import pytest
from academy_model_contracts import Limits
from academy_retrieval import Principal
from academy_rag import Citation, Index, Policy, Record, answer, prepare, publish, resolve
from academy_rag.fixtures import CONFIG, PRINCIPAL, QUERY, REQUIRED, SPEC, Scripted, record
from academy_rag.support import parse


def setup(tmp_path):
    index = Index(tmp_path / "index.db", SPEC)
    index.initialize()
    publish(index, record())
    return index, prepare(index, PRINCIPAL, QUERY, REQUIRED)


def run(index, bundle, fake=None, config=CONFIG, limits=Limits(max_steps=1)):
    fake = fake or Scripted()
    return asyncio.run(answer(index, bundle, lambda: PRINCIPAL, fake.adapter(config), config, limits))


def test_real_excerpt_citation_and_configured_request(tmp_path):
    index, bundle = setup(tmp_path)
    fake = Scripted()
    result = run(index, bundle, fake)
    assert result.reason == "answered" and result.attempts == 1 and result.charged == 26
    assert result.text == bundle.evidence[0].span.text
    assert result.citations == (Citation("e0", bundle.evidence[0].span),)
    assert resolve(Index(index.path, SPEC), result.citations[0], PRINCIPAL) == result.text
    body = parse(fake.requests[0], 16384)
    assert body["schema"] == "rag-quotes-v1" and body["prompt_version"] == "rag-v1"
    assert body["untrusted_evidence"][0]["source"]["tenant"] == "alpha"
    assert result.usage.input_units == 3


@pytest.mark.parametrize(
    "mode",
    [
        "wrong-quote",
        "wrong-id",
        "duplicate",
        "extra",
        "empty",
        "wrong-model",
        "wrong-schema",
        "wrong-usage",
        "duplicate-json",
        "nonfinite",
        "not-bytes",
    ],
)
def test_invalid_generation_never_returns_raw_text_or_citations(tmp_path, mode):
    index, bundle = setup(tmp_path)
    result = run(index, bundle, Scripted(mode))
    assert result.reason == "invalid_output" and result.text is None and result.citations == ()
    assert result.attempts == 1 and "private-fixture-marker" not in repr(result)
    assert (
        result.charged == 26
        if mode in ("wrong-quote", "wrong-id", "duplicate", "extra", "empty")
        else result.charged > 26
    )


@pytest.mark.parametrize("mode", ["refused", "incomplete", "error"])
def test_distinct_nonanswer_provider_outcomes(tmp_path, mode):
    index, bundle = setup(tmp_path)
    result = run(index, bundle, Scripted(mode))
    assert result.reason == ("provider_error" if mode == "error" else mode)
    assert result.text is None and result.citations == () and result.attempts == 1
    assert result.charged > 26 if mode == "error" else result.charged == 26


@pytest.mark.parametrize("kind", ["gate", "empty-budget", "deleted"])
def test_missing_evidence_never_calls_provider(tmp_path, kind):
    index, bundle = setup(tmp_path)
    if kind == "gate":
        bundle = prepare(index, PRINCIPAL, QUERY, ("moon",))
    elif kind == "empty-budget":
        bundle = prepare(index, PRINCIPAL, QUERY, REQUIRED, policy=Policy(context_bytes=16))
    else:
        publish(index, Record("alpha", "files", 2, None))
        bundle = prepare(index, PRINCIPAL, QUERY, REQUIRED)
    fake = Scripted()
    result = run(index, bundle, fake)
    assert result.reason == "missing_evidence" and result.attempts == result.charged == 0
    assert fake.requests == [] and result.text is None


def test_forged_or_stale_bundle_never_calls_provider(tmp_path):
    index, bundle = setup(tmp_path)
    fake = Scripted()
    forged = replace(
        bundle,
        evidence=(
            replace(
                bundle.evidence[0],
                span=replace(
                    bundle.evidence[0].span, key=replace(bundle.evidence[0].span.key, tenant="beta")
                ),
            ),
        ),
    )
    assert run(index, forged, fake).reason == "stale_evidence"
    publish(index, record(revision=2))
    assert run(index, bundle, fake).reason == "stale_evidence" and fake.requests == []


@pytest.mark.parametrize("change", ["update", "delete", "acl"])
def test_second_owner_update_during_generation_discards_answer(tmp_path, change):
    index, bundle = setup(tmp_path)
    other = Index(index.path, SPEC)

    def mutate():
        item = (
            Record("alpha", "files", 2, None)
            if change == "delete"
            else record(
                revision=2,
                groups=("admin",) if change == "acl" else (),
                text="Updated file failure procedure.",
            )
        )
        publish(other, item)

    fake = Scripted(change=mutate)
    result = run(index, bundle, fake)
    assert result.reason == "stale_evidence" and result.attempts == 1 and result.charged == 26
    assert result.text is None and result.citations == ()
    assert other.snapshot()[0] == 2


def test_permission_source_is_refreshed_before_and_after_provider(tmp_path):
    index, bundle = setup(tmp_path)
    state = [PRINCIPAL]
    observed = []

    def authority():
        observed.append(state[0])
        return state[0]

    fake = Scripted(change=lambda: state.__setitem__(0, Principal("beta")))
    result = asyncio.run(answer(index, bundle, authority, fake.adapter(), CONFIG))
    assert result.reason == "principal_changed" and result.text is None and result.attempts == 1
    assert observed == [PRINCIPAL, Principal("beta")]
    other = asyncio.run(answer(index, bundle, lambda: Principal("beta"), fake.adapter(), CONFIG))
    assert other.reason == "principal_changed" and other.attempts == 0 and len(fake.requests) == 1


def test_old_citations_cannot_be_resolved_after_revocation_or_deletion(tmp_path):
    index, bundle = setup(tmp_path)
    citation = run(index, bundle).citations[0]
    assert resolve(index, citation, Principal("beta")) is None
    publish(index, record(revision=2, groups=("admin",)))
    assert resolve(index, citation, PRINCIPAL) is None
    restricted = prepare(index, Principal("alpha", ("admin",)), QUERY, REQUIRED)
    latest = asyncio.run(
        answer(index, restricted, lambda: Principal("alpha", ("admin",)), Scripted().adapter(), CONFIG)
    ).citations[0]
    assert resolve(index, latest, PRINCIPAL) is None
    publish(index, Record("alpha", "files", 3, None))
    assert resolve(index, latest, Principal("alpha", ("admin",))) is None


def test_context_and_cost_preflight_and_exact_cost_edge(tmp_path):
    index, bundle = setup(tmp_path)
    fake = Scripted()
    assert run(index, bundle, fake, config=replace(CONFIG, context_units=1)).reason == "context_limit"
    assert run(index, bundle, fake, limits=Limits(max_cost=0)).reason == "cost_limit" and fake.requests == []
    blocked = run(index, bundle, fake, limits=Limits(max_cost=1))
    assert blocked.reason == "cost_limit"
    result = run(index, bundle, fake)
    raw = fake.requests[0]
    reserve = len(raw) * CONFIG.input_rate + CONFIG.output_units * CONFIG.output_rate
    assert run(index, bundle, limits=Limits(max_cost=reserve)).reason == "answered"
    assert run(index, bundle, limits=Limits(max_cost=reserve - 1)).reason == "cost_limit"
    assert result.charged == 26


def test_cooperative_timeout_cleanup_and_external_cancellation(tmp_path):
    index, bundle = setup(tmp_path)

    async def exercise():
        timeout = Scripted("wait")
        result = await answer(
            index, bundle, lambda: PRINCIPAL, timeout.adapter(), CONFIG, Limits(timeout_ms=10)
        )
        assert result.reason == "timeout" and result.text is None and timeout.cleaned and result.charged > 26
        cancelled = Scripted("wait")
        task = asyncio.create_task(answer(index, bundle, lambda: PRINCIPAL, cancelled.adapter(), CONFIG))
        await asyncio.wait_for(cancelled.entered.wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert cancelled.cleaned and len(cancelled.requests) == 1

    asyncio.run(exercise())


def test_no_permission_data_or_foreign_text_enters_provider_request(tmp_path):
    index, bundle = setup(tmp_path)
    for item in [
        record(id="private", text="private-fixture-marker file failure", groups=("admin",)),
        record(id="foreign", tenant="beta", text="foreign-fixture-marker file failure"),
    ]:
        publish(index, item)
    bundle = prepare(index, PRINCIPAL, QUERY, REQUIRED)
    fake = Scripted()
    assert run(index, bundle, fake).reason == "answered"
    assert (
        b"private-fixture-marker" not in fake.requests[0]
        and b"foreign-fixture-marker" not in fake.requests[0]
    )
    assert b"groups" not in fake.requests[0]
