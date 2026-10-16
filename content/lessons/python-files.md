## Files have a location and a lifetime

This is lesson 7 of 9. Use `pathlib.Path` to describe a location. A relative path is interpreted from the program's working directory, which is not always the source file's directory. When a file is missing, show the user which input could not be read; do not silently create an empty report instead.

Use a `with` block when opening a file. It closes the file when the block ends, including when processing raises an error. For text, name the encoding. Our project reads UTF-8 CSV. Passing `newline=""` lets the CSV reader handle line endings correctly.

## Let CSV understand CSV

```python
import csv
from io import StringIO

text = 'category,amount\n"food, snacks",2.50\ntravel,1.00\n'
reader = csv.DictReader(StringIO(text, newline=""), strict=True)
rows = list(reader)
assert rows[0]["category"] == "food, snacks"
assert rows[0]["amount"] == "2.50"
```

A quoted comma belongs inside the category. `line.split(",")` would split it incorrectly. DictReader uses the first row as field names, and the returned values are still strings. It does not validate amount rules for you.

To use a real file, put the reader inside `with Path(path).open(encoding="utf-8", newline="") as source:`. Process its rows while that block is open. The example makes a list only to inspect a tiny sample; the project should process input one record at a time.

## Define the file contract

Require exactly `category,amount` in that order as the header. Reject absent, duplicate or unexpected columns. Also reject rows with missing or extra fields. DictReader uses None for some missing values and as a key for extra values; check the row shape before calling string methods. Empty categories and invalid amounts stop the report with a record-specific error.

A correct header with no data is valid and should yield zero totals. A truly empty file is invalid because its header is missing. Blank physical lines are ignored by the CSV reader. The project's README states these rules so your tests and implementation agree.

## Produce JSON only after success

```python
import json

report = {"row_count": 2, "total_cents": 350,
          "by_category": {"food, snacks": 250, "travel": 100}}
encoded = json.dumps(report, ensure_ascii=False, sort_keys=True)
assert json.loads(encoded) == report
```

JSON is a format for exchanging data. Use the library rather than building quoted text by hand. This project prints one finished report on stdout. It does not print each partial result, so a later bad record cannot leave success-looking output behind. The caller can redirect a successful report to a file; output-file crash safety is outside this first project's scope.

## Guided practice

Change the sample to include a category named `café` and confirm it survives a JSON round trip. Add an extra field to a CSV record and inspect the row returned by DictReader before deciding how to reject it.

## Independent task

Read a temporary CSV file with a with block. Check its header and count accepted rows. Test a missing file, a header-only file, a missing column and a quoted comma. Do not use eval to parse data.

## Check your work

Valid inputs produce the expected count. Invalid shapes produce clear errors before amount conversion. You can explain where the file is opened, where it closes, and why CSV and JSON need their own parsers.

[Next: modules and command-line tools](/lessons/python-cli)
