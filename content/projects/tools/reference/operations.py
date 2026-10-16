import asyncio
from collections.abc import Callable
from dataclasses import replace
import sqlite3
from academy_model_contracts import Limits, ModelConfig, Provider, Request, Usage
from academy_model_contracts.contracts import identifier, integer
from academy_rag import Index, resolve
from .contracts import Authority, Call, Context, Outcome, Proposal, Report, Step, Toolbox, label
from .store import Store
from .support import LocalTools, approval_for, current, fields, parse, request


def decode_proposal(raw: object, sent: Request) -> Proposal:
    root = fields(parse(raw), {"model", "schema", "status", "proposal", "usage"})
    if root["model"] != sent.config.model or root["schema"] != "tool-proposals-v1":
        raise ValueError("wrong configured model/schema")
    usage = fields(root["usage"], {"input_units", "output_units"})
    measured = Usage(
        integer(usage["input_units"], 0, sent.input_bound),
        integer(usage["output_units"], 0, sent.config.output_units),
    )
    status = root["status"]
    if status in ("refused", "incomplete"):
        if root["proposal"] is not None:
            raise ValueError("noncomplete proposal")
        return Proposal(status, None, measured)
    if status != "complete":
        raise ValueError("invalid status")
    value = root["proposal"]
    if type(value) is dict and value == {"kind": "finish"}:
        return Proposal("finish", None, measured)
    call = fields(value, {"kind", "id", "name", "arguments"})
    if call["kind"] != "call":
        raise ValueError("invalid proposal variant")
    name = call["name"]
    if name == "source_excerpt":
        args = fields(call["arguments"], {"citation"})
        action = Call(identifier(call["id"]), "source_excerpt", identifier(args["citation"]))
    elif name == "save_note":
        args = fields(call["arguments"], {"citation", "label"})
        action = Call(identifier(call["id"]), "save_note", identifier(args["citation"]), label(args["label"]))
    else:
        raise ValueError("unknown tool")
    return Proposal("call", action, measured)


def execute(
    context: Context, call: Call, index: Index, store: Store, authority: Callable[[], Authority]
) -> Outcome:
    if type(context) is not Context or type(call) is not Call:
        raise ValueError("exact application context/proposal required")
    try:
        granted = current(context, index, authority)
        citation = next((c for c in context.citations if c.id == call.citation), None)
        if citation is None:
            return Outcome("unknown_citation", call.id)
        text = resolve(index, citation, granted.principal)
        if text is None:
            return Outcome("stale_source", call.id)
        if call.name == "source_excerpt":
            return Outcome("read", call.id, text=text)
        fingerprint = approval_for(context, call)
        if granted.approval != fingerprint:
            return Outcome("approval_required", call.id)
        note_id, replayed = store.commit(context, fingerprint, label(call.label), citation.span.digest)
        return Outcome("replayed" if replayed else "written", call.id, note_id=note_id, replayed=replayed)
    except ValueError as error:
        reason = str(error)
        if reason not in ("forbidden", "stale_source", "operation_conflict", "effect_limit"):
            raise
        return Outcome(reason, call.id)
    except sqlite3.Error:
        return Outcome("store_error", call.id)


async def run(
    context: Context,
    index: Index,
    store: Store,
    authority: Callable[[], Authority],
    provider: Provider,
    tools: Toolbox | None = None,
    config: ModelConfig = ModelConfig(prompt_version="tools-v1"),
    limits: Limits = Limits(),
) -> Report:
    if type(context) is not Context or type(config) is not ModelConfig or type(limits) is not Limits:
        raise ValueError("exact configured inputs required")
    if provider.provider_id != config.provider_id or provider.dialect != config.dialect:
        raise ValueError("configured provider mismatch")
    toolbox = tools if tools is not None else LocalTools(index, store, authority)
    steps: list[Step] = []
    history: list[Outcome] = []
    charged = 0
    attempts = 0
    phase = "provider"
    reservation = 0
    usage: Usage | None = None

    def report(reason: str) -> Report:
        return Report(
            reason, charged, attempts, tuple(steps), config.provider_id, config.model, config.prompt_version
        )

    try:
        async with asyncio.timeout(limits.timeout_ms / 1000):
            for number in range(limits.max_steps):
                try:
                    current(context, index, authority)
                except ValueError as error:
                    return report(str(error))
                sent = request(context, config, tuple(history))
                if sent.input_bound + config.output_units > config.context_units:
                    return report("context_limit")
                reservation = sent.reserve
                if charged + reservation > limits.max_cost:
                    return report("cost_limit")
                charged += reservation
                attempts += 1
                phase = "provider"
                usage = None
                try:
                    raw = await provider.complete(sent)
                except Exception:
                    steps.append(Step(number, "provider_error", reservation, None))
                    return report("provider_error")
                try:
                    proposal = decode_proposal(raw, sent)
                except (ValueError, UnicodeError, RecursionError):
                    steps.append(Step(number, "invalid_proposal", reservation, None))
                    return report("invalid_proposal")
                usage = proposal.usage
                cost = usage.input_units * config.input_rate + usage.output_units * config.output_rate
                charged += cost - reservation
                try:
                    current(context, index, authority)
                except ValueError as error:
                    steps.append(Step(number, "authority_changed", cost, usage))
                    return report(str(error))
                if proposal.kind != "call":
                    steps.append(Step(number, proposal.kind, cost, usage))
                    return report("finished" if proposal.kind == "finish" else proposal.kind)
                assert proposal.call is not None
                phase = "tool"
                try:
                    outcome = await toolbox.invoke(context, proposal.call)
                except Exception:
                    steps.append(Step(number, "tool_uncertain", cost, usage))
                    return report("tool_uncertain")
                if type(outcome) is not Outcome or outcome.call_id != proposal.call.id:
                    steps.append(Step(number, "tool_uncertain", cost, usage))
                    return report("tool_uncertain")
                try:
                    current(context, index, authority)
                except ValueError as error:
                    steps.append(Step(number, "authority_changed", cost, usage))
                    return report(str(error))
                # Public evidence reports never repeat source text; only fresh prompt history does.
                steps.append(Step(number, "call", cost, usage, replace(outcome, text=None)))
                if outcome.reason not in ("read", "written", "replayed"):
                    return report(outcome.reason)
                history.append(outcome)
            return report("step_limit")
    except TimeoutError:
        cost = (
            reservation
            if usage is None
            else usage.input_units * config.input_rate + usage.output_units * config.output_rate
        )
        steps.append(
            Step(len(steps), "provider_timeout" if phase == "provider" else "tool_timeout", cost, usage)
        )
        return report("provider_timeout" if phase == "provider" else "tool_timeout")
