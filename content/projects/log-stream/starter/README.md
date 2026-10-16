# Streaming service-log lab

Build a local, one-pass summary from newline-delimited JSON. Use Python 3.13+ and the standard library. No network, database, background jobs or learner-code execution in the academy are involved.

## Run locally

From the extracted `log-stream` folder:

```sh
python -m unittest discover -s tests -v
python cli.py sample.ndjson
```

The untouched starter raises NotImplementedError. Implement the three functions in stream.py. The CLI is complete; keep its success/failure behavior. Compare parsed JSON output with expected.json; whitespace/key order are not significant. For an extra development check in your own virtual environment, install mypy 2.3.1 and run `python -m mypy --strict stream.py cli.py`. Runtime tests do not need that package.

## Exact input and API contract

- `Reading` is a frozen value with `kind: str` and `duration_ms: int`. It represents already-validated input; direct construction is an internal/trusted operation, not an input validator.
- `iter_readings(lines: Iterable[bytes])` is a generator yielding one Reading per supplied line. It borrows its source and must never close it. Creating the generator must not iterate or consume the source. Each next request consumes exactly one line before yielding or failing, with no lookahead. Each bytes item represents one complete line.
- Each line is at most `MAX_LINE_BYTES = 1024` bytes, including any LF or CRLF terminator. An exact-limit line is accepted if otherwise valid; longer lines raise RecordError. The final line need not have a newline. Decode as strict UTF-8, then use standard `json.loads` semantics (including its last-value behavior for duplicate keys). Blank/whitespace-only lines are invalid; an entirely empty source is valid.
- Each JSON value must be an object with exactly `kind` and `duration_ms`. Kind must be exactly `api`, `db` or `worker`, with no trimming or case conversion. Duration must be an integer from 0 through 60000 inclusive; reject booleans, floats, strings, null and out-of-range values. Do not coerce values or skip errors.
- For a bad line, raise `RecordError`, a ValueError subclass, with a message beginning `line N:` using the one-based physical position. Convert UnicodeDecodeError and JSONDecodeError using `raise ... from exc` so `__cause__` preserves the original error. Other upstream errors such as OSError propagate unchanged; do not recategorize them as malformed records.
- `open_readings(path: Path)` is a context manager. On entry it opens one binary file using `path.open("rb")`. Its line reader must call `readline(MAX_LINE_BYTES + 1)` to bound each read; reject excess length rather than collecting the rest of an oversized line. It must not read at entry, call read/readlines, or materialize the file. The extra byte permits exact-limit detection. Buffered file I/O may fetch a bounded block internally; the parser must not request the next logical line in advance.
- The context yields the parsed iterator. Consume it inside the with block. On scope exit, close both its parser generator and the owned file after success, no consumption, early stopping, parse errors or consumer errors. Propagate the error. A retained parser is exhausted after scope exit. Do not depend on garbage collection to release the file.
- `summarize(readings: Iterable[Reading])` consumes validated readings once, retaining only three groups of integer totals, never a list/history of records. Return all groups in the shape `{"api":{"count":0,"total_ms":0},"db":...,"worker":...}`, with zero values for missing groups. Counts/totals are exact integers, with fresh state per call. Do not close borrowed input or suppress its errors.
- The CLI prints one JSON report plus newline only after successful consumption and cleanup, exiting 0 with empty stderr. For malformed input or file OSError, exit 2 with a useful message on stderr and empty stdout. In particular, a later bad record must not print a partial success report. Importing cli or stream produces no output. Invoke the CLI by absolute path from any working directory.

The design retains one bounded record plus three counters/totals, not one object per input row. Integers can grow as totals grow. Public tests check lazy consumption and bounded reads; they are not a universal memory benchmark. The parser cannot undo output a different caller chooses to publish before a later failure. The supplied CLI therefore waits for full success.

## Evidence and review

Pass the public suite and add two regression tests. Demonstrate closing after an early stop and after an exception without forcing garbage collection. Explain owned versus borrowed sources and show a retained iterator after its scope ends. Record a line-numbered failure with its original cause.

Have a reviewer inspect the retained state in every stage and the error/cleanup paths. Do not replace the parser or summarizer with mocks. Tests use a file-like spy only to observe bounded reads and closure while exercising your implementation. Checklists are self-reported evidence, not automatic coding grades. Packaging, managed HTTP ingestion, retries and the full ingestion package remain future work.
