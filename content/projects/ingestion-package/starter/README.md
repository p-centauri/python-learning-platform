# Installable HTTP ingestion lab

Build a small Python 3.13+ package, install its wheel and test its real HTTP boundary without the internet. Implement `parser.py` and `http.py`; the models, CLI and packaging skeleton are complete. The untouched starter intentionally fails. This is a bounded intermediate lab, not a production ingestion platform.

## Run and install

Use a dedicated environment inside the extracted `ingestion-package` folder:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m mypy src/academy_ingest
.venv/bin/python -m ruff check src tests
.venv/bin/academy-ingest --demo
.venv/bin/python -m build
```

Windows environments use `.venv\Scripts\python` and `.venv\Scripts\academy-ingest`. Initial tool/dependency installation needs your chosen package index. The 28 public tests and demo use MockTransport and never contact a live server. Choose `--demo` or `--url`, never both. Demo JSON should match `expected.json`; key order/spacing do not matter. `sample.ndjson` shows the feed format; it is not a CLI file option.

Build first, then install the resulting `dist/academy_ingest_lab-0.1.0-py3-none-any.whl` into another fresh environment. Change to a directory outside the source tree and run both `academy-ingest --demo` and `python -m academy_ingest --demo`. Verify the imported file lives in that environment, and the bundled `defaults.json` and `py.typed` are present. An editable install alone does not establish that the wheel works.

## Exact parser contract

- `Record` is a frozen internal value with `id: str`, `value: int`. `iter_records(chunks: Iterable[bytes])` borrows input. It must be a lazy generator: creating or closing it before use touches no source. It must yield a completed record before requesting another chunk. A chunk may contain partial or multiple lines; UTF-8 characters may cross chunks. Do not assume a chunk is one line.
- LF separates physical lines; a final unterminated nonempty line is valid. CR in CRLF is part of the line bytes and legal JSON whitespace. Empty chunks are ignored; a completely empty body is valid; blank lines are invalid. Each line, excluding LF but including any CR, is at most `MAX_LINE_BYTES=1024` bytes. Accept the exact limit. Check pending length before copying segments; retain at most one bounded line. The borrowed chunk is already allocated by the source; this contract cannot bound arbitrary caller-owned chunks.
- Strict UTF-8 and `json.loads` semantics apply, including last value for duplicate JSON keys. Each decoded value must be an object with exactly `id` and `value`. ID matches `[a-z][a-z0-9-]{0,31}`. Value must be an actual integer in 0..60000; booleans, floats, strings, missing/extra fields and malformed records are rejected. No trimming, coercion, skipped failures or duplicate-ID detection.
- Raise `RecordError` beginning `line N:` with a one-based physical position. Preserve UnicodeDecodeError/JSONDecodeError as `__cause__`. Leave other upstream errors unchanged. Closing the parser must not close a borrowed source.
- `summarize` consumes validated records once, keeps only count and total, and returns `{"count":...,"total":...}` with fresh state, exact integers and zeros for empty input. No list/history or partial report.

## Exact HTTP contract

- `open_feed(url, *, client, max_bytes=8192)` is a context manager. Borrow the client; own and close one streamed response on success, no consumption, early exit, parser failure, HTTP read failure and consumer failure. Close its parser on exit so a retained iterator is exhausted. Consumer exceptions propagate unchanged. Do not close the borrowed client.
- Before requesting, require HTTPS, a hostname, no credentials/fragment/whitespace/control characters, and no nonstandard port. The limit must be an actual integer in 1..8192. These checks are syntax restrictions, **not protection against SSRF**: HTTPS URLs can reach private hosts. Only use trusted configured URLs. A future server-side fetcher needs destination/DNS/network policy; do not accept arbitrary end-user URLs in a service.
- Make exactly one GET using `client.stream(..., follow_redirects=False)`. Even if the borrowed client defaults to following redirects, override it. Only status 200 is accepted. Media type must be `application/x-ndjson`, ignoring case, surrounding spaces and optional parameters. Only missing/identity Content-Encoding is supported; reject compression before reading. Do not inspect response.text/content or call read.
- Do not read body data at context entry. Iterate raw bytes with `chunk_size=256`, checking cumulative actual bytes before passing each chunk to the parser. Reject excess bytes even if Content-Length lies or is missing. The exact total limit is allowed. Small internal buffering is permitted; this is not zero-copy transport. Compressed input is excluded so decoded expansion does not evade the contract.
- Convert HTTPX HTTPError during opening/body reads to `FeedError` with the original cause; do not expose remote body content in error messages. Status/media/size/URL failures also use FeedError. No silent retries, redirects or success after a partial stream. The CLI owns its client, sets finite connect/read/write/pool timeouts and small pool limits, disables environment proxies, and leaves TLS verification enabled. Per-operation timeouts do not constitute a total wall-clock deadline.
- Print one report only after complete validation and cleanup. Domain failures exit 2 with a useful stderr message and empty stdout. Importing the package/CLI must be quiet. The parser and HTTP context are separate so tests can exercise each without mocking away the behavior under test.

## Review evidence

Show the 28 public test results, strict type/lint results, wheel contents, clean installation, bundled-resource access and both CLI forms outside the checkout. Add two regressions, including a late malformed record and a failure after an early yield. Explain owned vs borrowed objects, line vs body bounds, timeout vs deadline and why arbitrary server-side URLs need more protection.

The app can preserve your repository reference, commit, test output, self-review, invited-account review and revisions. It does not run this package or certify correctness. Database writes, retries/checkpoints, async workers and applied AI ingestion will be separate continuation work.
