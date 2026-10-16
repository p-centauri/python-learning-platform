"""Real thread/process boundaries plus deterministic file and shutdown contracts."""
from dataclasses import FrozenInstanceError
import os
import multiprocessing
from pathlib import Path
from unittest.mock import patch
import pytest

from academy_bounded_offload import Job, Outcome, read_job, run_batch
from academy_bounded_offload import offload

@pytest.mark.parametrize("id,path,error", [
    (True, "/tmp/a", TypeError), ("ok", Path("/tmp/a"), TypeError),
    ("", "/tmp/a", ValueError), ("A", "/tmp/a", ValueError),
    ("a" * 33, "/tmp/a", ValueError), ("é", "/tmp/a", ValueError),
    ("a", "relative", ValueError), ("a", "", ValueError),
    ("a", "/" + "a" * 512, ValueError),
])
def test_job_validation(id, path, error):
    with pytest.raises(error):
        Job(id, path)

def test_frozen_job_and_outcome():
    job = Job("a", "/tmp/a")
    with pytest.raises(FrozenInstanceError):
        job.id = "b"
    outcome = Outcome("a", 0, 1, "worker", True)
    with pytest.raises(FrozenInstanceError):
        outcome.value = 1

@pytest.mark.parametrize("raw,value", [(b"0\n", 0), (b"5\n", 5), (b"60000\n", 60000)])
def test_canonical_worker_input(tmp_path, raw, value):
    path = tmp_path / "input"
    path.write_bytes(raw)
    outcome = read_job(Job("api", str(path)))
    assert outcome.id == "api" and outcome.value == value
    assert outcome.worker_pid == os.getpid() and outcome.file_closed

@pytest.mark.parametrize("raw", [
    b"", b"1", b"01\n", b"-1\n", b"+1\n", b" 1\n", b"1\r\n",
    b"1\n2\n", b"60001\n", b"99999\n", b"100000\n", b"1\n" + b"x" * 1000,
])
def test_invalid_bytes_close_on_failure(tmp_path, raw):
    path = tmp_path / "input"
    path.write_bytes(raw)
    opened = []
    original = Path.open
    def spy(self, *args, **kwargs):
        stream = original(self, *args, **kwargs)
        opened.append(stream)
        return stream
    with patch.object(Path, "open", spy), pytest.raises(ValueError):
        read_job(Job("api", str(path)))
    assert len(opened) == 1 and opened[0].closed

def test_worker_reads_only_seven_bytes(tmp_path):
    reads, closes = [], []
    class Stream:
        closed = False
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.closed = True
            closes.append(True)
        def read(self, size):
            reads.append(size)
            return b"1\n"
    with patch.object(Path, "open", return_value=Stream()):
        assert read_job(Job("a", str(tmp_path / "a"))).file_closed
    assert reads == [7] and closes == [True]

def test_missing_file_and_wrong_job(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_job(Job("a", str(tmp_path / "missing")))
    with pytest.raises(TypeError):
        read_job("not a job")

@pytest.mark.parametrize("mode", ["thread", "process"])
def test_actual_owned_pool_boundary_order_and_closed_files(tmp_path, mode):
    jobs = []
    for index, value in enumerate([5, 0, 60000]):
        path = tmp_path / str(index)
        path.write_bytes(str(value).encode() + b"\n")
        jobs.append(Job("a" + str(index), str(path)))
    outcomes = run_batch(jobs, mode=mode, workers=2, pending=2)
    assert [r.id for r in outcomes] == ["a0", "a1", "a2"]
    assert [r.value for r in outcomes] == [5, 0, 60000]
    assert all(r.file_closed for r in outcomes)
    if mode == "thread":
        assert all(r.worker_pid == os.getpid() for r in outcomes)
        assert all(r.worker_thread.startswith("academy-offload") for r in outcomes)
    else:
        assert all(r.worker_pid != os.getpid() for r in outcomes)
        assert not {r.worker_pid for r in outcomes} & {child.pid for child in multiprocessing.active_children()}

@pytest.mark.parametrize("mode", ["thread", "process"])
def test_real_pool_worker_failure_returns_no_partial_report(tmp_path, mode):
    good = tmp_path / "good"
    bad = tmp_path / "bad"
    good.write_bytes(b"1\n")
    bad.write_bytes(b"wrong\n")
    with pytest.raises(ValueError):
        run_batch([Job("good", str(good)), Job("bad", str(bad))], mode=mode)
    # Same exception identity is intentionally not promised across process serialization.

@pytest.mark.parametrize("setting,value,error", [
    ("workers", True, TypeError), ("workers", 0, ValueError), ("workers", 5, ValueError),
    ("mode", True, TypeError), ("mode", "green", ValueError),
    ("pending", 0, ValueError), ("limit", 17, ValueError),
])
def test_owner_validates_before_source_or_pool(setting, value, error):
    def source():
        raise AssertionError("source touched")
        yield
    with patch.object(offload, "ThreadPoolExecutor", side_effect=AssertionError("pool created"), create=True):
        with pytest.raises(error):
            run_batch(source(), **{setting: value})

@pytest.mark.parametrize("mode", ["thread", "process"])
@pytest.mark.parametrize("failure", [False, True])
def test_owner_shutdown_and_explicit_spawn(tmp_path, mode, failure):
    events = []
    class Owner:
        def shutdown(self, wait=True, *, cancel_futures=False):
            events.append(("shutdown", wait, cancel_futures))
    owner = Owner()
    error = LookupError("collect")
    def collector(*args, **kwargs):
        events.append(("collect", args[0] is owner, kwargs))
        if failure:
            raise error
        return ()
    factory = "ThreadPoolExecutor" if mode == "thread" else "ProcessPoolExecutor"
    with patch.object(offload, factory, return_value=owner, create=True) as created:
        with patch.object(offload, "collect_ordered", collector):
            if failure:
                with pytest.raises(LookupError) as caught:
                    run_batch([], mode=mode, workers=3, pending=4, limit=0)
                assert caught.value is error
            else:
                assert run_batch([], mode=mode, workers=3, pending=4, limit=0) == ()
    assert events == [
        ("collect", True, {"pending": 4, "limit": 0}),
        ("shutdown", True, True),
    ]
    assert created.call_args.kwargs["max_workers"] == 3
    if mode == "process":
        assert created.call_args.kwargs["mp_context"].get_start_method() == "spawn"

def test_real_owner_waits_for_running_work_after_failure(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event, Thread
    running, release, shutdown_entered, done = Event(), Event(), Event(), Event()
    errors = []
    error = LookupError("worker failed")
    class ObservedPool(ThreadPoolExecutor):
        def shutdown(self, wait=True, *, cancel_futures=False):
            shutdown_entered.set()
            super().shutdown(wait=wait, cancel_futures=cancel_futures)
    def worker(job):
        if job.id == "fail":
            assert running.wait(2), "test coordination deadline"
            raise error
        running.set()
        assert release.wait(2), "test coordination deadline"
        return Outcome(job.id, 1, os.getpid(), "worker", True)
    def owner():
        try:
            run_batch([Job("fail", str(tmp_path / "a")), Job("running", str(tmp_path / "b"))])
        except BaseException as caught:
            errors.append(caught)
        finally:
            done.set()
    with patch.object(offload, "ThreadPoolExecutor", ObservedPool, create=True):
        with patch.object(offload, "read_job", worker):
            thread = Thread(target=owner)
            thread.start()
            try:
                assert shutdown_entered.wait(2), "owner never reached shutdown"
                assert not done.is_set(), "owner returned while running work still held"
            finally:
                release.set()
                thread.join(timeout=3)
            assert not thread.is_alive() and done.is_set()
    assert errors == [error]
