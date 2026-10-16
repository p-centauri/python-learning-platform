import argparse
import asyncio
from dataclasses import asdict, replace
import json
from pathlib import Path
from importlib.metadata import version
from academy_model_contracts import Adapter, Dialect, Limits, ModelConfig, build_request, run
from academy_model_contracts.fakes import ScriptedTransport, WaitingTransport, response


async def observe() -> dict[str, object]:
    examples: dict[str, object] = {}
    for dialect in ("message-v1", "completion-v1"):
        chosen: Dialect = "message-v1" if dialect == "message-v1" else "completion-v1"
        config = replace(
            ModelConfig(), provider_id="fixture-a" if dialect == "message-v1" else "fixture-b", dialect=chosen
        )
        transport = ScriptedTransport((response(chosen), response(chosen)))
        report = await run(
            Adapter(config.provider_id, chosen, transport),
            config,
            ("Inspect a Python traceback", "Inspect a database rollback"),
        )
        assert report.stopped == "finished" and report.charged == 240 and len(transport.requests) == 2
        examples[dialect] = dict(report=asdict(report), requests=len(transport.requests), fixture_only=True)
    config = ModelConfig()
    for name, raw, stop in [
        ("refusal", response(kind="refused", text="not executable output"), "refused"),
        ("incomplete", response(kind="incomplete", text="{partial"), "incomplete"),
        ("malformed", b"invalid private-fixture-marker", "invalid_response"),
        ("provider-error", RuntimeError("private-fixture-marker"), "provider_error"),
        ("wrong-model", response(model="fixture-model-changed"), "invalid_response"),
    ]:
        transport = ScriptedTransport((raw, response()))
        report = await run(Adapter(config.provider_id, config.dialect, transport), config, ("one", "two"))
        assert report.stopped == stop and len(transport.requests) == 1
        assert report.steps[0].decision is None and "private-fixture-marker" not in repr(report)
        examples[name] = dict(report=asdict(report), requests=len(transport.requests))
    reserve = build_request(config, "one").reserve
    transport = ScriptedTransport((response(),))
    blocked = await run(
        Adapter(config.provider_id, config.dialect, transport), config, ("one",), Limits(max_cost=reserve - 1)
    )
    assert blocked.stopped == "cost_limit" and not transport.requests and not blocked.steps
    examples["cost-blocked"] = dict(report=asdict(blocked), requests=0, required_reserve=reserve)
    transport = ScriptedTransport((response(),) * 3)
    limited = await run(
        Adapter(config.provider_id, config.dialect, transport),
        config,
        ("one", "two", "three"),
        Limits(max_steps=2),
    )
    assert limited.stopped == "step_limit" and len(transport.requests) == 2
    examples["step-limited"] = dict(report=asdict(limited), requests=2)
    waiting = WaitingTransport()
    timeout = await run(
        Adapter(config.provider_id, config.dialect, waiting), config, ("one",), Limits(timeout_ms=10)
    )
    assert (
        timeout.stopped == "timeout"
        and waiting.entered.is_set()
        and waiting.finished.is_set()
        and timeout.charged == reserve
    )
    examples["timeout"] = dict(report=asdict(timeout), requests=len(waiting.requests), cleanup_awaited=True)
    waiting = WaitingTransport()
    task = asyncio.create_task(run(Adapter(config.provider_id, config.dialect, waiting), config, ("one",)))
    await waiting.entered.wait()
    task.cancel()
    cancelled = False
    try:
        await task
    except asyncio.CancelledError:
        cancelled = True
    assert cancelled and waiting.finished.is_set()
    examples["external-cancellation"] = dict(
        propagated=cancelled, cleanup_awaited=True, requests=len(waiting.requests), durable_ledger=False
    )
    context_refused = False
    try:
        build_request(replace(config, context_units=1), "one")
    except ValueError:
        context_refused = True
    assert context_refused
    return dict(
        schema="2026.10-model-contracts-v1",
        package=version("academy-model-contracts-lab"),
        transport="scripted offline bytes; no network or model",
        accounting="complete UTF-8 request-byte fixture units and fictional integer credits; not a tokenizer or billing guarantee",
        context_overflow_refused=context_refused,
        examples=examples,
        limits="Finite application contracts only; no factual quality, provider conformance, real pricing, hidden usage, hard cancellation or authorization proof.",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = asyncio.run(observe())
    serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(serialized)
    print(serialized, end="")


if __name__ == "__main__":
    main()
