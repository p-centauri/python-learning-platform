import asyncio
from dataclasses import replace
import pytest
from unittest.mock import patch
from academy_model_contracts import Adapter, Limits, ModelConfig, build_request, run
from academy_model_contracts.fakes import ScriptedTransport, WaitingTransport, response


@pytest.mark.parametrize("dialect", ["message-v1", "completion-v1"])
def test_two_adapter_formats_settle_known_usage_and_reuse_borrowed_transport(dialect):
    async def scenario():
        config = replace(ModelConfig(), provider_id="configured", dialect=dialect)
        transport = ScriptedTransport((response(dialect),) * 3)
        provider = Adapter(config.provider_id, dialect, transport)
        first = await run(provider, config, ("one", "two"))
        assert first.stopped == "finished" and first.charged == 240
        assert [step.charged for step in first.steps] == [120, 120]
        assert all(step.reserved > step.charged for step in first.steps)
        assert (
            first.model == config.model
            and first.prompt_version == "triage-v1"
            and first.schema_version == "triage-schema-v1"
        )
        again = await run(provider, config, ("three",))
        assert again.charged == 120 and len(transport.requests) == 3
        assert all(type(body) is bytes for body in transport.requests)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "problem", ["wrong-provider", "wrong-dialect", "late-invalid-prompt", "list-prompts", "too-many-prompts"]
)
def test_preflight_refusal_performs_no_provider_call(problem):
    async def scenario():
        config = ModelConfig()
        transport = ScriptedTransport((response(),))
        provider = Adapter(
            "other" if problem == "wrong-provider" else config.provider_id,
            "completion-v1" if problem == "wrong-dialect" else config.dialect,
            transport,
        )
        prompts = ("valid", "") if problem == "late-invalid-prompt" else ("valid",)
        if problem == "list-prompts":
            prompts = ["valid"]
        if problem == "too-many-prompts":
            prompts = ("valid",) * 9
        with pytest.raises(ValueError):
            await run(provider, config, prompts)
        assert not transport.requests

    asyncio.run(scenario())


def test_reservation_before_first_call_and_exact_budget_boundary():
    async def scenario():
        config = ModelConfig()
        reserve = build_request(config, "one").reserve
        transport = ScriptedTransport((response(),))
        provider = Adapter(config.provider_id, config.dialect, transport)
        blocked = await run(provider, config, ("one",), Limits(max_cost=reserve - 1))
        assert (
            blocked.stopped == "cost_limit"
            and blocked.charged == 0
            and not blocked.steps
            and not transport.requests
        )
        admitted = await run(provider, config, ("one",), Limits(max_cost=reserve))
        assert admitted.stopped == "finished" and admitted.charged == 120 and len(transport.requests) == 1

    asyncio.run(scenario())


def test_settlement_allows_later_call_but_reservation_still_gates_each_attempt():
    async def scenario():
        config = ModelConfig()
        reserve = build_request(config, "one").reserve
        transport = ScriptedTransport((response(),) * 2)
        provider = Adapter(config.provider_id, config.dialect, transport)
        enough = await run(provider, config, ("one", "one"), Limits(max_cost=reserve + 120))
        assert enough.stopped == "finished" and enough.charged == 240 and len(enough.steps) == 2
        second = ScriptedTransport((response(),) * 2)
        blocked = await run(
            Adapter(config.provider_id, config.dialect, second),
            config,
            ("one", "one"),
            Limits(max_cost=reserve + 119),
        )
        assert blocked.stopped == "cost_limit" and blocked.charged == 120 and len(second.requests) == 1

    asyncio.run(scenario())


@pytest.mark.parametrize("kind", ["refused", "incomplete"])
def test_refusal_or_incomplete_stops_without_retry_or_partial_decision(kind):
    async def scenario():
        transport = ScriptedTransport((response(kind=kind, text="not JSON"), response()))
        config = ModelConfig()
        result = await run(Adapter(config.provider_id, config.dialect, transport), config, ("one", "two"))
        assert result.stopped == kind and len(result.steps) == len(transport.requests) == 1
        assert result.steps[0].decision is None and result.charged == 120
        assert "not JSON" not in repr(result)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "raw,kind",
    [
        (RuntimeError("private-api-secret"), "provider_error"),
        (b"broken private-api-secret", "invalid_response"),
        (response(model="changed-model"), "invalid_response"),
    ],
)
def test_unknown_usage_keeps_entire_reservation_and_redacts_failure(raw, kind):
    async def scenario():
        config = ModelConfig()
        transport = ScriptedTransport((raw, response()))
        report = await run(Adapter(config.provider_id, config.dialect, transport), config, ("one", "two"))
        assert report.stopped == kind and len(transport.requests) == 1 and len(report.steps) == 1
        assert report.charged == build_request(config, "one").reserve == report.steps[0].reserved
        assert report.steps[0].usage is None and report.steps[0].decision is None
        assert "private-api-secret" not in repr(report)

    asyncio.run(scenario())


def test_step_limit_counts_actual_attempts_not_successful_answers():
    async def scenario():
        config = ModelConfig()
        transport = ScriptedTransport((response(),) * 3)
        report = await run(
            Adapter(config.provider_id, config.dialect, transport),
            config,
            ("one", "two", "three"),
            Limits(max_steps=2),
        )
        assert (
            report.stopped == "step_limit"
            and len(report.steps) == len(transport.requests) == 2
            and report.charged == 240
        )

    asyncio.run(scenario())


def test_timeout_awaits_cooperative_cleanup_and_retains_unknown_charge():
    async def scenario():
        config = ModelConfig()
        transport = WaitingTransport()
        report = await run(
            Adapter(config.provider_id, config.dialect, transport), config, ("one",), Limits(timeout_ms=10)
        )
        assert report.stopped == "timeout" and transport.entered.is_set() and transport.finished.is_set()
        assert report.charged == build_request(config, "one").reserve and report.steps[0].usage is None
        assert len(transport.requests) == 1

    asyncio.run(scenario())


def test_external_cancellation_propagates_after_provider_cleanup():
    async def scenario():
        config = ModelConfig()
        transport = WaitingTransport()
        task = asyncio.create_task(
            run(Adapter(config.provider_id, config.dialect, transport), config, ("one",))
        )
        await transport.entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert transport.finished.is_set() and len(transport.requests) == 1

    asyncio.run(scenario())


def test_empty_input_and_zero_rates_are_finite_not_invented_work():
    async def scenario():
        config = replace(ModelConfig(), input_rate=0, output_rate=0)
        transport = ScriptedTransport((response(),))
        provider = Adapter(config.provider_id, config.dialect, transport)
        empty = await run(provider, config, (), Limits(max_cost=0))
        assert (
            empty.stopped == "finished" and empty.charged == 0 and not empty.steps and not transport.requests
        )
        free = await run(provider, config, ("one",), Limits(max_cost=0))
        assert free.stopped == "finished" and free.charged == 0 and len(transport.requests) == 1

    asyncio.run(scenario())


def test_total_cooperative_deadline_is_not_reset_for_each_call():
    async def scenario():
        waiting = WaitingTransport()

        class TwoCalls:
            def __init__(self):
                self.calls = 0

            async def send(self, body):
                self.calls += 1
                if self.calls == 1:
                    await asyncio.sleep(0)
                    return response()
                return await waiting.send(body)

        config = ModelConfig()
        transport = TwoCalls()
        intervals = []
        original = asyncio.timeout

        def observed(delay):
            intervals.append(delay)
            return original(delay)

        with patch("academy_model_contracts.operations.asyncio.timeout", side_effect=observed):
            report = await run(
                Adapter(config.provider_id, config.dialect, transport),
                config,
                ("one", "two"),
                Limits(timeout_ms=20),
            )
        assert report.stopped == "timeout" and [step.kind for step in report.steps] == ["complete", "timeout"]
        assert len(intervals) == 2 and 0 < intervals[1] < intervals[0] <= 0.02
        assert waiting.finished.is_set() and report.charged == 120 + build_request(config, "two").reserve

    asyncio.run(scenario())
