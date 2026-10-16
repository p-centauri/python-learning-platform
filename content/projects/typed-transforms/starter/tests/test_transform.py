from dataclasses import FrozenInstanceError
import inspect
import pytest
from academy_typed_transforms import Row, decode_row, first, is_row_payload, map_rows, watch_call


@pytest.mark.parametrize("limit", [0, 1, 64])
def test_map_inclusive_capacity_and_fresh_results(limit):
    values = list(range(limit))
    a, b = map_rows(values, str, limit=limit), map_rows(values, str, limit=limit)
    assert a == b == tuple(str(value) for value in values)
    values.clear()
    assert len(a) == limit


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None])
def test_limit_type_before_acquisition(bad):
    class Unopened:
        def __iter__(self):
            pytest.fail("invalid options must not acquire input")

    with pytest.raises(TypeError):
        map_rows(Unopened(), str, limit=bad)


@pytest.mark.parametrize("bad", [-1, 65])
def test_limit_range_before_mapping(bad):
    with pytest.raises(ValueError):
        map_rows([], str, limit=bad)


def test_invalid_mapper_before_input_even_if_empty():
    class Unopened:
        def __iter__(self):
            pytest.fail("wrong mapper must fail before input")

    with pytest.raises(TypeError):
        map_rows(Unopened(), None)


@pytest.mark.parametrize("limit", [0, 2, 64])
def test_overflow_observes_one_extra_but_does_not_map_it(limit):
    pulled, mapped = [], []

    def rows():
        for value in range(1000):
            pulled.append(value)
            yield value

    def mapper(value):
        mapped.append(value)
        return str(value)

    borrowed = rows()
    with pytest.raises(ValueError, match="Too many"):
        map_rows(borrowed, mapper, limit=limit)
    assert len(pulled) == limit + 1 and len(mapped) == limit
    assert next(borrowed) == limit + 1
    borrowed.close()


def test_input_and_mapper_failure_identity_without_retry():
    error = OSError("private source details")

    def broken_input():
        yield 1
        raise error

    with pytest.raises(OSError) as failure:
        map_rows(broken_input(), str)
    assert failure.value is error
    calls = []

    def broken_map(value):
        calls.append(value)
        raise error

    with pytest.raises(OSError) as failure:
        map_rows([1, 2], broken_map)
    assert failure.value is error and calls == [1]


def test_borrowed_input_is_not_closed_and_values_are_not_deep_frozen():
    class Input:
        def __init__(self):
            self.closed = False

        def __iter__(self):
            return iter([1])

        def close(self):
            self.closed = True

    source = Input()
    value = []
    result = map_rows(source, lambda _: value)
    assert not source.closed and result[0] is value
    value.append(9)
    assert result == ([9],)


def test_wrapper_preserves_signature_metadata_argument_and_result_identity():
    events, calls = [], []

    def report(rows, /, *, prefix="x"):
        """Original documentation."""
        calls.append((rows, prefix))
        return rows

    report.custom = "marker"
    observed = watch_call(report, observer=events.append)
    values = [1]
    assert observed(values, prefix="y") is values
    assert calls == [(values, "y")] and events == ["started", "returned"]
    assert inspect.signature(observed) == inspect.signature(report)
    assert observed.__wrapped__ is report and observed.__name__ == "report"
    assert observed.__doc__ == report.__doc__ and observed.custom == "marker"


@pytest.mark.parametrize("error", [ValueError("secret"), KeyboardInterrupt(), SystemExit(2)])
def test_wrapper_error_identity_and_one_failure_event(error):
    events, calls = [], []

    def fail():
        calls.append(1)
        raise error

    observed = watch_call(fail, observer=events.append)
    with pytest.raises(type(error)) as result:
        observed()
    assert result.value is error and calls == [1]
    assert events == ["started", "raised"]


def test_wrapper_observers_are_independent_and_factory_has_no_events():
    a, b = [], []

    def read():
        return 3

    left, right = watch_call(read, observer=a.append), watch_call(read, observer=b.append)
    assert a == b == []
    assert left() == right() == 3
    assert a == b == ["started", "returned"]


@pytest.mark.parametrize("function,observer", [(None, lambda event: None), (lambda: 1, None)])
def test_wrapper_rejects_non_callable_configuration(function, observer):
    with pytest.raises(TypeError):
        watch_call(function, observer=observer)


@pytest.mark.parametrize("phase", ["started", "returned", "raised"])
def test_observer_failure_has_explicit_phase_behavior(phase):
    observer_error = RuntimeError("observer failed")
    target_error = ValueError("target failed")
    events, calls = [], []

    def observer(event):
        events.append(event)
        if event == phase:
            raise observer_error

    def target():
        calls.append(1)
        if phase == "raised":
            raise target_error
        return 4

    with pytest.raises(RuntimeError) as failure:
        watch_call(target, observer=observer)()
    assert failure.value is observer_error
    assert calls == ([] if phase == "started" else [1])
    assert events == (["started"] if phase == "started" else ["started", phase])
    if phase == "raised":
        assert failure.value.__context__ is target_error


def test_wrapper_observes_return_not_generator_completion():
    events = []

    def values():
        yield 1
        raise ValueError("later failure")

    rows = watch_call(values, observer=events.append)()
    assert events == ["started", "returned"]
    assert next(rows) == 1
    with pytest.raises(ValueError):
        next(rows)
    assert events == ["started", "returned"]


def test_first_preserves_value_or_default_identity():
    value, missing = object(), object()
    assert first([value]) is value
    assert first([]) is None and first([], default=missing) is missing
    assert first([value], default=missing) is value
    assert first([], default=0) == 0


def test_first_uses_length_and_one_index_without_iteration():
    class Input:
        def __len__(self):
            return 1

        def __getitem__(self, index):
            assert index == 0
            return "first"

        def __bool__(self):
            pytest.fail("truth override must not replace length")

        def __iter__(self):
            pytest.fail("first must not materialize input")

    assert first(Input()) == "first"


@pytest.mark.parametrize(
    "payload",
    [
        None,
        "{}",
        [],
        {},
        {"id": "a"},
        {"id": "a", "value": 1, "extra": 2},
        {"id": 1, "value": 2},
        {"id": "a", "value": True},
        {"id": "a", "value": 1.0},
    ],
)
def test_decode_rejects_shapes_without_coercion(payload):
    assert not is_row_payload(payload)
    with pytest.raises(TypeError):
        decode_row(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"id": "", "value": 1},
        {"id": "A", "value": 1},
        {"id": "a" * 33, "value": 1},
        {"id": "é", "value": 1},
        {"id": "a", "value": -1},
        {"id": "a", "value": 60001},
    ],
)
def test_guard_is_structural_and_decoder_checks_business_rules(payload):
    assert is_row_payload(payload)
    with pytest.raises(ValueError):
        decode_row(payload)


@pytest.mark.parametrize("value", [0, 60000])
def test_decode_copies_validated_values_and_is_frozen(value):
    payload = {"id": "api", "value": value}
    row = decode_row(payload)
    payload["id"] = "changed"
    assert row == Row("api", value)
    with pytest.raises(FrozenInstanceError):
        row.value = 8


def test_guard_does_not_make_mutable_payload_permanently_safe():
    payload = {"id": "api", "value": 1}
    assert is_row_payload(payload)
    payload["value"] = True
    with pytest.raises(TypeError):
        decode_row(payload)
