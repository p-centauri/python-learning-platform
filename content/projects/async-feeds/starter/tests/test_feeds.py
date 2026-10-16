import asyncio
from collections.abc import Sequence
from contextlib import aclosing, asynccontextmanager

import httpx
import pytest

from academy_async_feeds import (
    ConfigError,
    FeedError,
    Record,
    RecordError,
    Source,
    ingest,
    iter_records,
    open_feed,
)
import academy_async_feeds.worker as worker

GOOD = b'{"id":"api","value":10}'


async def chunks(parts):
    for part in parts:
        yield part


async def collect(parts):
    async with aclosing(iter_records(chunks(parts))) as records:
        return [record async for record in records]


@pytest.mark.parametrize(
    "parts,expected",
    [
        ([], []),
        ([b""], []),
        ([GOOD], [Record("api", 10)]),
        ([GOOD + b"\n"], [Record("api", 10)]),
        ([GOOD + b"\r\n"], [Record("api", 10)]),
        ([bytes([byte]) for byte in GOOD + b"\n"], [Record("api", 10)]),
        ([GOOD + b"\n" + GOOD], [Record("api", 10), Record("api", 10)]),
        ([b'{"id":"a","value":0}\n{"id":"b","value":60000}'], [Record("a", 0), Record("b", 60000)]),
        ([GOOD + b" " * (1024 - len(GOOD)) + b"\n"], [Record("api", 10)]),
    ],
)
def test_parser_framing_and_inclusive_bounds(parts, expected, run_async):
    assert run_async(collect(parts)) == expected


@pytest.mark.parametrize(
    "raw",
    [
        b"\n",
        b"{}",
        b"[]",
        b'{"id":"Api","value":1}',
        b'{"id":"a","value":true}',
        b'{"id":"a","value":1.0}',
        b'{"id":"a","value":-1}',
        b'{"id":"a","value":60001}',
        b'{"id":"a","value":1,"extra":0}',
        b'{"id":1,"value":1}',
        b"\xff",
        b"not-json",
        GOOD + b" " * (1025 - len(GOOD)),
    ],
)
def test_parser_rejects_strict_shape_and_long_lines(raw, run_async):
    with pytest.raises(RecordError, match="line 1"):
        run_async(collect([raw]))


def test_late_parser_error_keeps_line_and_cause(run_async):
    async def scenario():
        async with aclosing(iter_records(chunks([GOOD + b"\n?\n"]))) as records:
            assert await anext(records) == Record("api", 10)
            with pytest.raises(RecordError, match="line 2") as error:
                await anext(records)
            assert isinstance(error.value.__cause__, ValueError)

    run_async(scenario())


def test_parser_is_lazy_and_borrows_input(run_async):
    class Borrowed:
        reads = 0
        closed = False

        def __aiter__(self):
            return self

        async def __anext__(self):
            self.reads += 1
            if self.reads == 1:
                return GOOD + b"\n" + GOOD + b"\n"
            raise StopAsyncIteration

        async def aclose(self):
            self.closed = True

    async def scenario():
        source = Borrowed()
        records = iter_records(source)
        assert source.reads == 0
        assert await anext(records) == Record("api", 10)
        assert source.reads == 1
        await records.aclose()
        assert not source.closed and source.reads == 1

    run_async(scenario())


@pytest.mark.parametrize("bad", ["text", bytearray(GOOD), None])
def test_parser_requires_bytes(bad, run_async):
    with pytest.raises(RecordError):
        run_async(collect([bad]))


class Stream(httpx.AsyncByteStream):
    def __init__(self, parts, failure=None, entered=None, release=None):
        self.parts = parts
        self.failure = failure
        self.entered = entered
        self.release = release
        self.closed = False

    async def __aiter__(self):
        for part in self.parts:
            yield part
        if self.entered is not None:
            self.entered.set()
            await self.release.wait()
        if self.failure is not None:
            raise self.failure

    async def aclose(self):
        self.closed = True


def test_http_stream_cleanup_and_borrowed_client_reuse(sources, run_async):
    async def scenario():
        streams = []
        requests = []

        def respond(request):
            requests.append(request)
            stream = Stream([GOOD + b"\n" + GOOD + b"\n"])
            streams.append(stream)
            return httpx.Response(
                200, headers={"Content-Type": "application/x-ndjson; charset=utf-8"}, stream=stream
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            async with open_feed(sources[0], client=client) as rows:
                assert await anext(rows) == Record("api", 10)
            assert streams[0].closed and not client.is_closed
            async with open_feed(sources[1], client=client) as rows:
                assert len([row async for row in rows]) == 2
            assert all(stream.closed for stream in streams) and not client.is_closed
        assert [request.method for request in requests] == ["GET", "GET"]

    run_async(scenario())


@pytest.mark.parametrize(
    "status,headers",
    [
        (302, {"Location": "https://example.test/other"}),
        (503, {}),
        (200, {"Content-Type": "application/json"}),
        (200, {"Content-Type": "application/x-ndjson", "Content-Encoding": "gzip"}),
    ],
)
def test_http_policy_rejects_without_redirects(status, headers, sources, run_async):
    async def scenario():
        stream = Stream([GOOD])
        calls = []

        def respond(request):
            calls.append(request)
            return httpx.Response(status, headers=headers, stream=stream)

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond), follow_redirects=True) as client:
            with pytest.raises(FeedError):
                async with open_feed(sources[0], client=client):
                    pytest.fail("invalid response accepted")
            assert stream.closed and not client.is_closed and len(calls) == 1

    run_async(scenario())


@pytest.mark.parametrize("limit,valid", [(len(GOOD), True), (len(GOOD) - 1, False)])
def test_http_counts_actual_bytes_not_content_length(limit, valid, sources, run_async):
    async def scenario():
        stream = Stream([GOOD])

        def respond(request):
            return httpx.Response(
                200, headers={"Content-Type": "application/x-ndjson", "Content-Length": "1"}, stream=stream
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:

            async def read():
                async with open_feed(sources[0], client=client, max_bytes=limit) as rows:
                    return [row async for row in rows]

            if valid:
                assert await read() == [Record("api", 10)]
            else:
                with pytest.raises(FeedError, match="body byte limit"):
                    await read()
            assert stream.closed and not client.is_closed

    run_async(scenario())


@pytest.mark.parametrize("limit", [0, 8193, True, 1.0])
def test_http_limit_validation_before_request(limit, sources, run_async):
    async def scenario():
        def forbidden(request):
            pytest.fail("invalid limit reached transport")

        async with httpx.AsyncClient(transport=httpx.MockTransport(forbidden)) as client:
            with pytest.raises(FeedError):
                async with open_feed(sources[0], client=client, max_bytes=limit):
                    pass

    run_async(scenario())


@pytest.mark.parametrize("during_read", [False, True])
def test_http_error_preserves_cause_and_closes(during_read, sources, run_async):
    async def scenario():
        failure = httpx.ReadTimeout("SECRET upstream body")
        stream = Stream([], failure=failure)
        calls = []

        def respond(request):
            calls.append(request)
            if not during_read:
                raise failure
            return httpx.Response(200, headers={"Content-Type": "application/x-ndjson"}, stream=stream)

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            with pytest.raises(FeedError) as caught:
                async with open_feed(sources[0], client=client) as rows:
                    _ = [row async for row in rows]
            assert caught.value.__cause__ is failure and "SECRET" not in str(caught.value)
            assert not client.is_closed and len(calls) == 1
            if during_read:
                assert stream.closed

    run_async(scenario())


def test_http_caller_exception_identity_and_owned_cleanup(sources, run_async):
    async def scenario():
        failure = httpx.ReadTimeout("caller-owned error")
        stream = Stream([GOOD])

        def respond(request):
            return httpx.Response(200, headers={"Content-Type": "application/x-ndjson"}, stream=stream)

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            with pytest.raises(httpx.ReadTimeout) as caught:
                async with open_feed(sources[0], client=client):
                    raise failure
            assert caught.value is failure and stream.closed and not client.is_closed

    run_async(scenario())


def test_http_cancel_during_read_closes_before_propagating(sources, run_async):
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        stream = Stream([], entered=entered, release=release)

        def respond(request):
            return httpx.Response(200, headers={"Content-Type": "application/x-ndjson"}, stream=stream)

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:

            async def read():
                async with open_feed(sources[0], client=client) as rows:
                    _ = [row async for row in rows]

            task = asyncio.create_task(read())
            await entered.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert stream.closed and not client.is_closed

    run_async(scenario())


@pytest.mark.parametrize(
    "options",
    [
        {"workers": 0},
        {"workers": 5},
        {"workers": True},
        {"queue_size": 0},
        {"queue_size": 17},
        {"queue_size": True},
        {"timeout": 0},
        {"timeout": -1},
        {"timeout": 31},
        {"timeout": float("nan")},
        {"timeout": float("inf")},
        {"timeout": True},
    ],
)
def test_job_options_rejected_before_opening(options, sources, run_async):
    @asynccontextmanager
    async def forbidden(source):
        pytest.fail("invalid settings opened source")
        yield

    with pytest.raises(ConfigError):
        run_async(ingest(sources, opener=forbidden, **options))


@pytest.mark.parametrize(
    "sources",
    [
        [Source("Bad", "https://example.test")],
        [Source("a", "http://example.test")],
        [Source("a", "https://user:secret@example.test")],
        [Source("a", "https://example.test#part")],
        [Source("a", "https://example.test:8443")],
        [Source("a", "https://example.test/ space")],
        [Source("a", "https://example.test"), Source("a", "https://example.test/other")],
        [Source(f"a{i}", "https://example.test") for i in range(17)],
        [None],
        None,
    ],
)
def test_invalid_sources_rejected_without_io(sources, run_async):
    @asynccontextmanager
    async def forbidden(source):
        pytest.fail("invalid source reached opener")
        yield

    with pytest.raises(ConfigError):
        run_async(ingest(sources, opener=forbidden))


@pytest.mark.parametrize("options", [{}, {"workers": 4, "queue_size": 16, "timeout": 30}])
def test_empty_job_and_fresh_totals(sources, run_async, options):
    async def scenario():
        closed = []

        @asynccontextmanager
        async def configured(source):
            try:
                yield records(source)
            finally:
                closed.append(source.label)

        async def records(source):
            yield Record(source.label, 10)
            yield Record(source.label, 20)

        assert await ingest([], opener=configured, **options) == {"sources": 0, "count": 0, "total": 0}
        assert closed == []
        for _ in range(2):
            assert await ingest(sources, opener=configured, **options) == {
                "sources": 2,
                "count": 4,
                "total": 60,
            }
        assert sorted(closed) == ["feed-a", "feed-a", "feed-b", "feed-b"]

    run_async(scenario())


def test_worker_and_queue_bounds_with_backpressure(monkeypatch, run_async):
    real_queue = asyncio.Queue
    queues = []

    class ObservedQueue(real_queue):
        peak = 0
        blocked_puts = 0

        async def put(self, item):
            if self.full():
                self.blocked_puts += 1
            await super().put(item)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            queues.append(self)

        def put_nowait(self, item):
            super().put_nowait(item)
            self.peak = max(self.peak, self.qsize())

    monkeypatch.setattr(worker.asyncio, "Queue", ObservedQueue)

    async def scenario():
        active = peak = 0
        entered, release = asyncio.Event(), asyncio.Event()
        baseline = set(asyncio.all_tasks())

        @asynccontextmanager
        async def configured(source):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            if active == 2:
                entered.set()
            try:
                await release.wait()
                yield records()
            finally:
                active -= 1

        async def records():
            yield Record("api", 1)

        job = asyncio.create_task(
            ingest(
                [Source(f"a{i}", "https://example.test") for i in range(16)],
                opener=configured,
                workers=2,
                queue_size=1,
            )
        )
        await entered.wait()
        assert peak == 2 and queues[0].maxsize == 1
        # job + one producer + two workers, independent of the sixteen sources.
        assert len(set(asyncio.all_tasks()) - baseline) <= 4
        release.set()
        assert await job == {"sources": 16, "count": 16, "total": 16}
        assert active == 0 and queues[0].peak == 1 and queues[0].blocked_puts > 0
        await asyncio.wait_for(queues[0].join(), timeout=0.2)
        assert not (set(asyncio.all_tasks()) - baseline)

    run_async(scenario())


def test_worker_failure_cancels_sibling_and_preserves_group(sources, run_async):
    async def scenario():
        entered = asyncio.Event()
        never = asyncio.Event()
        closed = []
        failure = RecordError("late bad record")
        baseline = set(asyncio.all_tasks())

        @asynccontextmanager
        async def configured(source):
            try:
                yield records(source)
            finally:
                closed.append(source.label)

        async def records(source):
            if source.label == "feed-a":
                yield Record("api", 10)
                await entered.wait()
                raise failure
            entered.set()
            await never.wait()
            yield Record("worker", 20)

        with pytest.raises(ExceptionGroup) as caught:
            await ingest(sources, opener=configured)
        assert failure in caught.value.exceptions
        assert sorted(closed) == ["feed-a", "feed-b"]
        assert not (set(asyncio.all_tasks()) - baseline)

    run_async(scenario())


def test_caller_cancellation_waits_for_owned_cleanup(sources, run_async):
    async def scenario():
        entered, never = asyncio.Event(), asyncio.Event()
        closed = []
        baseline = set(asyncio.all_tasks())

        @asynccontextmanager
        async def configured(source):
            try:
                entered.set()
                await never.wait()
                yield chunks([])
            finally:
                closed.append(source.label)

        job = asyncio.create_task(ingest(sources, opener=configured, workers=1, queue_size=1))
        await entered.wait()
        job.cancel()
        with pytest.raises(asyncio.CancelledError):
            await job
        assert closed == ["feed-a"]
        assert not (set(asyncio.all_tasks()) - baseline)

    run_async(scenario())


def test_total_deadline_includes_opening_and_cleanup(sources, run_async):
    async def scenario():
        closed = []
        never = asyncio.Event()

        @asynccontextmanager
        async def configured(source):
            try:
                await never.wait()
                yield chunks([])
            finally:
                closed.append(source.label)

        with pytest.raises(TimeoutError):
            await ingest(sources[:1], opener=configured, timeout=0.01)
        assert closed == ["feed-a"]

    run_async(scenario())


def test_cleanup_failure_cannot_publish_success(sources, run_async):
    async def scenario():
        failure = RuntimeError("cleanup failed")

        async def records():
            yield Record("api", 1)

        @asynccontextmanager
        async def configured(source):
            yield records()
            raise failure

        with pytest.raises(ExceptionGroup) as caught:
            await ingest(sources[:1], opener=configured)
        assert failure in caught.value.exceptions

    run_async(scenario())


def test_child_cancellation_never_returns_partial_report(sources, run_async):
    async def scenario():
        @asynccontextmanager
        async def configured(source):
            raise asyncio.CancelledError
            yield chunks([])

        with pytest.raises(FeedError, match="Incomplete batch"):
            await ingest(sources[:1], opener=configured, workers=1, queue_size=1)

    run_async(scenario())


def test_config_snapshot_survives_caller_list_mutation(sources, run_async):
    async def scenario():
        started, release = asyncio.Event(), asyncio.Event()
        opened = []

        @asynccontextmanager
        async def configured(source):
            opened.append(source.label)
            started.set()
            await release.wait()
            yield records()

        async def records():
            yield Record("api", 1)

        job = asyncio.create_task(ingest(sources, opener=configured, workers=1))
        await started.wait()
        sources.clear()
        release.set()
        assert await job == {"sources": 2, "count": 2, "total": 2}
        assert opened == ["feed-a", "feed-b"]

    run_async(scenario())


def test_cancellation_awaits_async_cleanup_before_finishing(sources, run_async):
    async def scenario():
        entered, cleanup_started, cleanup_release = asyncio.Event(), asyncio.Event(), asyncio.Event()
        closed = []

        @asynccontextmanager
        async def configured(source):
            try:
                entered.set()
                await asyncio.Event().wait()
                yield chunks([])
            finally:
                cleanup_started.set()
                await cleanup_release.wait()
                closed.append(source.label)

        job = asyncio.create_task(ingest(sources[:1], opener=configured, workers=1))
        await entered.wait()
        job.cancel()
        await cleanup_started.wait()
        assert not job.done() and not closed
        cleanup_release.set()
        with pytest.raises(asyncio.CancelledError):
            await job
        assert closed == ["feed-a"]

    run_async(scenario())


def test_snapshot_enforces_actual_source_count_before_io(run_async):
    class Underreported(Sequence):
        def __len__(self):
            return 1

        def __getitem__(self, index):
            if index >= 17:
                raise IndexError
            return Source(f"a{index}", "https://example.test")

    @asynccontextmanager
    async def forbidden(source):
        pytest.fail("an oversized actual snapshot reached I/O")
        yield

    with pytest.raises(ConfigError):
        run_async(ingest(Underreported(), opener=forbidden))
