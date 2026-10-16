import asyncio
from dataclasses import replace
import json
import pytest
from academy_model_contracts import Limits, ModelConfig
from academy_rag import publish
from academy_rag.fixtures import record
from academy_tools import Call, LocalTools, execute, run
from academy_tools.fixtures import ScriptedTransport, setup


def test_real_read_write_finish_and_request_observations(tmp_path):
    index, store, ctx, a = setup(tmp_path)
    transport = ScriptedTransport()
    report = asyncio.run(run(ctx, index, store, lambda: a, transport.provider()))
    assert report.stopped == "finished" and report.attempts == 3 and report.charged == 78
    assert [s.outcome.reason for s in report.steps if s.outcome] == ["read", "written"]
    assert store.counts(ctx) == (1, 1)
    final = json.loads(transport.requests[2])["input"]["observed_tool_results"]
    assert final[0]["text"] == ctx.citations[0].span.text and final[1]["note_id"] == 1
    assert all(s.outcome.text is None for s in report.steps if s.outcome)
    assert (report.provider_id, report.model, report.prompt_version) == (
        "fixture-a",
        "fixture-model-2026-10",
        "tools-v1",
    )


@pytest.mark.parametrize(
    "mode,reason",
    [
        ("unknown", "invalid_proposal"),
        ("extra", "invalid_proposal"),
        ("bad-usage", "invalid_proposal"),
        ("refused", "refused"),
        ("incomplete", "incomplete"),
        ("error", "provider_error"),
        ("changed", "approval_required"),
    ],
)
def test_invalid_forbidden_and_noncomplete_no_effect(tmp_path, mode, reason):
    index, store, ctx, a = setup(tmp_path)
    t = ScriptedTransport((mode,))
    r = asyncio.run(run(ctx, index, store, lambda: a, t.provider()))
    assert r.stopped == reason and r.attempts == 1 and store.counts(ctx) == (0, 0)
    assert r.charged == 26 if mode in ("refused", "incomplete", "changed") else r.charged > 26


@pytest.mark.parametrize(
    "limit,reason",
    [(Limits(max_cost=0), "cost_limit"), (Limits(), "context_limit"), (Limits(max_steps=1), "step_limit")],
)
def test_cost_full_context_and_step_admission(tmp_path, limit, reason):
    index, store, ctx, a = setup(tmp_path)
    t = ScriptedTransport(("read",))
    config = (
        ModelConfig(prompt_version="tools-v1", context_units=16)
        if reason == "context_limit"
        else ModelConfig(prompt_version="tools-v1")
    )
    r = asyncio.run(run(ctx, index, store, lambda: a, t.provider(), config=config, limits=limit))
    assert r.stopped == reason and r.attempts == (1 if reason == "step_limit" else 0)
    assert len(t.requests) == r.attempts and store.counts(ctx) == (0, 0)


def test_refreshed_authority_during_provider_blocks_tool(tmp_path):
    index, store, ctx, a = setup(tmp_path)
    state = [a]

    def revoke():
        state[0] = replace(a, read=False)

    t = ScriptedTransport(("write",), revoke)
    r = asyncio.run(run(ctx, index, store, lambda: state[0], t.provider()))
    assert r.stopped == "forbidden" and store.counts(ctx) == (0, 0)


def test_changed_source_during_provider_blocks_tool(tmp_path):
    index, store, ctx, a = setup(tmp_path)

    def change():
        publish(index, record(revision=2))

    t = ScriptedTransport(("write",), change)
    r = asyncio.run(run(ctx, index, store, lambda: a, t.provider()))
    assert r.stopped == "stale_source" and store.counts(ctx) == (0, 0)


def test_reauthorize_after_tool_wait_before_effect(tmp_path):
    index, store, ctx, a = setup(tmp_path)
    state = [a]

    async def before():
        state[0] = replace(a, approval=None)

    tools = LocalTools(index, store, lambda: state[0], before=before)
    t = ScriptedTransport(("write",))
    r = asyncio.run(run(ctx, index, store, lambda: state[0], t.provider(), tools))
    assert r.stopped == "approval_required" and store.counts(ctx) == (0, 0)


def test_repeat_ids_and_new_ids_do_not_multiply_effect(tmp_path):
    index, store, ctx, a = setup(tmp_path)
    t = ScriptedTransport(("write", "new-id", "finish"))
    r = asyncio.run(run(ctx, index, store, lambda: a, t.provider()))
    assert r.stopped == "finished" and [s.outcome.reason for s in r.steps if s.outcome] == [
        "written",
        "replayed",
    ]
    assert store.counts(ctx) == (1, 1)


@pytest.mark.parametrize("phase", ["provider", "before-tool", "after-tool"])
def test_shared_deadline_actual_cleanup_and_unknown_committed_effect(tmp_path, phase):
    index, store, ctx, a = setup(tmp_path)
    clean = []

    async def wait():
        try:
            await asyncio.Event().wait()
        finally:
            await asyncio.sleep(0)
            clean.append(True)

    tools = LocalTools(
        index,
        store,
        lambda: a,
        before=wait if phase == "before-tool" else None,
        after=wait if phase == "after-tool" else None,
    )
    t = ScriptedTransport(("wait" if phase == "provider" else "write",))
    r = asyncio.run(run(ctx, index, store, lambda: a, t.provider(), tools, limits=Limits(timeout_ms=30)))
    assert r.stopped == ("provider_timeout" if phase == "provider" else "tool_timeout")
    assert t.cleaned if phase == "provider" else clean == [True]
    assert store.counts(ctx) == ((1, 1) if phase == "after-tool" else (0, 0))
    if phase == "after-tool":
        assert r.steps[-1].outcome is None
        retry = execute(ctx, Call("retry", "save_note", "e0", "Review file cleanup"), index, store, lambda: a)
        assert retry.reason == "replayed" and store.counts(ctx) == (1, 1)


def test_external_cancellation_propagates_after_committed_note(tmp_path):
    index, store, ctx, a = setup(tmp_path)
    entered = asyncio.Event()
    clean = []

    async def after():
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            await asyncio.sleep(0)
            clean.append(True)

    t = ScriptedTransport(("write",))
    tools = LocalTools(index, store, lambda: a, after=after)

    async def scenario():
        task = asyncio.create_task(run(ctx, index, store, lambda: a, t.provider(), tools))
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    assert clean == [True] and store.counts(ctx) == (1, 1)
    assert (
        execute(ctx, Call("retry", "save_note", "e0", "Review file cleanup"), index, store, lambda: a).reason
        == "replayed"
    )


def test_one_deadline_covers_multiple_provider_and_tool_steps(tmp_path):
    index, store, ctx, a = setup(tmp_path)

    async def pause():
        await asyncio.sleep(0.025)

    t = ScriptedTransport(("read",))
    tools = LocalTools(index, store, lambda: a, before=pause)
    r = asyncio.run(run(ctx, index, store, lambda: a, t.provider(), tools, limits=Limits(timeout_ms=40)))
    assert r.stopped == "tool_timeout" and r.attempts == 2 and len(r.steps) == 2


def test_provider_identity_mismatch_no_call(tmp_path):
    index, store, ctx, a = setup(tmp_path)
    t = ScriptedTransport()
    with pytest.raises(ValueError):
        asyncio.run(run(ctx, index, store, lambda: a, t.provider(), config=ModelConfig(provider_id="other")))
    assert not t.requests and store.counts(ctx) == (0, 0)


@pytest.mark.parametrize("change", ["read-revoke", "source-change", "write-revoke"])
def test_post_tool_changes_reject_visible_result_without_undoing_committed_effect(tmp_path, change):
    index, store, ctx, a = setup(tmp_path)
    state = [a]

    async def after():
        if change == "source-change":
            publish(index, record(revision=2))
        else:
            state[0] = replace(a, read=False)

    tools = LocalTools(index, store, lambda: state[0], after=after)
    t = ScriptedTransport(("write" if change == "write-revoke" else "read",))
    r = asyncio.run(run(ctx, index, store, lambda: state[0], t.provider(), tools))
    assert r.stopped == ("stale_source" if change == "source-change" else "forbidden")
    assert all(s.outcome is None for s in r.steps)
    assert store.counts(ctx) == ((1, 1) if change == "write-revoke" else (0, 0))
