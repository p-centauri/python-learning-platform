# Expense tracker CLI — learner starter

Implement the three functions in `expenses.py`. They intentionally raise NotImplementedError until you write them. The supplied CLI and public tests are ready to use. Initial test failures are expected; they show the work remaining, not a broken environment. No third-party packages are required.

Work through the academy's nine Python foundations lessons. The app does not run or grade this code. Run it locally with Python 3.13+ and review the result separately.

## Run

From this folder, using your environment's Python:

```sh
python cli.py --help
python -m unittest discover -s tests -v
python cli.py sample.csv
```

On Windows without activation, replace `python` with `.\.venv\Scripts\python.exe` after creating the environment. On macOS/Linux without activation, use `.venv/bin/python`. The lesson on setup explains creating the environment. Compare the successful JSON to `expected.json` as parsed values; key order and indentation do not matter.

## Exact contract

This is a small, single-currency learning project. Integer cents represent a currency with two decimal places. It does not implement tax, exchange rates, refunds, authentication or production financial accounting.

### parse_amount(text)

- The input is a string. Strip surrounding whitespace.
- Accept one or more ASCII digits, optionally followed by a dot and exactly one or two ASCII digits. Leading zeros and zero are allowed.
- Examples: `"12"` → 1200, `"12.3"` → 1230, `"12.30"` → 1230, `" 0 "` → 0.
- Reject negatives, signs, empty text, currency symbols, commas, exponent notation, NaN/Infinity, `.50`, `12.`, and more than two fractional digits with ValueError.
- Return an integer. Do not go through float and do not silently round bad input.

### summarize_rows(rows)

- Accept an iterable of dictionary records containing exactly the keys `category` and `amount`, with string values. A missing/extra field or non-string value is invalid.
- Strip outer whitespace from category and lowercase it. An empty result is invalid. Preserve internal characters, including commas and Unicode text.
- Use the amount contract above. Zero-valued records still count and their category is present.
- For invalid records, raise ValueError with the logical record number (starting at 2 after the header) and an actionable reason. CSV record numbers are not guaranteed to be physical line numbers.
- Return `{"row_count": int, "total_cents": int, "by_category": {str: int}}` with exact sums. Duplicate categories add together; duplicate rows count as separate expenses.
- Empty rows produce a zero/empty report. Each call uses fresh state and leaves input records unchanged. Do not retain all input rows; a category mapping may grow with the number of distinct categories.

### summarize_csv(path)

- Accept a path string or pathlib.Path. Open text as UTF-8 using `newline=""` and a with block.
- Use csv.DictReader with `strict=True` to handle quoted commas and malformed quoting.
- Require the header to be exactly `category,amount`, in that order. Missing, duplicate or extra columns are rejected with ValueError mentioning the header. Whitespace/BOM in header names is not normalized.
- Read rows while the file is open and feed them into summarize_rows. Missing/extra row fields are invalid. Blank physical lines follow the CSV reader's behavior (ignored).
- A header-only file is valid; a truly empty file is not. Expected malformed CSV, Unicode and file errors must reach the CLI (ValueError, csv.Error or OSError), not become an empty successful report.

### CLI

The provided `cli.py` accepts one CSV path. Success means exit 0, empty stderr, and one JSON report on stdout. Invalid input or file errors mean exit 2, an error on stderr, and no report on stdout. NotImplementedError and other unexpected programming errors are intentionally not disguised as input errors.

The command must work when launched from a different working directory with absolute script/input paths. Importing expenses must not read files or print output. Shell output redirection is optional; atomic output-file replacement and crash recovery are outside this module.

## Implementation order

1. Make amount cases pass. Use the worked parser in lesson 5 as a guide and explain each rule.
2. Summarize one valid row, then several categories, then invalid and empty records.
3. Add file/header handling. Keep the file open while consuming its rows.
4. Run the real command for success and failure, then run every test.
5. Add at least three tests of your own from mistakes or edge cases you discovered.

Do not edit the expected output to fit a wrong implementation. The tests are public acceptance examples, not exhaustive certification. A passing suite still needs code review.

## Review evidence

Demonstrate exact money conversion, invalid-record messages, quoted CSV, zero and empty inputs, independent repeated calls, and no partial JSON on errors. Explain why you chose each data structure and where files close. Show the added tests and a run from another folder. The academy project checklist records your own progress; it does not verify these claims automatically.
