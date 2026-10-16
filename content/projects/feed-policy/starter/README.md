# Feed filtering & test-design lab

Extend the previous ingestion package with a separate filtering/reporting interface. Work locally on trusted code. The academy does not execute this download or grade uploaded Python. Checklist completion and a manual rubric review are separate from mastery.

## Setup

Use Python 3.13 or later in a fresh virtual environment:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
python -m mypy src/academy_feed_policy demo.py
python -m ruff check src tests demo.py
python demo.py
python -m build
```

The first run must fail: implement the three unfinished functions in `policy.py`. The reference is kept outside the download. Runtime code uses only the standard library; pytest, mypy, Ruff and build are development tools. Package-index access is needed for setup. Do not name your file `logging.py`, `re.py` or `pytest.py`.

## Exact contract

`parse_selector(spec)` returns `(prefix, minimum)`. Accept only `prefix:minimum`, with no trimming. Prefix is 1–16 ASCII characters, begins with a lowercase letter and then contains lowercase letters, ASCII digits or hyphens. Minimum is decimal ASCII digits from 0 through 60000 inclusive, with no leading zero except `0` itself. Reject signs, whitespace, Unicode digits, decimals, missing parts, extra separators and non-strings. Reject input longer than 22 characters before matching. Invalid input raises `RuleError` with a generic message that does not echo the input.

`make_selector(*, prefix, minimum)` validates those same settings. Minimum must be an actual `int`, excluding `bool`. Return a fresh function that accepts an already validated `Reading` and selects records whose ID starts with prefix and value is at least minimum. Independent selectors keep independent settings. No coercion or mutation of readings is needed.

`logged_report(reporter, *, logger, source_id)` returns a positional-only reporter wrapper. A source label follows the prefix grammar but allows up to 32 characters. Validate the label when creating the wrapper. Preserve metadata with `functools.wraps`. Pass the original iterable to the reporter exactly once. On success return the same report object. On failure preserve the same exception object and traceback; do not retry or suppress it.

Log `feed_report_started` at INFO before calling, then either `feed_report_succeeded` at INFO with `record_count`, or `feed_report_failed` at WARNING. Every event has only the configured `source_id` as extra context, plus count on success. Never log records, values, totals, raw source URLs, exception bodies, `exc_info` or stack traces. Do not configure global logging, add handlers, or write directly to stdout/stderr. Ordinary reporter exceptions derive from `Exception`; interrupts derive from `BaseException` and must propagate without a failure event. This bounded contract assumes a correctly configured, reliable logger and a reporter that returns a valid `Report`. Handler failures and general decorator signatures are outside this lab.

`apply_policy` is provided: it filters lazily and calls the reporter once. It borrows the input; it must not close it or materialize it. Creating the generator may call `iter` on the source, but does not request a record before the reporter runs. The caller owns resource lifetime. A late failure produces no success event or partial returned report.

`Reading` has read-only `id: str` and `value: int` properties, so the prior package's frozen `Record` satisfies it without inheritance or changes. `Report` has `count: int` and `total: int`. To connect the previous `summarize`, use a small typed adapter because a normal dictionary annotation is broader than this precise return contract. Keep HTTP acquisition and cleanup with the previous owner. This lab adds no network calls, retries, async work, authorization or new parser rules.

## Evidence for review

Run all public tests against your implementation; show the collected-case count and tool versions. Add two regressions that check behavior instead of asserting your own mock setup: one late source failure and one independently configured selector. Use fixtures for fresh input and yield cleanup, parametrization for boundary cases, `monkeypatch` at the lookup site, and `caplog` to inspect actual log records. Explain what each test can and cannot prove.

Install your built wheel into a second environment and run the tests and demo outside the source directory. Expected demo stdout is `{"count": 1, "total": 20}`; stderr is empty. Check quiet imports and the bundled `py.typed` marker. Include one structural integration with the previous ingestion records and explain ownership. Public tests are objective checks of a bounded contract; passing them does not prove every Python skill. Submit your repository/artifact link, test evidence, tradeoffs and known gaps for manual review in the academy.
