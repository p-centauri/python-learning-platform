import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from events import build_timeline, normalize_label

ROOT = Path(__file__).resolve().parents[1]


def payload(rows):
    return json.dumps(rows, ensure_ascii=False).encode("utf-8")


def event(label="ok", timestamp="2024-06-01T00:00:00Z"):
    return {"label": label, "timestamp": timestamp}


class TimelineTests(unittest.TestCase):
    def test_unicode_label_policy(self):
        for raw, expected in [
            (" Café ", "café"),
            ("CAFE\u0301", "café"),
            ("Straße", "strasse"),
            ("a, b", "a, b"),
        ]:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_label(raw), expected)

    def test_invalid_labels(self):
        for raw in ["", "  ", None, 3, []]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                normalize_label(raw)

    def test_sample_matches_expected(self):
        self.assertEqual(
            build_timeline((ROOT / "sample.json").read_bytes()),
            json.loads((ROOT / "expected.json").read_text()),
        )

    def test_offsets_are_converted_and_sorted(self):
        rows = [event("later", "2024-06-01T06:00:00Z"), event("earlier", "2024-06-01T10:00:00+05:00")]
        result = build_timeline(payload(rows))
        self.assertEqual([r["label"] for r in result], ["earlier", "later"])
        self.assertEqual(result[0]["timestamp"], "2024-06-01T05:00:00+00:00")

    def test_equal_instants_keep_input_order_and_duplicates(self):
        rows = [event("first", "2024-06-01T01:00:00+01:00"), event("second"), event("first")]
        self.assertEqual([r["label"] for r in build_timeline(payload(rows))], ["first", "second", "first"])

    def test_fractional_seconds_and_negative_offset(self):
        rows = [event("b", "2024-06-01T00:00:00.2Z"), event("a", "2024-05-31T19:00:00.1-05:00")]
        result = build_timeline(payload(rows))
        self.assertEqual(result[0], event("a", "2024-06-01T00:00:00.100000+00:00"))

    def test_naive_impossible_and_overflow_dates(self):
        for text in [
            "2024-02-30T00:00:00Z",
            "2024-06-01T00:00:00",
            "2024-06-01",
            "0001-01-01T00:00:00+01:00",
        ]:
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "record 2"):
                build_timeline(payload([event(), event(timestamp=text)]))

    def test_bad_record_shapes(self):
        for row in [None, [], {}, event(label=2), event(timestamp=2), {**event(), "extra": 1}]:
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, "record 2"):
                build_timeline(payload([event(), row]))

    def test_invalid_encoding_json_and_top_level(self):
        for raw in [
            b'[{"label":"\xff","timestamp":"2024-06-01T00:00:00Z"}]',
            b"not json",
            b"{}",
            b"null",
            b"3",
        ]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                build_timeline(raw)

    def test_empty_and_repeated_calls(self):
        build_timeline(payload([event("before")]))
        self.assertEqual(build_timeline(b"[]"), [])
        self.assertEqual(build_timeline(payload([event("after")]))[0]["label"], "after")

    def test_cli_success_from_another_directory(self):
        with tempfile.TemporaryDirectory() as cwd:
            run = subprocess.run(
                [sys.executable, str(ROOT / "cli.py"), str(ROOT / "sample.json")],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=5,
            )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, "")
        self.assertEqual(json.loads(run.stdout), json.loads((ROOT / "expected.json").read_text()))

    def test_cli_error_has_no_partial_output(self):
        with tempfile.TemporaryDirectory() as cwd:
            source = Path(cwd) / "bad.json"
            source.write_bytes(payload([event(), event(timestamp="not-a-date")]))
            for path in [source, Path(cwd) / "missing.json"]:
                run = subprocess.run(
                    [sys.executable, str(ROOT / "cli.py"), str(path)],
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self.assertEqual(run.returncode, 2)
                self.assertEqual(run.stdout, "")
                self.assertTrue(run.stderr)

    def test_import_is_quiet(self):
        run = subprocess.run(
            [sys.executable, "-c", "import events; import cli"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout + run.stderr, "")


if __name__ == "__main__":
    unittest.main()
