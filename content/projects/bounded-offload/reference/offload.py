"""Trusted maintained solution; excluded from learner downloads."""
from collections import deque
from collections.abc import Callable, Iterable
from concurrent.futures import Executor, Future, ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing
import os
from pathlib import Path
import re
import threading
from typing import Literal, TypeVar

from .contracts import Job, Outcome, bounded_integer, validate_settings

T = TypeVar("T")
R = TypeVar("R")

def collect_ordered(
    executor: Executor, rows: Iterable[T], function: Callable[[T], R], /, *,
    pending: int = 2, limit: int = 16,
) -> tuple[R, ...]:
    validate_settings(pending, limit)
    iterator = iter(rows)
    window: deque[Future[R]] = deque()
    results: list[R] = []
    admitted = 0
    exhausted = False

    def fill() -> None:
        nonlocal admitted, exhausted
        while len(window) < pending and not exhausted:
            try:
                row = next(iterator)
            except StopIteration:
                exhausted = True
                break
            if admitted == limit:
                raise ValueError("Job limit exceeded")
            window.append(executor.submit(function, row))
            admitted += 1

    try:
        fill()
        while window:
            # Retire only after result succeeds. Failure still leaves it tracked.
            result = window[0].result()
            window.popleft()
            results.append(result)
            fill()
        return tuple(results)
    except BaseException:
        for future in window:
            future.cancel()
        raise

def read_job(job: Job) -> Outcome:
    if type(job) is not Job:
        raise TypeError("Expected Job")
    with Path(job.path).open("rb") as stream:
        raw = stream.read(7)
        if re.fullmatch(rb"(0|[1-9][0-9]{0,4})\n", raw) is None:
            raise ValueError("Expected canonical bounded decimal line")
        value = int(raw)
        if value > 60000:
            raise ValueError("Value exceeds bound")
    return Outcome(job.id, value, os.getpid(), threading.current_thread().name, stream.closed)

def run_batch(
    jobs: Iterable[Job], /, *, mode: Literal["thread", "process"] = "thread",
    workers: int = 2, pending: int = 2, limit: int = 16,
) -> tuple[Outcome, ...]:
    validate_settings(pending, limit)
    bounded_integer(workers, 1, 4, "workers")
    if type(mode) is not str:
        raise TypeError("Expected exact mode")
    if mode not in ("thread", "process"):
        raise ValueError("Expected thread or process mode")
    executor: Executor
    if mode == "thread":
        executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="academy-offload")
    else:
        executor = ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn"))
    try:
        return collect_ordered(executor, jobs, read_job, pending=pending, limit=limit)
    finally:
        executor.shutdown(wait=True, cancel_futures=True)
