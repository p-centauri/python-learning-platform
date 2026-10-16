"""Finite public cases. Test coordination deadlines do not give the API a deadline."""
from concurrent.futures import Executor, Future, ThreadPoolExecutor, TimeoutError
from threading import Event
import pytest
from academy_bounded_offload import collect_ordered

class TrackedFuture(Future):
    def __init__(self, pool):
        super().__init__()
        self.pool = pool
        self.cancel_calls = 0
    def result(self, timeout=None):
        self.pool.events.append("result")
        value = super().result(timeout)
        self.pool.outstanding -= 1
        return value
    def cancel(self):
        self.cancel_calls += 1
        return super().cancel()

class Pool(Executor):
    def __init__(self, *, fail_submit=None, futures=None):
        self.calls = []
        self.events = []
        self.outstanding = 0
        self.peak = 0
        self.shutdown_called = False
        self.fail_submit = fail_submit
        self.futures = futures or []
        self.returned = []
    def submit(self, fn, /, *args, **kwargs):
        self.events.append("submit")
        if len(self.calls) == self.fail_submit:
            raise OSError("submit failed")
        self.calls.append(args[0])
        self.outstanding += 1
        self.peak = max(self.peak, self.outstanding)
        if self.futures:
            future = self.futures.pop(0)
        else:
            future = TrackedFuture(self)
            try:
                future.set_result(fn(*args, **kwargs))
            except BaseException as error:
                future.set_exception(error)
        self.returned.append(future)
        return future
    def shutdown(self, wait=True, *, cancel_futures=False):
        self.shutdown_called = True

class Source:
    def __init__(self, values):
        self.values = iter(values)
        self.reads = 0
        self.closed = False
        self.iterations = 0
    def __iter__(self):
        self.iterations += 1
        return self
    def __next__(self):
        value = next(self.values)
        self.reads += 1
        return value
    def close(self):
        self.closed = True

@pytest.mark.parametrize("pending", [1, 2, 4])
def test_window_and_order(pending):
    pool = Pool()
    source = Source(range(16))
    result = collect_ordered(pool, source, lambda n: n * 2, pending=pending)
    assert result == tuple(n * 2 for n in range(16))
    assert pool.peak == pending
    assert pool.events[:pending] == ["submit"] * pending
    assert source.reads == 16 and source.iterations == 1 and not source.closed
    assert not pool.shutdown_called

@pytest.mark.parametrize("setting,value,error", [
    ("pending", True, TypeError), ("pending", 1.0, TypeError),
    ("pending", 0, ValueError), ("pending", 5, ValueError),
    ("limit", True, TypeError), ("limit", "2", TypeError),
    ("limit", -1, ValueError), ("limit", 17, ValueError),
])
def test_configuration_before_iteration(setting, value, error):
    pool = Pool()
    source = Source([1])
    with pytest.raises(error):
        collect_ordered(pool, source, abs, **{setting: value})
    assert source.iterations == 0 and not pool.calls and not pool.shutdown_called

@pytest.mark.parametrize("limit", [0, 1, 16])
def test_one_extra_observed_never_submitted(limit):
    source = Source(range(100))
    pool = Pool()
    with pytest.raises(ValueError, match="limit"):
        collect_ordered(pool, source, abs, pending=1, limit=limit)
    assert source.reads == limit + 1 and len(pool.calls) == limit
    assert not source.closed and not pool.shutdown_called

def test_empty_zero_limit():
    pool = Pool()
    assert collect_ordered(pool, [], abs, limit=0) == ()
    assert not pool.calls and not pool.shutdown_called

def test_input_failure_cancels_tracked_queued_future():
    pool = Pool()
    queued = TrackedFuture(pool)
    pool.futures = [queued]
    error = RuntimeError("input")
    def rows():
        yield 1
        raise error
    with pytest.raises(RuntimeError) as caught:
        collect_ordered(pool, rows(), abs)
    assert caught.value is error and queued.cancelled() and queued.cancel_calls == 1
    assert not pool.shutdown_called

def test_submit_failure_cancels_existing_not_unsubmitted():
    pool = Pool(fail_submit=1)
    queued = TrackedFuture(pool)
    pool.futures = [queued]
    with pytest.raises(OSError, match="submit"):
        collect_ordered(pool, [1, 2, 3], abs)
    assert pool.calls == [1] and queued.cancelled() and not pool.shutdown_called

def test_worker_failure_keeps_original_and_cancels_queued():
    pool = Pool()
    failed, queued = TrackedFuture(pool), TrackedFuture(pool)
    error = LookupError("worker")
    failed.set_exception(error)
    pool.futures = [failed, queued]
    with pytest.raises(LookupError) as caught:
        collect_ordered(pool, [1, 2, 3], abs)
    assert caught.value is error and queued.cancelled()
    assert pool.calls == [1, 2] and not pool.shutdown_called

def test_running_future_cannot_be_stopped_by_cancel():
    pool = Pool()
    running, failed = TrackedFuture(pool), TrackedFuture(pool)
    running.set_running_or_notify_cancel()
    failed.set_exception(ValueError("worker"))
    pool.futures = [failed, running]
    with pytest.raises(ValueError):
        collect_ordered(pool, [1, 2], abs)
    assert running.cancel_calls == 1 and not running.cancelled() and not running.done()
    running.set_result(2)  # The owner must arrange actual completion.
    assert running.result() == 2

def test_ordered_observation_not_completion_order():
    pool = Pool()
    one, two = TrackedFuture(pool), TrackedFuture(pool)
    two.set_result("second")
    one.set_result("first")
    pool.futures = [one, two]
    assert collect_ordered(pool, [1, 2], str) == ("first", "second")

def test_borrowed_pool_remains_usable_after_failure():
    with ThreadPoolExecutor(max_workers=1) as pool:
        def fail(n):
            raise ValueError("failed")
        with pytest.raises(ValueError):
            collect_ordered(pool, [1], fail)
        assert pool.submit(abs, -3).result(timeout=2) == 3

def test_real_running_thread_timeout_is_only_waiting():
    started, release, finished = Event(), Event(), Event()
    def work():
        started.set()
        try:
            assert release.wait(2), "test coordination deadline"
            return 7
        finally:
            finished.set()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(work)
        try:
            assert started.wait(2), "test coordination deadline"
            assert future.cancel() is False
            with pytest.raises(TimeoutError):
                future.result(timeout=0.001)
            assert not finished.is_set()
        finally:
            release.set()
        assert future.result(timeout=2) == 7
    assert finished.is_set()

def test_failure_does_not_close_borrowed_generator():
    closed = []
    def rows():
        try:
            yield 1
            yield 2
        finally:
            closed.append(True)
    source = rows()
    pool = Pool()
    with pytest.raises(ValueError):
        collect_ordered(pool, source, abs, limit=0)
    assert not closed
    source.close()
    assert closed == [True]
