import pytest
from academy_measured_cache import Measurement, sample


def test_exact_call_order_samples_and_last_identity():
    events, values = [], [object(), object()]
    ticks = iter([2, 5, 8, 12])

    def clock():
        events.append("clock")
        return next(ticks)

    def work():
        events.append("work")
        return values[len([x for x in events if x == "work"]) - 1]

    result = sample(work, repeats=2, clock=clock)
    assert result.elapsed_ns == (3, 4) and result.last is values[-1]
    assert events == ["clock", "work", "clock", "clock", "work", "clock"]


@pytest.mark.parametrize(
    "repeats,error",
    [
        (True, TypeError),
        (1.0, TypeError),
        ("3", TypeError),
        (0, ValueError),
        (8, ValueError),
        (-1, ValueError),
    ],
)
def test_validation_before_work_or_clock(repeats, error):
    def forbidden():
        raise AssertionError("touched")

    with pytest.raises(error):
        sample(forbidden, repeats=repeats, clock=forbidden)


@pytest.mark.parametrize("repeats", [1, 3, 7])
def test_finite_repetitions_and_zero_duration(repeats):
    calls = []
    result = sample(lambda: calls.append(True), repeats=repeats, clock=lambda: 0)
    assert len(calls) == repeats and result.last is None and result.elapsed_ns == (0,) * repeats


@pytest.mark.parametrize(
    "ticks,error,work_calls",
    [
        ([True], TypeError, 0),
        ([-1], ValueError, 0),
        ([1.0], TypeError, 0),
        ([2, False], TypeError, 1),
        ([2, 1], ValueError, 1),
        ([2, 5, 4], ValueError, 1),
        ([0, 0, 0, 0], None, 2),
    ],
)
def test_clock_types_monotonicity_and_effects(ticks, error, work_calls):
    iterator = iter(ticks)
    calls = []
    if error:
        with pytest.raises(error):
            sample(lambda: calls.append(True), repeats=2, clock=lambda: next(iterator))
    else:
        assert sample(lambda: calls.append(True), repeats=2, clock=lambda: next(iterator)).elapsed_ns == (
            0,
            0,
        )
    assert len(calls) == work_calls


def test_work_failure_preserves_error_and_no_end_clock():
    events = []
    error = LookupError("work")

    def work():
        events.append("work")
        raise error

    def clock():
        events.append("clock")
        return 2

    with pytest.raises(LookupError) as caught:
        sample(work, clock=clock)
    assert caught.value is error and events == ["clock", "work"]


@pytest.mark.parametrize("phase", [0, 1, 2])
def test_clock_failure_preserves_error_and_prior_effects(phase):
    events = []
    error = OSError("clock")
    calls = 0

    def clock():
        nonlocal calls
        calls += 1
        if calls == phase + 1:
            raise error
        return calls

    with pytest.raises(OSError) as caught:
        sample(lambda: events.append(True), clock=clock)
    assert caught.value is error and len(events) == (0 if phase == 0 else 1)


def test_report_holds_last_reference_not_deep_copy():
    from dataclasses import FrozenInstanceError

    value = []
    report = sample(lambda: value, repeats=1, clock=lambda: 0)
    value.append(1)
    assert report.last is value and report.last == [1]
    with pytest.raises(FrozenInstanceError):
        report.last = []
    assert isinstance(report, Measurement)


def test_actual_wall_and_cpu_clocks_have_no_speed_threshold():
    from time import process_time_ns

    for options in ({}, {"clock": process_time_ns}):
        report = sample(lambda: sum(range(32)), **options)
        assert report.last == 496 and len(report.elapsed_ns) == 3
        assert all(type(n) is int and n >= 0 for n in report.elapsed_ns)
