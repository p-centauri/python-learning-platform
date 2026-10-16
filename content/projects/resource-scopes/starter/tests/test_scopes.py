"""Public local behavior cases; no external services or learner API execution."""

import asyncio
from contextvars import copy_context
import gc
from typing import cast
import weakref
import pytest
from academy_resource_scopes import (
    AsyncResource,
    Resource,
    WeakRegistry,
    current_request,
    owned_async_resources,
    owned_resources,
    request_scope,
)


def run_async(function):
    async def bounded():
        # A test harness deadline catches broken fixtures/starters; it is not
        # a hard execution guarantee offered by the resource scope itself.
        async with asyncio.timeout(2):
            await function()

    asyncio.run(bounded())


class Box:
    def __init__(self, value: int = 5):
        self.value = value


def factory(events, name, *, fail=None):
    def acquire():
        events.append("open:" + name)
        if fail is not None:
            raise fail

        def close():
            events.append("close:" + name)

        return Resource(Box(), close)

    return acquire


def test_sync_order_identity_lifetime_and_fresh_instances():
    events = []
    first = factory(events, "a")
    second = factory(events, "b")
    for _ in range(2):
        with owned_resources([first, second]) as values:
            assert len(values) == 2 and isinstance(values, tuple)
            assert values[0] is not values[1]
            assert not any(e.startswith("close:") for e in events[-2:])
        assert events[-2:] == ["close:b", "close:a"]


def test_lazy_configuration_and_empty_scope():
    class Borrowed:
        def __iter__(self):
            raise AssertionError("acquired too early")

    scope = owned_resources(Borrowed(), limit=-1)
    with pytest.raises(ValueError):
        with scope:
            pass
    with owned_resources([], limit=0) as values:
        assert values == ()


@pytest.mark.parametrize(
    "limit,error", [(True, TypeError), (1.0, TypeError), (-1, ValueError), (9, ValueError)]
)
def test_sync_invalid_limit_before_iterating(limit, error):
    class Borrowed:
        def __iter__(self):
            raise AssertionError("input acquired")

    with pytest.raises(error):
        with owned_resources(Borrowed(), limit=limit):
            pass


@pytest.mark.parametrize("limit", [0, 1, 8])
def test_sync_bound_does_not_call_overflow_or_request_next(limit):
    events = []
    seen = []

    def factories():
        for i in range(limit + 2):
            seen.append(i)
            yield factory(events, str(i))
        raise AssertionError("too far")

    with pytest.raises(ValueError):
        with owned_resources(factories(), limit=limit):
            pytest.fail("body entered")
    assert seen == list(range(limit + 1))
    assert events == ["open:" + str(i) for i in range(limit)] + [
        "close:" + str(i) for i in reversed(range(limit))
    ]


def test_sync_partial_acquisition_failure_identity():
    events = []
    error = OSError("opening")
    with pytest.raises(OSError) as caught:
        with owned_resources([factory(events, "a"), factory(events, "b", fail=error), factory(events, "c")]):
            pytest.fail("body entered")
    assert caught.value is error
    assert events == ["open:a", "open:b", "close:a"]


@pytest.mark.parametrize("error", [ValueError("body"), KeyboardInterrupt("body")])
def test_sync_body_baseexception_identity(error):
    events = []
    with pytest.raises(type(error)) as caught:
        with owned_resources([factory(events, "a"), factory(events, "b")]):
            raise error
    assert caught.value is error and events[-2:] == ["close:b", "close:a"]


def test_sync_input_failure_and_borrowed_iterator_is_not_closed():
    events = []
    error = LookupError("input")

    class Borrowed:
        def __iter__(self):
            return self

        def __next__(self):
            if not events:
                return factory(events, "a")
            raise error

        def close(self):
            raise AssertionError("borrowed iterator closed")

    with pytest.raises(LookupError) as caught:
        with owned_resources(Borrowed()):
            pass
    assert caught.value is error and events == ["open:a", "close:a"]


@pytest.mark.parametrize("bad", [None, lambda: object()])
def test_sync_bad_factory_or_handoff_cleans_previous(bad):
    events = []
    with pytest.raises(TypeError):
        with owned_resources([factory(events, "a"), bad]):
            pass
    assert events == ["open:a", "close:a"]


def test_cleanup_failure_attempts_remaining_and_preserves_chain():
    events = []
    body = ValueError("body")
    inner = OSError("inner")
    outer = RuntimeError("outer")

    def acquire(name, error):
        def close():
            events.append(name)
            raise error

        return Resource(name, close)

    with pytest.raises(RuntimeError) as caught:
        with owned_resources([lambda: acquire("outer", outer), lambda: acquire("inner", inner)]):
            raise body
    assert events == ["inner", "outer"]
    assert caught.value is outer
    assert outer.__context__ is inner and inner.__context__ is body


def test_callback_truthy_return_cannot_suppress_body():
    error = ValueError("body")
    close = cast(object, lambda: True)
    with pytest.raises(ValueError) as caught:
        with owned_resources([lambda: Resource("a", close)]):
            raise error
    assert caught.value is error


@pytest.mark.parametrize("constructor", [Resource, AsyncResource])
def test_handoff_rejects_noncallable_cleanup(constructor):
    with pytest.raises(TypeError):
        constructor("a", None)


def async_factory(events, name, *, fail=None, close_fail=None):
    async def acquire():
        events.append("open:" + name)
        await asyncio.sleep(0)
        if fail is not None:
            raise fail

        async def close():
            events.append("closing:" + name)
            await asyncio.sleep(0)
            events.append("closed:" + name)
            if close_fail is not None:
                raise close_fail

        return AsyncResource(Box(), close)

    return acquire


def test_async_normal_lifo_and_awaited_cleanup():
    async def run():
        events = []
        async with owned_async_resources([async_factory(events, "a"), async_factory(events, "b")]) as values:
            assert len(values) == 2 and values[0] is not values[1]
            assert events == ["open:a", "open:b"]
        assert events == ["open:a", "open:b", "closing:b", "closed:b", "closing:a", "closed:a"]
        async with owned_async_resources([], limit=0) as values:
            assert values == ()

    run_async(run)


@pytest.mark.parametrize("limit,error", [(False, TypeError), (-1, ValueError), (9, ValueError)])
def test_async_invalid_limit_before_input(limit, error):
    async def run():
        class Borrowed:
            def __iter__(self):
                raise AssertionError("input acquired")

        with pytest.raises(error):
            async with owned_async_resources(Borrowed(), limit=limit):
                pass

    run_async(run)


@pytest.mark.parametrize("limit", [0, 1, 8])
def test_async_partial_failure_overflow_and_borrowed_input(limit):
    async def run():
        events = []
        error = OSError("open")
        with pytest.raises(OSError) as caught:
            async with owned_async_resources(
                [async_factory(events, "a"), async_factory(events, "b", fail=error)]
            ):
                pytest.fail("body entered")
        assert caught.value is error
        assert events == ["open:a", "open:b", "closing:a", "closed:a"]
        events.clear()
        seen = []

        def factories():
            for i in range(limit + 2):
                seen.append(i)
                yield async_factory(events, str(i))

        with pytest.raises(ValueError):
            async with owned_async_resources(factories(), limit=limit):
                pass
        assert seen == list(range(limit + 1))
        assert events == ["open:" + str(i) for i in range(limit)] + [
            event for i in reversed(range(limit)) for event in ("closing:" + str(i), "closed:" + str(i))
        ]

    run_async(run)


def test_async_body_cancellation_finishes_cooperative_cleanup():
    async def run():
        events = []
        entered = asyncio.Event()
        wait = asyncio.Event()

        async def worker():
            with request_scope("worker"):
                async with owned_async_resources([async_factory(events, "a"), async_factory(events, "b")]):
                    entered.set()
                    await wait.wait()

        task = asyncio.create_task(worker())
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert task.cancelled()
        assert events[-4:] == ["closing:b", "closed:b", "closing:a", "closed:a"]
        assert current_request() is None

    run_async(run)


def test_async_cancellation_during_next_factory_closes_prior_handoff():
    async def run():
        events = []
        entered = asyncio.Event()

        async def blocked():
            entered.set()
            await asyncio.Event().wait()
            return AsyncResource(Box(), lambda: asyncio.sleep(0))

        async def worker():
            async with owned_async_resources([async_factory(events, "a"), blocked]):
                pytest.fail("body entered")

        task = asyncio.create_task(worker())
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert events == ["open:a", "closing:a", "closed:a"]

    run_async(run)


def test_async_cleanup_failure_attempts_remaining_and_preserves_body():
    async def run():
        events = []
        body = ValueError("body")
        cleanup = OSError("cleanup")
        with pytest.raises(OSError) as caught:
            async with owned_async_resources(
                [async_factory(events, "a"), async_factory(events, "b", close_fail=cleanup)]
            ):
                raise body
        assert caught.value is cleanup and cleanup.__context__ is body
        assert events[-4:] == ["closing:b", "closed:b", "closing:a", "closed:a"]

    run_async(run)


@pytest.mark.parametrize("bad", [None, lambda: asyncio.sleep(0, result=object())])
def test_async_bad_factory_or_handoff_cleans_prior(bad):
    async def run():
        events = []
        with pytest.raises(TypeError):
            async with owned_async_resources([async_factory(events, "a"), bad]):
                pass
        assert events == ["open:a", "closing:a", "closed:a"]

    run_async(run)


def test_context_nested_restoration_exception_and_reuse_factory():
    assert current_request() is None
    with request_scope("outer"):
        for _ in range(2):
            with pytest.raises(ValueError):
                with request_scope("inner"):
                    assert current_request() == "inner"
                    raise ValueError("body")
            assert current_request() == "outer"
    assert current_request() is None


@pytest.mark.parametrize(
    "label,error",
    [(True, TypeError), ("", ValueError), ("A", ValueError), ("a" * 33, ValueError), ("é", ValueError)],
)
def test_context_invalid_label_preserves_parent(label, error):
    with request_scope("parent"):
        with pytest.raises(error):
            with request_scope(label):
                pass
        assert current_request() == "parent"


def test_context_task_snapshot_isolated_and_copy_context_restores():
    async def run():
        gate = asyncio.Event()

        async def child():
            await gate.wait()
            assert current_request() == "parent"
            with request_scope("child"):
                await asyncio.sleep(0)
                assert current_request() == "child"
            return current_request()

        with request_scope("parent"):
            task = asyncio.create_task(child())
            with request_scope("later"):
                gate.set()
                assert await task == "parent"
                assert current_request() == "later"
            context = copy_context()
        assert current_request() is None
        assert context.run(current_request) == "parent"
        assert current_request() is None

    run_async(run)


def test_weak_registry_identity_replacement_and_temporary_strong_lookup():
    registry = WeakRegistry[Box]()
    a, b = Box(1), Box(2)
    registry.store("item", a)
    assert registry.get("item") is a
    registry.store("item", b)
    assert registry.get("item") is b
    assert registry.get("missing") is None
    held = registry.get("item")
    reference = weakref.ref(b)
    del b
    gc.collect()
    assert reference() is held
    del held
    gc.collect()
    assert reference() is None and registry.get("item") is None and len(registry) == 0
    assert a.value == 1


def test_weak_registry_does_not_own_lifetime_or_run_cleanup():
    registry = WeakRegistry[Box]()
    events = []

    class Handle(Box):
        def close(self):
            events.append("closed")

    handle = Handle()
    reference = weakref.ref(handle)
    registry.store("item", handle)
    del handle
    gc.collect()
    assert reference() is None and registry.get("item") is None
    assert events == []


@pytest.mark.parametrize(
    "key,error", [(True, TypeError), ("", ValueError), ("bad key", ValueError), ("a" * 33, ValueError)]
)
def test_weak_registry_invalid_key_preserves_entry(key, error):
    registry = WeakRegistry[Box]()
    value = Box()
    registry.store("item", value)
    with pytest.raises(error):
        registry.store(key, value)
    with pytest.raises(error):
        registry.get(key)
    assert registry.get("item") is value and len(registry) == 1


def test_weak_registry_nonweakable_replacement_preserves_existing():
    registry = WeakRegistry[object]()
    value = Box()
    registry.store("item", value)
    with pytest.raises(TypeError):
        registry.store("item", 42)
    assert registry.get("item") is value


def test_context_label_visible_in_cleanup_before_scope_restores():
    labels = []
    with request_scope("request"):
        with owned_resources([lambda: Resource("a", lambda: labels.append(current_request()))]):
            assert current_request() == "request"
    assert labels == ["request"] and current_request() is None


def test_async_input_failure_and_borrowed_iterator_not_closed():
    async def run():
        events = []
        error = LookupError("input")

        class Borrowed:
            def __iter__(self):
                return self

            def __next__(self):
                if not events:
                    return async_factory(events, "a")
                raise error

            def close(self):
                raise AssertionError("borrowed input closed")

        with pytest.raises(LookupError) as caught:
            async with owned_async_resources(Borrowed()):
                pass
        assert caught.value is error
        assert events == ["open:a", "closing:a", "closed:a"]

    run_async(run)


def test_async_body_exception_identity_and_context_restoration():
    async def run():
        events = []
        error = ValueError("body")
        with pytest.raises(ValueError) as caught:
            with request_scope("request"):
                async with owned_async_resources([async_factory(events, "a")]):
                    raise error
        assert caught.value is error and current_request() is None
        assert events == ["open:a", "closing:a", "closed:a"]

    run_async(run)


def test_async_scope_creation_is_lazy_and_each_scope_is_one_use():
    async def run():
        events = []
        scope = owned_async_resources([async_factory(events, "a")])
        assert events == []
        async with scope:
            assert events == ["open:a"]
        with pytest.raises((AttributeError, RuntimeError)):
            async with scope:
                pass
        assert events == ["open:a", "closing:a", "closed:a"]

    run_async(run)


def test_weak_registry_does_not_retain_collectible_cycles():
    registry = WeakRegistry[Box]()
    value = Box()
    value.peer = value
    reference = weakref.ref(value)
    registry.store("cycle", value)
    del value
    gc.collect()
    assert reference() is None and registry.get("cycle") is None


def test_failed_factory_owns_partial_work_before_handoff():
    events = []
    error = OSError("partial setup")

    def partial():
        events.append("allocate:partial")
        try:
            raise error
        finally:
            events.append("release:partial")

    with pytest.raises(OSError) as caught:
        with owned_resources([factory(events, "a"), partial]):
            pytest.fail("body entered")
    assert caught.value is error
    assert events == ["open:a", "allocate:partial", "release:partial", "close:a"]


def test_cancelled_factory_owns_partial_work_before_async_handoff():
    async def run():
        events = []
        allocated = asyncio.Event()

        async def partial():
            events.append("allocate:partial")
            allocated.set()
            try:
                await asyncio.Event().wait()
            finally:
                await asyncio.sleep(0)
                events.append("release:partial")
            raise AssertionError("unreachable")

        async def worker():
            async with owned_async_resources([async_factory(events, "a"), partial]):
                pytest.fail("body entered")

        task = asyncio.create_task(worker())
        await allocated.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert events == ["open:a", "allocate:partial", "release:partial", "closing:a", "closed:a"]

    run_async(run)


@pytest.mark.parametrize("label", ["a", "a" * 32])
def test_exact_label_boundaries_for_context_and_weak_lookup(label):
    registry = WeakRegistry[Box]()
    value = Box()
    with request_scope(label):
        assert current_request() == label
        registry.store(label, value)
        assert registry.get(label) is value
    assert current_request() is None
