"""Public local contract checks. Exercise the real parser and HTTP boundary."""
from collections.abc import Iterator
from contextlib import contextmanager
import json
import io
import subprocess
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

import httpx

from academy_ingest import FeedError, Record, RecordError, iter_records, open_feed, summarize
from academy_ingest.models import MAX_BODY_BYTES, MAX_LINE_BYTES

URL = "https://feed.example.test/events"
ROW = b'{"id":"api","value":10}\n'


class ObservedStream(httpx.SyncByteStream):
    def __init__(self, chunks: list[bytes], fail: Exception | None = None) -> None:
        self.chunks = chunks
        self.fail = fail
        self.reads = 0
        self.closed = False

    def __iter__(self) -> Iterator[bytes]:
        for chunk in self.chunks:
            self.reads += 1
            yield chunk
        if self.fail is not None:
            raise self.fail

    def close(self) -> None:
        self.closed = True


@contextmanager
def fixture(
    chunks: list[bytes] | None = None, *, status: int = 200,
    headers: dict[str, str] | None = None, fail: Exception | None = None,
) -> Iterator[tuple[httpx.Client, ObservedStream, list[httpx.Request]]]:
    stream = ObservedStream(chunks if chunks is not None else [ROW], fail)
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(status, headers=headers or {"content-type": "application/x-ndjson"}, stream=stream)

    with httpx.Client(transport=httpx.MockTransport(handle), timeout=2, trust_env=False) as client:
        yield client, stream, requests


class ParsingTests(unittest.TestCase):
    def test_empty_input_and_empty_chunks(self) -> None:
        self.assertEqual(list(iter_records([])), [])
        self.assertEqual(list(iter_records([b"", b""])), [])

    def test_arbitrary_chunks_and_final_unterminated_line(self) -> None:
        body = ROW + b'{"id":"worker-1","value":0}'
        self.assertEqual(list(iter_records(bytes([b]) for b in body)), [Record("api", 10), Record("worker-1", 0)])

    def test_crlf_and_split_utf8_identifier(self) -> None:
        self.assertEqual(list(iter_records([b'{"id":"api","value":10}\r\n'])), [Record("api", 10)])
        # Unicode in a rejected identifier is decoded across chunk boundaries.
        with self.assertRaises(RecordError):
            list(iter_records([b'{"id":"caf\xc3', b'\xa9","value":1}\n']))

    def test_generator_creation_does_not_touch_source(self) -> None:
        def source() -> Iterator[bytes]:
            raise AssertionError("source touched")
            yield b""
        iterator = iter_records(source())
        iterator.close()

    def test_yields_before_asking_for_another_chunk(self) -> None:
        def source() -> Iterator[bytes]:
            yield ROW
            raise AssertionError("read ahead")
        iterator = iter_records(source())
        self.assertEqual(next(iterator), Record("api", 10))
        iterator.close()

    def test_exact_line_limit_and_excess_in_later_chunk(self) -> None:
        raw = ROW.rstrip(b"\n")
        padding = b" " * (MAX_LINE_BYTES - len(raw))
        self.assertEqual(list(iter_records([raw, padding, b"\n"])), [Record("api", 10)])
        with self.assertRaisesRegex(RecordError, "line 1:.*byte limit"):
            list(iter_records([raw, padding, b" \n"]))

    def test_blank_line_is_invalid_not_an_empty_feed(self) -> None:
        for raw in [b"\n", b" \r\n", b"   "]:
            with self.subTest(raw=raw), self.assertRaisesRegex(RecordError, "line 1:"):
                list(iter_records([raw]))

    def test_strict_shape_and_numeric_rules(self) -> None:
        values: list[object] = [True, False, 1.0, "1", None, -1, 60001]
        rows: list[object] = [[], None, {}, {"id": "api", "value": 1, "extra": 2}]
        rows += [{"id": "api", "value": value} for value in values]
        rows += [{"id": name, "value": 1} for name in ["", "API", " api", "a" * 33, "../a", 1]]
        for row in rows:
            with self.subTest(row=row), self.assertRaises(RecordError):
                list(iter_records([json.dumps(row).encode()]))
        self.assertEqual(list(iter_records([b'{"id":"z-1","value":60000}'])), [Record("z-1", 60000)])

    def test_error_position_and_original_json_cause(self) -> None:
        iterator = iter_records([ROW + b"{bad}\n"])
        self.assertEqual(next(iterator), Record("api", 10))
        with self.assertRaisesRegex(RecordError, "line 2:") as raised:
            next(iterator)
        self.assertIsInstance(raised.exception.__cause__, json.JSONDecodeError)

    def test_original_decode_cause(self) -> None:
        with self.assertRaises(RecordError) as raised:
            list(iter_records([b"\xff\n"]))
        self.assertIsInstance(raised.exception.__cause__, UnicodeDecodeError)

    def test_upstream_failure_propagates_and_source_is_borrowed(self) -> None:
        error = OSError("source broke")
        closed: list[bool] = []
        def source() -> Iterator[bytes]:
            try:
                yield ROW
                raise error
            finally:
                closed.append(True)
        borrowed = source()
        parser = iter_records(borrowed)
        next(parser)
        parser.close()
        self.assertEqual(closed, [])
        with self.assertRaises(OSError) as raised:
            next(borrowed)
        self.assertIs(raised.exception, error)

    def test_summary_one_use_empty_and_fresh_state(self) -> None:
        self.assertEqual(summarize(iter([Record("a", 10), Record("b", 5)])), {"count": 2, "total": 15})
        self.assertEqual(summarize(iter(())), {"count": 0, "total": 0})
        self.assertEqual(summarize(Record("a", 1) for _ in range(20000)), {"count": 20000, "total": 20000})


class HTTPTests(unittest.TestCase):
    def test_complete_response_and_borrowed_client(self) -> None:
        with fixture() as (client, stream, requests):
            with open_feed(URL, client=client) as records:
                self.assertEqual(summarize(records), {"count": 1, "total": 10})
            self.assertTrue(stream.closed)
            self.assertFalse(client.is_closed)
            self.assertEqual(requests[0].method, "GET")
            self.assertEqual(requests[0].extensions["timeout"]["read"], 2)

    def test_no_reads_at_entry_and_close_without_consumption(self) -> None:
        with fixture() as (client, stream, _):
            with open_feed(URL, client=client) as records:
                self.assertEqual(stream.reads, 0)
            self.assertTrue(stream.closed)
            self.assertEqual(list(records), [])

    def test_early_exit_closes_retained_iterator(self) -> None:
        with fixture([ROW * 30]) as (client, stream, _):
            with open_feed(URL, client=client) as records:
                self.assertEqual(next(records), Record("api", 10))
            self.assertTrue(stream.closed)
            self.assertEqual(list(records), [])

    def test_parser_failure_closes_response(self) -> None:
        with fixture([b"bad\n"]) as (client, stream, _):
            with self.assertRaises(RecordError), open_feed(URL, client=client) as records:
                list(records)
            self.assertTrue(stream.closed)

    def test_consumer_failure_keeps_identity_and_closes(self) -> None:
        for error in [RuntimeError("caller failed"), httpx.ReadTimeout("caller operation")]:
            with fixture() as (client, stream, _):
                with self.assertRaises(type(error)) as raised:
                    with open_feed(URL, client=client):
                        raise error
                self.assertIs(raised.exception, error)
                self.assertTrue(stream.closed)

    def test_invalid_status_does_not_read_or_retry(self) -> None:
        for status in [204, 301, 404, 429, 503]:
            with fixture(status=status) as (client, stream, requests):
                with self.assertRaisesRegex(FeedError, str(status)), open_feed(URL, client=client):
                    self.fail("should not yield")
                self.assertTrue(stream.closed)
                self.assertEqual(stream.reads, 0)
                self.assertEqual(len(requests), 1)

    def test_redirect_override_even_if_client_follows(self) -> None:
        def handle(request: httpx.Request) -> httpx.Response:
            return httpx.Response(302, headers={"location": "https://other.example.test/"})
        with httpx.Client(transport=httpx.MockTransport(handle), follow_redirects=True) as client:
            with self.assertRaisesRegex(FeedError, "302"), open_feed(URL, client=client):
                self.fail("should not follow")

    def test_media_type_and_compression_rejected(self) -> None:
        for headers in [{"content-type": "text/html"}, {"x-other": "missing"},
                        {"content-type": "application/x-ndjson", "content-encoding": "gzip"}]:
            with fixture(headers=headers) as (client, stream, _):
                with self.assertRaises(FeedError), open_feed(URL, client=client):
                    self.fail("should not yield")
                self.assertTrue(stream.closed)
                self.assertEqual(stream.reads, 0)

    def test_media_type_parameters_accepted(self) -> None:
        with fixture(headers={"content-type": "Application/X-NDJSON; charset=utf-8"}) as (client, _, _):
            with open_feed(URL, client=client) as records:
                self.assertEqual(len(list(records)), 1)

    def test_actual_bytes_counted_not_content_length(self) -> None:
        with fixture([ROW], headers={"content-type": "application/x-ndjson", "content-length": "1"}) as (client, stream, _):
            with self.assertRaisesRegex(FeedError, "body byte limit"), open_feed(URL, client=client, max_bytes=len(ROW)-1) as records:
                list(records)
            self.assertTrue(stream.closed)
        with fixture([ROW]) as (client, _, _):
            with open_feed(URL, client=client, max_bytes=len(ROW)) as records:
                self.assertEqual(len(list(records)), 1)

    def test_stream_read_failure_keeps_cause_and_closes(self) -> None:
        error = httpx.ReadTimeout("read stalled")
        with fixture([ROW], fail=error) as (client, stream, requests):
            with self.assertRaises(FeedError) as raised:
                with open_feed(URL, client=client) as records:
                    list(records)
            self.assertIs(raised.exception.__cause__, error)
            self.assertTrue(stream.closed)
            self.assertEqual(len(requests), 1)

    def test_connect_failure_keeps_cause(self) -> None:
        error = httpx.ConnectTimeout("connect stalled")
        def handle(request: httpx.Request) -> httpx.Response:
            raise error
        with httpx.Client(transport=httpx.MockTransport(handle)) as client:
            with self.assertRaises(FeedError) as raised, open_feed(URL, client=client):
                self.fail("should not yield")
            self.assertIs(raised.exception.__cause__, error)

    def test_bad_urls_and_limits_make_no_request(self) -> None:
        with fixture() as (client, _, requests):
            for url in ["http://feed.example.test/", "https://user:pw@feed.example.test/", "https://feed.example.test/#x", "https://feed.example.test:444/", "https://feed.example.test:bad/", "file:///tmp/a", "https://feed.example.test/a b"]:
                with self.subTest(url=url), self.assertRaises(FeedError), open_feed(url, client=client):
                    self.fail("should not yield")
            for limit in [True, 0, -1, MAX_BODY_BYTES + 1]:
                with self.subTest(limit=limit), self.assertRaises(FeedError), open_feed(URL, client=client, max_bytes=limit):
                    self.fail("should not yield")
            self.assertEqual(requests, [])


class CommandTests(unittest.TestCase):
    def test_late_bad_record_prints_no_partial_cli_success(self) -> None:
        from academy_ingest.cli import main
        stream = ObservedStream([ROW, b"{bad}\n"])
        def handle(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, headers={"content-type": "application/x-ndjson"}, stream=stream)
        transport = httpx.MockTransport(handle)
        output, errors = io.StringIO(), io.StringIO()
        with patch("academy_ingest.cli.httpx.MockTransport", return_value=transport), patch.object(
            sys, "argv", ["academy-ingest", "--demo"]
        ), redirect_stdout(output), redirect_stderr(errors):
            status = main()
        self.assertEqual(status, 2)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("line 2:", errors.getvalue())
        self.assertTrue(stream.closed)

    def test_module_demo_and_quiet_import(self) -> None:
        result = subprocess.run([sys.executable, "-m", "academy_ingest", "--demo"], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"count": 2, "total": 15})
        self.assertEqual(result.stderr, "")
        imported = subprocess.run([sys.executable, "-c", "import academy_ingest; import academy_ingest.cli"], capture_output=True, text=True, timeout=10)
        self.assertEqual(imported.returncode, 0, imported.stderr)
        self.assertEqual(imported.stdout + imported.stderr, "")

    def test_bad_cli_url_has_no_partial_success(self) -> None:
        result = subprocess.run([sys.executable, "-m", "academy_ingest", "--url", "http://bad.example.test"], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("HTTPS", result.stderr)


if __name__ == "__main__":
    unittest.main()
