"""Public acceptance examples. Add your own tests; passing these is not certification."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from expenses import parse_amount, summarize_csv, summarize_rows

ROOT = Path(__file__).resolve().parents[1]


class AmountTests(unittest.TestCase):
    def test_valid_amounts_are_exact_integer_cents(self):
        for text, expected in [
            ("0", 0),
            ("12", 1200),
            ("12.3", 1230),
            ("12.30", 1230),
            (" 0.01 ", 1),
            ("001.05", 105),
            ("0.29", 29),
        ]:
            with self.subTest(text=text):
                result = parse_amount(text)
                self.assertIs(type(result), int)
                self.assertEqual(result, expected)

    def test_bad_amounts_are_rejected_not_rounded(self):
        for text in [
            "",
            " ",
            "-1",
            "+1",
            "1.234",
            "1.",
            ".50",
            "1,00",
            "1e2",
            "NaN",
            "Infinity",
            "£1",
            "١",
            "1.2.3",
            "1 2",
        ]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_amount(text)


class SummaryTests(unittest.TestCase):
    def test_grouping_normalization_and_no_mutation(self):
        rows = [
            {"category": " Food ", "amount": "1.20"},
            {"category": "food", "amount": "0.03"},
            {"category": "café", "amount": "0"},
        ]
        before = copy.deepcopy(rows)
        self.assertEqual(
            summarize_rows(iter(rows)),
            {"row_count": 3, "total_cents": 123, "by_category": {"food": 123, "café": 0}},
        )
        self.assertEqual(rows, before)

    def test_empty_and_repeated_calls_are_independent(self):
        first = summarize_rows([{"category": "books", "amount": "5"}])
        self.assertEqual(summarize_rows([]), {"row_count": 0, "total_cents": 0, "by_category": {}})
        self.assertEqual(summarize_rows([{"category": "food", "amount": "2"}])["by_category"], {"food": 200})
        self.assertEqual(first["by_category"], {"books": 500})

    def test_invalid_records_name_the_record(self):
        for bad in [
            {"category": " ", "amount": "1"},
            {"category": "food", "amount": "wrong"},
            {"category": "food"},
            {"category": "food", "amount": None},
            {"category": "food", "amount": "1", "extra": "x"},
        ]:
            with self.subTest(row=bad), self.assertRaisesRegex(ValueError, "record 3"):
                summarize_rows([{"category": "ok", "amount": "1"}, bad])


class FileAndCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def write_input(self, text):
        path = self.folder / "input.csv"
        path.write_text(text, encoding="utf-8")
        return path

    def run_cli(self, path):
        return subprocess.run(
            [sys.executable, str(ROOT / "cli.py"), str(path)],
            cwd=self.folder,
            capture_output=True,
            text=True,
            timeout=5,
        )

    def test_sample_and_quoted_fields(self):
        expected = json.loads((ROOT / "expected.json").read_text())
        self.assertEqual(summarize_csv(ROOT / "sample.csv"), expected)
        path = self.write_input('category,amount\n"food, snacks",2.50\n')
        self.assertEqual(summarize_csv(path)["by_category"], {"food, snacks": 250})

    def test_header_only_is_valid(self):
        self.assertEqual(
            summarize_csv(self.write_input("category,amount\n")),
            {"row_count": 0, "total_cents": 0, "by_category": {}},
        )

    def test_bad_headers(self):
        for text in ["", "amount,category\n", "category,amount,extra\n", "category,category\n"]:
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "header"):
                summarize_csv(self.write_input(text))

    def test_bad_row_width(self):
        for text in ["category,amount\nfood\n", "category,amount\nfood,1,extra\n"]:
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "record 2"):
                summarize_csv(self.write_input(text))

    def test_command_success_from_another_directory(self):
        result = self.run_cli(ROOT / "sample.csv")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), json.loads((ROOT / "expected.json").read_text()))

    def test_command_failure_never_prints_partial_report(self):
        path = self.write_input("category,amount\nfood,1\nbooks,bad\n")
        result = self.run_cli(path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("record 3", result.stderr)

    def test_missing_file_and_malformed_quotes(self):
        for path in [self.folder / "missing.csv", self.write_input('category,amount\n"unclosed,2.00\n')]:
            with self.subTest(path=path):
                result = self.run_cli(path)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr)

    def test_import_does_not_execute_the_command(self):
        result = subprocess.run(
            [sys.executable, "-c", "import cli; import expenses"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
