import asyncio
import json
import httpx
import pytest
from academy_ingestion_service import Datum
from academy_resource_scopes import Resource, current_request, owned_resources, request_scope
from academy_practical_review import read_all, prepare
from academy_practical_review.jobs import observe_jobs

TOKEN = "local_test_token_12345"


class Stream(httpx.AsyncByteStream):
    def __init__(self, chunks, wait=False):
        self.chunks = chunks
        self.wait = wait
        self.closed = False
        self.entered = asyncio.Event()

    async def __aiter__(self):
        self.entered.set()
        if self.wait:
            await asyncio.Event().wait()
        for chunk in self.chunks:
            yield chunk

    async def aclose(self):
        self.closed = True


def encoded(id="a", cursor=None):
    return json.dumps(dict(items=[dict(id=id, revision=1, value=0)], next_cursor=cursor)).encode()


def test_async_page_ownership_scoped_request_and_cursor():
    async def scenario():
        streams = []
        queries = []

        async def handle(request):
            assert request.headers["authorization"] == "Bearer " + TOKEN
            assert request.url.path == "/namespaces/north/readings"
            queries.append(dict(request.url.params))
            raw = encoded("a", dict(id="a", revision=1)) if len(queries) == 1 else encoded("b")
            stream = Stream([raw])
            streams.append(stream)
            return httpx.Response(200, headers={"content-type": "application/json"}, stream=stream)

        async with httpx.AsyncClient(
            base_url="https://fixture.invalid", transport=httpx.MockTransport(handle)
        ) as client:
            assert await read_all(client, "north", TOKEN) == (Datum("a", 1, 0), Datum("b", 1, 0))
            assert not client.is_closed and all(s.closed for s in streams)
        assert queries == [dict(limit="32"), dict(limit="32", after_id="a", after_revision="1")]

    asyncio.run(scenario())


def test_cancelled_reader_closes_response_but_keeps_borrowed_client():
    async def scenario():
        stream = Stream([], wait=True)

        async def handle(request):
            return httpx.Response(200, headers={"content-type": "application/json"}, stream=stream)

        async with httpx.AsyncClient(
            base_url="https://fixture.invalid", transport=httpx.MockTransport(handle)
        ) as client:
            task = asyncio.create_task(read_all(client, "north", TOKEN))
            await asyncio.wait_for(stream.entered.wait(), 1)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert stream.closed and not client.is_closed

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "raw",
    [
        b"x" * 8193,
        b"{",
        b'{"items":[],"items":[],"next_cursor":null}',
        encoded("a", dict(id="b", revision=1)),
    ],
)
def test_page_failure_closes_owned_stream(raw):
    async def scenario():
        stream = Stream([raw])

        async def handle(request):
            return httpx.Response(200, headers={"content-type": "application/json"}, stream=stream)

        async with httpx.AsyncClient(
            base_url="https://fixture.invalid", transport=httpx.MockTransport(handle)
        ) as client:
            with pytest.raises(ValueError):
                await read_all(client, "north", TOKEN)
            assert stream.closed and not client.is_closed

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "status,media",
    [(401, "application/json"), (503, "application/json"), (302, "application/json"), (200, "text/plain")],
)
def test_refused_status_or_media_does_not_use_response(status, media):
    async def scenario():
        stream = Stream([b"private"])

        async def handle(request):
            return httpx.Response(status, headers={"content-type": media}, stream=stream)

        async with httpx.AsyncClient(
            base_url="https://fixture.invalid", transport=httpx.MockTransport(handle)
        ) as client:
            with pytest.raises(ValueError):
                await read_all(client, "north", TOKEN)
            assert stream.closed

    asyncio.run(scenario())


def test_page_cap_and_repeated_cursor_fail_without_unbounded_requests():
    async def scenario(repeat):
        calls = []
        streams = []

        async def handle(request):
            calls.append(request)
            id = "a" if repeat else "item-" + str(len(calls)).zfill(2)
            stream = Stream([encoded(id, dict(id=id, revision=1))])
            streams.append(stream)
            return httpx.Response(200, headers={"content-type": "application/json"}, stream=stream)

        async with httpx.AsyncClient(
            base_url="https://fixture.invalid", transport=httpx.MockTransport(handle)
        ) as client:
            with pytest.raises(ValueError):
                await read_all(client, "north", TOKEN)
            assert len(calls) == (2 if repeat else 8) and all(s.closed for s in streams)

    asyncio.run(scenario(False))
    asyncio.run(scenario(True))


def test_partial_resource_failure_restores_context_and_removes_owned_files(tmp_path):
    path = tmp_path / "owned"
    events = []

    def acquire():
        path.write_text("0")

        def close():
            events.append(current_request())
            path.unlink()

        return Resource(path, close)

    def fail():
        raise LookupError("original failure")

    with pytest.raises(LookupError, match="original failure"):
        with request_scope("partial"), owned_resources([acquire, fail]):
            pass
    assert not path.exists() and current_request() is None and events == ["partial"]


def test_actual_prior_thread_spawn_file_and_context_contracts():
    import os

    report = observe_jobs(prepare("north", [Datum("a", 1, 0), Datum("b", 1, 5)]))
    assert report["jobs"] == 2 and report["equivalent"] and report["files_closed"]
    assert report["context_restored"] and report["directories_removed"] == [True]
    assert report["cleanup_labels"] == ["review-jobs"] and report["thread_pids"] == [os.getpid()]
    assert report["spawn_pids"] and os.getpid() not in report["spawn_pids"]
