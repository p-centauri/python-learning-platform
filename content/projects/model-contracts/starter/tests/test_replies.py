from dataclasses import replace
import json
import pytest
from academy_model_contracts import ModelConfig, build_request, decode_reply
from academy_model_contracts.fakes import response
from academy_model_contracts.support import encode


@pytest.mark.parametrize("dialect", ["message-v1", "completion-v1"])
@pytest.mark.parametrize("kind", ["complete", "refused", "incomplete"])
def test_distinct_provider_outcomes_preserve_usage_and_only_complete_has_decision(dialect, kind):
    request = build_request(replace(ModelConfig(), dialect=dialect), "Review this failure")
    text = None if kind == "complete" else "{malformed partial or refusal; no parsing or execution}"
    reply = decode_reply(response(dialect, kind=kind, input_units=0, output_units=0, text=text), request)
    assert reply.kind == kind and reply.usage.input_units == reply.usage.output_units == 0
    assert (reply.decision is not None) == (kind == "complete")
    if reply.decision:
        assert reply.decision.queue == "python" and reply.decision.needs_human is True
    assert "malformed partial" not in repr(reply)


@pytest.mark.parametrize(
    "text",
    [
        '{"queue":"python","summary":"x","needs_human":true,"tenant":"other"}',
        '{"queue":"python","summary":"x","needs_human":true,"queue":"http"}',
        '{"queue":"python","summary":"x","needs_human":NaN}',
        '{"queue":"python","summary":"x","needs_human":"false"}',
        '{"queue":"admin","summary":"x","needs_human":false}',
        '{"queue":"python","needs_human":true}',
        "[]",
        "```json\n{}\n```",
        "{} trailing",
        "x" * 4097,
    ],
)
def test_completed_untrusted_output_is_strict_not_repaired(text):
    request = build_request(ModelConfig(), "Review")
    with pytest.raises(ValueError):
        decode_reply(response(text=text), request)


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong-model",
        "unknown-status",
        "mixed-refusal",
        "extra-envelope",
        "missing-usage",
        "bool-input",
        "negative-output",
        "input-over-bound",
        "output-over-cap",
        "empty-refusal",
    ],
)
def test_wrong_identity_usage_or_variant_is_refused(mutation):
    request = build_request(ModelConfig(), "Review")
    payload = json.loads(response())
    if mutation == "wrong-model":
        payload["model"] = "fixture-model-new"
    elif mutation == "unknown-status":
        payload["status"] = "streaming"
    elif mutation == "mixed-refusal":
        payload["refusal"] = "do not also complete"
    elif mutation == "extra-envelope":
        payload["url"] = "https://untrusted.invalid"
    elif mutation == "missing-usage":
        del payload["usage"]
    elif mutation == "bool-input":
        payload["usage"]["input"] = True
    elif mutation == "negative-output":
        payload["usage"]["output"] = -1
    elif mutation == "input-over-bound":
        payload["usage"]["input"] = request.input_bound + 1
    elif mutation == "output-over-cap":
        payload["usage"]["output"] = request.config.output_units + 1
    elif mutation == "empty-refusal":
        payload.update(status="refused", text=None, refusal="")
    with pytest.raises(ValueError):
        decode_reply(encode(payload), request)


@pytest.mark.parametrize(
    "raw",
    [None, {}, b"\xff", b"{} trailing", b"x" * 16385, b'{"model":"a","model":"b"}', b'{"value":Infinity}'],
)
def test_bad_raw_bytes_never_become_a_proposal(raw):
    with pytest.raises(ValueError):
        decode_reply(raw, build_request(ModelConfig(), "Review"))


def test_completion_variant_rejects_mixed_result_and_cross_dialect():
    request = build_request(replace(ModelConfig(), dialect="completion-v1"), "Review")
    payload = json.loads(response("completion-v1"))
    payload["result"]["refusal"] = "mixed"
    with pytest.raises(ValueError):
        decode_reply(encode(payload), request)
    with pytest.raises(ValueError):
        decode_reply(response("message-v1"), request)
