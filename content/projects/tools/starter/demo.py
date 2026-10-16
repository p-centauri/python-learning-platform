"""Guarded local experiments; no provider/network or academy database access."""

import argparse
import asyncio
from dataclasses import asdict, replace
from importlib.metadata import version
import json
from pathlib import Path
import tempfile
from academy_model_contracts import Limits, ModelConfig
from academy_rag import publish
from academy_rag.fixtures import record
from academy_tools import Call, LocalTools, Store, execute, run
from academy_tools.fixtures import FIXTURE, ScriptedTransport, setup


async def experiments(directory: Path) -> dict[str, object]:
    results: dict[str, object] = {}
    modes = {
        "normal": ("read", "write", "finish"),
        "duplicate-new-id": ("write", "new-id", "finish"),
        "unapproved-change": ("changed",),
        "unknown-tool": ("unknown",),
        "extra-authority": ("extra",),
        "refused": ("refused",),
        "incomplete": ("incomplete",),
        "provider-error": ("error",),
        "provider-timeout": ("wait",),
        "step-limit": ("read",),
        "cost-blocked": ("write",),
        "context-blocked": ("write",),
        "permission-change": ("write",),
        "source-change": ("write",),
        "tool-before-timeout": ("write",),
        "tool-after-timeout": ("write",),
    }
    for name, sequence in modes.items():
        area = directory / name
        area.mkdir()
        index, store, ctx, granted = setup(area)
        state = [granted]
        cleanup: list[bool] = []

        def change() -> None:
            if name == "permission-change":
                state[0] = replace(granted, read=False)
            if name == "source-change":
                publish(index, record(revision=2))

        async def wait() -> None:
            try:
                await asyncio.Event().wait()
            finally:
                await asyncio.sleep(0)
                cleanup.append(True)

        transport = ScriptedTransport(sequence, change)
        tools = LocalTools(
            index,
            store,
            lambda: state[0],
            before=wait if name == "tool-before-timeout" else None,
            after=wait if name == "tool-after-timeout" else None,
        )
        limits = Limits(timeout_ms=30) if "timeout" in name else Limits()
        if name == "step-limit":
            limits = Limits(max_steps=1)
        if name == "cost-blocked":
            limits = Limits(max_cost=0)
        config = ModelConfig(
            prompt_version="tools-v1", context_units=16 if name == "context-blocked" else 8192
        )
        report = await run(ctx, index, store, lambda: state[0], transport.provider(), tools, config, limits)
        value: dict[str, object] = {
            "report": asdict(report),
            "requests": len(transport.requests),
            "notes_receipts": store.counts(ctx),
            "cleanup": transport.cleaned or bool(cleanup),
        }
        if name == "tool-after-timeout":
            reopened = Store(store.path)
            reopened.initialize()
            replay = execute(
                ctx,
                Call("new-retry-id", "save_note", "e0", "Review file cleanup"),
                index,
                reopened,
                lambda: granted,
            )
            value["explicit_replay"] = asdict(replay)
            value["after_replay_notes_receipts"] = reopened.counts(ctx)
        results[name] = value
    area = directory / "cancel"
    area.mkdir()
    index, store, ctx, granted = setup(area)
    entered = asyncio.Event()
    clean = []

    async def after() -> None:
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            await asyncio.sleep(0)
            clean.append(True)

    transport = ScriptedTransport(("write",))
    tools = LocalTools(index, store, lambda: granted, after=after)
    task = asyncio.create_task(run(ctx, index, store, lambda: granted, transport.provider(), tools))
    await asyncio.wait_for(entered.wait(), 1)
    task.cancel()
    propagated = False
    try:
        await task
    except asyncio.CancelledError:
        propagated = True
    reopened = Store(store.path)
    reopened.initialize()
    replay = execute(
        ctx,
        Call("retry-after-cancel", "save_note", "e0", "Review file cleanup"),
        index,
        reopened,
        lambda: granted,
    )
    results["external-cancellation"] = {
        "propagated": propagated,
        "cleanup": bool(clean),
        "requests": len(transport.requests),
        "notes_receipts": reopened.counts(ctx),
        "replay": replay.reason,
        "durable_provider_cost_ledger": False,
    }
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-tools-demo-") as folder:
        results = asyncio.run(experiments(Path(folder)))
    report = {
        "package": version("academy-tools-lab"),
        "dependencies": {
            "model": version("academy-model-contracts-lab"),
            "retrieval": version("academy-retrieval-lab"),
            "rag": version("academy-rag-lab"),
        },
        "fixture": FIXTURE,
        "schema": "tool-proposals-v1",
        "store": "tool-store-v1",
        "examples": results,
        "scope": "Controlled proposals, exact application approvals and separate local SQLite notes/receipts. No external side effects, real model quality, distributed exactly-once or automatic mastery.",
    }
    serialized = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(serialized + "\n")
        assert json.loads(args.output.read_text()) == json.loads(serialized)
    print(serialized)


if __name__ == "__main__":
    main()
