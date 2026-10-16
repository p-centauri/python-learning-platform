"""Behavioral acceptance checks; add your own regression cases."""

import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from stream import MAX_LINE_BYTES, Reading, RecordError, iter_readings, open_readings, summarize

GOOD = b'{"kind":"api","duration_ms":12}\n'
ROOT = Path(__file__).resolve().parents[1]


class ReadSpy(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.requests = []

    def read(self, *args):
        raise AssertionError("do not read the entire file")

    def readlines(self, *args):
        raise AssertionError("do not collect all lines")

    def readline(self, size=-1):
        self.requests.append(size)
        if size != MAX_LINE_BYTES + 1:
            raise AssertionError("bound every line read")
        return super().readline(size)


class StreamTests(unittest.TestCase):
    def test_parser_defers_work_and_does_not_look_ahead(self):
        touched = []

        def source():
            touched.append(1)
            yield GOOD
            touched.append(2)
            yield b'{"kind":"db","duration_ms":7}'
            raise OSError("later failure")

        records = iter_readings(source())
        self.assertEqual(touched, [])
        self.assertEqual(next(records), Reading("api", 12))
        self.assertEqual(touched, [1])
        self.assertEqual(next(records), Reading("db", 7))
        self.assertEqual(touched, [1, 2])
        with self.assertRaisesRegex(OSError, "later failure"):
            next(records)

    def test_iterator_exhaustion_and_empty_source(self):
        cursor = iter_readings([GOOD])
        self.assertEqual(list(cursor), [Reading("api", 12)])
        self.assertEqual(list(cursor), [])
        self.assertEqual(list(iter_readings([])), [])

    def test_values_and_line_endings(self):
        self.assertEqual(
            list(
                iter_readings(
                    [b'{"kind":"db","duration_ms":0}\r\n', b'{"kind":"worker","duration_ms":60000}']
                )
            ),
            [Reading("db", 0), Reading("worker", 60000)],
        )

    def test_schema_and_range_rejections(self):
        bad = [None, [], {}, {"kind": "api"}, {"kind": "api", "duration_ms": 1, "extra": 0}]
        bad += [{"kind": kind, "duration_ms": 1} for kind in ["API", " api", "other", 3, None]]
        bad += [{"kind": "api", "duration_ms": duration} for duration in [True, -1, 60001, 1.5, "2", None]]
        for value in bad:
            with self.subTest(value=value), self.assertRaisesRegex(RecordError, r"^line 1:"):
                list(iter_readings([json.dumps(value).encode()]))

    def test_error_line_and_original_cause(self):
        for raw, cause in [(b"\xff\n", UnicodeDecodeError), (b"{bad}\n", json.JSONDecodeError)]:
            with self.subTest(raw=raw):
                cursor = iter_readings([GOOD, raw])
                next(cursor)
                with self.assertRaisesRegex(RecordError, r"^line 2:") as caught:
                    next(cursor)
                self.assertIsInstance(caught.exception.__cause__, cause)

    def test_blank_lines_are_errors_not_skipped(self):
        for raw in [b"\n", b" \r\n"]:
            with self.subTest(raw=raw), self.assertRaisesRegex(RecordError, r"^line 2:"):
                list(iter_readings([GOOD, raw, GOOD]))

    def test_exact_byte_limit_and_one_byte_over(self):
        exact = GOOD.rstrip(b"\n") + b" " * (MAX_LINE_BYTES - len(GOOD)) + b"\n"
        self.assertEqual(len(exact), MAX_LINE_BYTES)
        self.assertEqual(list(iter_readings([exact])), [Reading("api", 12)])
        with self.assertRaisesRegex(RecordError, r"^line 1:"):
            list(iter_readings([exact + b" "]))

    def test_parser_does_not_close_borrowed_source(self):
        for data in [GOOD, b"{bad}\n"]:
            source = io.BytesIO(data)
            records = iter_readings(source)
            try:
                list(records)
            except RecordError:
                pass
            records.close()
            self.assertFalse(source.closed)
            source.close()

    def test_owned_file_closes_on_all_exit_paths(self):
        for mode in ["full", "unused", "early", "parse_error", "consumer_error"]:
            with self.subTest(mode=mode):
                source = ReadSpy(GOOD + (b"bad\n" if mode == "parse_error" else GOOD))
                consumer_error = RuntimeError("consumer stopped")
                with patch.object(Path, "open", return_value=source) as opened:
                    try:
                        with open_readings(Path("events.ndjson")) as records:
                            self.assertEqual(source.requests, [])
                            if mode in ["full", "parse_error"]:
                                list(records)
                            elif mode == "early":
                                next(records)
                                self.assertEqual(source.requests, [MAX_LINE_BYTES + 1])
                            elif mode == "consumer_error":
                                next(records)
                                raise consumer_error
                    except RecordError:
                        self.assertEqual(mode, "parse_error")
                    except RuntimeError as error:
                        self.assertEqual(mode, "consumer_error")
                        self.assertIs(error, consumer_error)
                    else:
                        self.assertNotIn(mode, ["parse_error", "consumer_error"])
                    opened.assert_called_once_with("rb")
                self.assertTrue(source.closed)
                self.assertIsNone(next(records, None))

    def test_oversized_file_read_is_bounded_and_closed(self):
        source = ReadSpy(b"x" * 100000)
        with patch.object(Path, "open", return_value=source):
            with self.assertRaisesRegex(RecordError, r"^line 1:"):
                with open_readings(Path("large.ndjson")) as records:
                    next(records)
        self.assertEqual(source.requests, [MAX_LINE_BYTES + 1])
        self.assertTrue(source.closed)

    def test_summary_one_pass_and_fixed_groups(self):
        class Once:
            def __init__(self):
                self.iterations = 0

            def __iter__(self):
                self.iterations += 1
                if self.iterations > 1:
                    raise AssertionError("second pass")
                return iter([Reading("api", 2), Reading("api", 3), Reading("db", 0)])

        self.assertEqual(
            summarize(Once()),
            {
                "api": {"count": 2, "total_ms": 5},
                "db": {"count": 1, "total_ms": 0},
                "worker": {"count": 0, "total_ms": 0},
            },
        )
        empty = summarize(iter(()))
        self.assertEqual(empty, {kind: {"count": 0, "total_ms": 0} for kind in ["api", "db", "worker"]})
        empty["api"]["count"] = 99
        self.assertEqual(summarize([])["api"]["count"], 0)

    def test_summary_large_generated_input_and_failure(self):
        self.assertEqual(
            summarize(Reading("worker", 60000) for _ in range(100000))["worker"],
            {"count": 100000, "total_ms": 6000000000},
        )
        error = OSError("read failed")

        def source():
            yield Reading("api", 1)
            raise error

        with self.assertRaises(OSError) as caught:
            summarize(source())
        self.assertIs(caught.exception, error)

    def test_cli_sample_from_other_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            run = subprocess.run(
                [sys.executable, str(ROOT / "cli.py"), str(ROOT / "sample.ndjson")],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=5,
            )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, "")
        self.assertEqual(json.loads(run.stdout), json.loads((ROOT / "expected.json").read_text()))

    def test_cli_later_failure_has_no_partial_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.ndjson"
            path.write_bytes(GOOD + b"{bad}\n")
            run = subprocess.run(
                [sys.executable, str(ROOT / "cli.py"), str(path)], capture_output=True, text=True, timeout=5
            )
        self.assertEqual(run.returncode, 2)
        self.assertEqual(run.stdout, "")
        self.assertIn("line 2:", run.stderr)

    def test_cli_missing_file_fails_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            run = subprocess.run(
                [sys.executable, str(ROOT / "cli.py"), str(Path(directory) / "missing")],
                capture_output=True,
                text=True,
                timeout=5,
            )
        self.assertEqual(run.returncode, 2)
        self.assertEqual(run.stdout, "")
        self.assertTrue(run.stderr)

    def test_imports_are_quiet(self):
        run = subprocess.run(
            [sys.executable, "-c", "import stream; import cli"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout + run.stderr, "")


if __name__ == "__main__":
    unittest.main()
