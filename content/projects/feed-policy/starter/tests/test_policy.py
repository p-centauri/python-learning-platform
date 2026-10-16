import inspect
import logging

import pytest

from academy_feed_policy import RuleError, apply_policy, logged_report, make_selector, parse_selector
import academy_feed_policy.policy as policy


@pytest.mark.parametrize("spec,expected", [
    ("a:0", ("a", 0)), ("api-2:10", ("api-2", 10)),
    ("abcdefghijklmnop:60000", ("abcdefghijklmnop", 60000)),
])
def test_valid_rules(spec, expected):
    assert parse_selector(spec) == expected


@pytest.mark.parametrize("spec", [
    "", "api", ":1", "Api:1", "1api:1", "api_:1", "api:01", "api:+1",
    "api:-1", "api:1.0", "api:١", "api:1\n", " api:1", "api: 1", "api:1:2",
    "api:60001", "abcdefghijklmnopq:1", "a:" + "9" * 1000, None, 1, True,
])
def test_invalid_rules_are_redacted(spec):
    with pytest.raises(RuleError) as error:
        parse_selector(spec)
    assert str(error.value) == "Invalid selector"


@pytest.mark.parametrize("prefix,minimum", [
    ("", 0), ("UPPER", 0), ("a" * 17, 0), ("api", -1), ("api", 60001),
    ("api", True), ("api", 1.0), (None, 1),
])
def test_invalid_settings(prefix, minimum):
    with pytest.raises(RuleError):
        make_selector(prefix=prefix, minimum=minimum)


def test_independent_closures_and_inclusive_boundary(readings):
    api = make_selector(prefix="api", minimum=20)
    worker = make_selector(prefix="worker", minimum=0)
    assert [api(row) for row in readings] == [False, True, False]
    assert [worker(row) for row in readings] == [False, False, True]
    assert [api(row) for row in readings] == [False, True, False]


def test_settings_require_keywords():
    with pytest.raises(TypeError):
        make_selector("api", 0)


@pytest.mark.parametrize("source_id", ["demo-feed", "a" * 32])
def test_wrapper_preserves_input_result_metadata_and_logs(readings, logger, caplog, source_id):
    result = {"count": 3, "total": 55}
    calls = []

    def report(rows, /):
        """Original report documentation."""
        calls.append(rows)
        return result

    wrapped = logged_report(report, logger=logger, source_id=source_id)
    assert wrapped.__name__ == report.__name__
    assert wrapped.__doc__ == report.__doc__
    assert wrapped.__wrapped__ is report
    assert inspect.signature(wrapped) == inspect.signature(report)
    with caplog.at_level(logging.INFO, logger=logger.name):
        assert wrapped(readings) is result
    assert len(calls) == 1 and calls[0] is readings
    assert [entry.getMessage() for entry in caplog.records] == [
        "feed_report_started", "feed_report_succeeded",
    ]
    assert [entry.levelno for entry in caplog.records] == [logging.INFO, logging.INFO]
    assert all(entry.source_id == source_id for entry in caplog.records)
    assert caplog.records[1].record_count == 3
    assert all(entry.exc_info is None and entry.stack_info is None for entry in caplog.records)
    assert "55" not in caplog.text


def test_error_identity_without_sensitive_exception_logs(readings, logger, caplog):
    failure = ValueError("SECRET payload https://private.example/token")
    calls = []

    def fail(rows, /):
        calls.append(rows)
        raise failure

    wrapped = logged_report(fail, logger=logger, source_id="feed-a")
    with caplog.at_level(logging.INFO, logger=logger.name), pytest.raises(ValueError) as caught:
        wrapped(readings)
    assert caught.value is failure
    assert len(calls) == 1 and calls[0] is readings
    assert [entry.getMessage() for entry in caplog.records] == ["feed_report_started", "feed_report_failed"]
    assert caplog.records[-1].levelno == logging.WARNING
    assert all(entry.exc_info is None and entry.stack_info is None for entry in caplog.records)
    assert all(not hasattr(entry, "record_count") for entry in caplog.records)
    assert "SECRET" not in caplog.text and "private.example" not in caplog.text


@pytest.mark.parametrize("source_id", ["", "Bad", "a" * 33, "feed/token", "feed\n", None])
def test_label_validation_before_call(source_id, logger):
    def unused(rows, /):
        pytest.fail("reporter called during configuration")
    with pytest.raises(RuleError) as caught:
        logged_report(unused, logger=logger, source_id=source_id)
    assert str(caught.value) == "Invalid source label"


def test_wrapper_positional_only(logger):
    wrapped = logged_report(lambda rows: {"count": 0, "total": 0}, logger=logger, source_id="feed")
    with pytest.raises(TypeError):
        wrapped(records=[])


def test_interrupt_is_not_converted_or_retried(logger, caplog):
    failure = KeyboardInterrupt()
    def interrupt(rows, /):
        raise failure
    with caplog.at_level(logging.INFO, logger=logger.name), pytest.raises(KeyboardInterrupt) as caught:
        logged_report(interrupt, logger=logger, source_id="feed")([])
    assert caught.value is failure
    assert [entry.getMessage() for entry in caplog.records] == ["feed_report_started"]


def test_lazy_one_pass_pipeline_borrows_source(readings):
    class Borrowed:
        consumed = 0
        closed = False
        def __iter__(self):
            for row in readings:
                self.consumed += 1
                yield row
        def close(self):
            self.closed = True
    source = Borrowed()
    calls = []
    def report(rows, /):
        assert source.consumed == 0
        calls.append(rows)
        selected = list(rows)
        return {"count": len(selected), "total": sum(row.value for row in selected)}
    assert apply_policy(source, selector=make_selector(prefix="api", minimum=10), reporter=report) == {
        "count": 1, "total": 20,
    }
    assert len(calls) == 1 and source.consumed == 3 and not source.closed


def test_late_source_failure_never_logs_success(readings, logger, caplog):
    failure = RuntimeError("SECRET late failure")
    def source():
        yield readings[1]
        raise failure
    def report(rows, /):
        total = count = 0
        for row in rows:
            total += row.value
            count += 1
        return {"count": count, "total": total}
    wrapped = logged_report(report, logger=logger, source_id="feed")
    with caplog.at_level(logging.INFO, logger=logger.name), pytest.raises(RuntimeError) as caught:
        apply_policy(source(), selector=make_selector(prefix="api", minimum=0), reporter=wrapped)
    assert caught.value is failure
    assert "feed_report_succeeded" not in caplog.text and "SECRET" not in caplog.text


def test_patch_lookup_site_keeps_real_validation(monkeypatch):
    real_match = policy.re.fullmatch
    calls = []
    def observed(pattern, value):
        calls.append(value)
        return real_match(pattern, value)
    monkeypatch.setattr(policy.re, "fullmatch", observed)
    assert parse_selector("api:10") == ("api", 10)
    assert calls == ["api:10"]


def test_long_input_rejected_before_matching(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("unbounded matching attempted")
    monkeypatch.setattr(policy.re, "fullmatch", forbidden)
    with pytest.raises(RuleError):
        parse_selector("api:" + "1" * 1000)
