"""Run original controlled RAG experiments; imports remain quiet and no provider network is used."""

import argparse
import asyncio
from dataclasses import asdict, replace
from importlib.metadata import version
import json
from pathlib import Path
import tempfile
from academy_model_contracts import Limits
from academy_retrieval import Principal
from academy_rag import Index, Policy, Record, Result, answer, prepare, publish, resolve
from academy_rag.fixtures import CONFIG, PRINCIPAL, QUERY, REQUIRED, SPEC, VERSION, Scripted, record


async def experiments(directory: Path) -> dict[str, object]:
    index = Index(directory / "index.db", SPEC)
    index.initialize()
    publish(index, record())
    publish(index, record(id="private", groups=("admin",), text="private-fixture-marker file failure"))
    publish(index, record(id="foreign", tenant="beta", text="foreign-fixture-marker file failure"))
    bundle = prepare(index, PRINCIPAL, QUERY, REQUIRED)
    examples: dict[str, object] = {}

    async def run(name: str, fake: Scripted, *, limits: Limits = Limits(max_steps=1)) -> Result:
        result = await answer(index, bundle, lambda: PRINCIPAL, fake.adapter(), CONFIG, limits)
        examples[name] = {"result": asdict(result), "requests": len(fake.requests), "cleanup": fake.cleaned}
        return result

    accepted = await run("current", Scripted())
    assert accepted.reason == "answered" and accepted.citations
    for mode in ("refused", "incomplete", "wrong-quote", "wrong-id", "wrong-model", "error"):
        result = await run(mode, Scripted(mode))
        assert result.text is None and not result.citations
    await run("cost-blocked", Scripted(), limits=Limits(max_cost=0))
    await run("timeout", Scripted("wait"), limits=Limits(timeout_ms=10))
    no_evidence = prepare(index, PRINCIPAL, QUERY, ("moon",))
    fake = Scripted()
    missing = await answer(index, no_evidence, lambda: PRINCIPAL, fake.adapter(), CONFIG)
    examples["missing"] = {"result": asdict(missing), "requests": len(fake.requests)}
    assert missing.reason == "missing_evidence" and not fake.requests
    small = prepare(index, PRINCIPAL, QUERY, REQUIRED, policy=Policy(context_bytes=16))
    no_context = await answer(index, small, lambda: PRINCIPAL, Scripted().adapter(), CONFIG)
    examples["whole-context-only"] = asdict(no_context)
    assert no_context.attempts == 0
    context = await answer(
        index, bundle, lambda: PRINCIPAL, Scripted().adapter(), replace(CONFIG, context_units=1)
    )
    examples["context-blocked"] = asdict(context)
    assert context.reason == "context_limit" and context.attempts == 0
    state = [PRINCIPAL]
    fake = Scripted(change=lambda: state.__setitem__(0, Principal("beta")))
    changed = await answer(index, bundle, lambda: state[0], fake.adapter(), CONFIG)
    examples["principal-changed"] = asdict(changed)
    assert changed.reason == "principal_changed" and changed.text is None
    other = Index(index.path, SPEC)

    def update_source() -> None:
        publish(other, record(revision=2, text="Close the file after a failure before starting a new task."))

    fake = Scripted(change=update_source)
    stale = await answer(index, bundle, lambda: PRINCIPAL, fake.adapter(), CONFIG)
    examples["changed-during-call"] = asdict(stale)
    assert stale.reason == "stale_evidence" and stale.text is None
    assert resolve(index, accepted.citations[0], PRINCIPAL) is None
    bundle = prepare(index, PRINCIPAL, QUERY, REQUIRED)
    updated = await run("updated", Scripted())
    assert updated.citations[0].span.key.revision == 2
    publish(index, Record("alpha", "files", 3, None))
    bundle = prepare(index, PRINCIPAL, QUERY, REQUIRED)
    deleted = await run("deleted", Scripted())
    assert deleted.reason == "missing_evidence" and deleted.attempts == 0
    assert resolve(index, updated.citations[0], PRINCIPAL) is None
    assert not publish(index, Record("alpha", "files", 3, None))
    conflict = False
    try:
        publish(index, record())
    except ValueError:
        conflict = True
    assert conflict
    reopened = Index(index.path, SPEC).snapshot()
    assert reopened == index.snapshot()
    cancelled = Scripted("wait")
    # Use another current source, since the first has a retained deletion marker.
    publish(index, record(id="cancel"))
    bundle = prepare(index, PRINCIPAL, QUERY, REQUIRED)
    task = asyncio.create_task(answer(index, bundle, lambda: PRINCIPAL, cancelled.adapter(), CONFIG))
    await asyncio.wait_for(cancelled.entered.wait(), 1)
    task.cancel()
    propagated = False
    try:
        await task
    except asyncio.CancelledError:
        propagated = True
    assert propagated and cancelled.cleaned
    examples["external-cancellation"] = {
        "propagated": propagated,
        "cleanup": cancelled.cleaned,
        "requests": len(cancelled.requests),
        "durable_call_ledger": False,
    }
    return {
        "package": version("academy-rag-lab"),
        "dependencies": {
            "retrieval": version("academy-retrieval-lab"),
            "model": version("academy-model-contracts-lab"),
        },
        "fixture": VERSION,
        "schema": "rag-quotes-v1",
        "store": "rag-store-v1",
        "deleted_revision_survives_reopen": True,
        "old_publish_refused": conflict,
        "old_citations_unresolvable": True,
        "scope": "Controlled provider quotes and hand-supplied vectors; separate local SQLite index, no model/network/ANN/freeform entailment or held-out quality; no automatic mastery",
        "examples": examples,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="rag-demo-") as directory:
        report = asyncio.run(experiments(Path(directory)))
    rendered = json.dumps(report, indent=2) + "\n"
    assert "private-fixture-marker" not in rendered and "foreign-fixture-marker" not in rendered
    if args.output:
        args.output.write_text(rendered)
        assert json.loads(args.output.read_text()) == json.loads(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
