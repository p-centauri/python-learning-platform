# Typed transformation lab

Implement four functions in `src/academy_typed_transforms/transform.py`: map_rows, watch_call, first and decode_row. Keep the published annotations, overloads and supplied interfaces/validation. This is a synchronous standard-library package for Python 3.13+, not an async worker, database or automatic academy grading service.

## Literal runtime and type contract

- `map_rows(rows, mapper, /, *, limit=64)` relates input T to mapper output U and returns `tuple[U, ...]`. Accept exact integer limits 0..64; reject bool/wrong type with TypeError and range errors with ValueError. Validate options and callability before acquiring input. Consume a borrowed iterable once in order. On overflow observe item limit+1, raise ValueError without mapping it, and never fetch another. Propagate input/mapper failures unchanged, with one mapper call per accepted item and no retries/partial return. Do not close borrowed input. A tuple does not freeze mutable mapper results; item count does not stop blocked user code.
- `watch_call(function, /, *, observer)` returns Callable[P,R] with the original positional/keyword parameter contract and return type. Reject non-callables when configuring. Use wraps so inspect.signature, name/doc/custom attributes and __wrapped__ preserve the target. Configuring emits nothing. On each call emit only `started`, then either `returned` or `raised`; call the target once with the same objects/arguments. Return its exact result or re-raise its exact BaseException when the observer is reliable. No argument/result/exception text is emitted. These events describe calling/returning, not later generator or awaitable completion.
- Observer failures deliberately propagate: failure on started prevents the target; failure on returned occurs after the target's successful effects; failure on raised replaces the target exception while retaining Python's exception context. No retry or observer-failure suppression is promised. This explicit limit matters when using wrappers around side effects.
- `first(rows, /)` returns T|None. With an explicit keyword default U it returns T|U, preserving the exact first/default object. Use the borrowed Sequence's length and index zero only; no materialization. Normal consistent Sequence behavior is assumed. Overloads describe two call shapes, not runtime dispatch; the implementation handles both.
- `is_row_payload` is supplied: a positive TypeGuard recognizes an exact dict with exactly id/value and exact str/int fields (reject bool). It narrows the true branch only and does not prove domain validity or make mutable input permanently safe. `decode_row(payload: object)` must check current shape and return a fresh supplied frozen Row, without input mutation/coercion. Malformed shape/type raises TypeError; Row rejects non-ASCII/empty/overlong IDs and values outside 0..60000 with ValueError. Identifier grammar `[a-z][a-z0-9-]{0,31}`. Exact built-in strings/integers exclude subclasses that could change value behavior.
- Read-only `Valued[T_co]` is covariant; `Consumer[T_contra]` is contravariant. They describe structural static interfaces, not runtime validation. Call sites must retain input/result types and keyword-only restrictions. Do not erase relationships with Any, casts or type-ignore comments.

## Run separate evidence checks

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
python -m mypy --strict src/academy_typed_transforms demo.py
python check_types.py --package-path src
python -m ruff check src tests demo.py check_types.py typing/positive.py
python -m build
```

`check_types.py` statically checks one positive file with assert_type and ten separate rejected-call fixtures. It requires exactly the documented diagnostic for each rejection, not just any failing command. It never executes those snippets. The unfinished starter can type-check while failing runtime tests; prove both layers. Mypy 2.3.1 is pinned for reproducible diagnostics.

Install the built wheel plus pytest==9.0.3 and mypy==2.3.1 in a second fresh environment. Copy tests, demo.py, check_types.py and typing/ to an empty folder outside source; unset PYTHONPATH and MYPYPATH. Run `python -I -m pytest -q tests`, `python -I check_types.py` (no package-path), `python -I demo.py` and `python -m pip check`. Check the imported module lives in that environment and its py.typed marker is packaged. The wheel must exclude tests, fixtures and maintained reference. Expected demo: count=2, total=15, first="api", events=["started","returned","started","returned"], empty stderr.

Adapt the previous ingestion Records through read-only Valued[int] and map_rows, and adapt Row output to the previous Reading/FeedKey/Snapshot in a separate strict-typed offline script. Preserve all existing package contracts. No network is required for this adapter.

## Submit reproducible review evidence

Provide actual runtime/checker/lint/build/install commands and output, two extra regression cases, and a type-error explanation with its corrected call. Explain variance direction, generic input/output relationships, overload empty/default cases, honest guards and observer/input ownership. A reviewer should inspect runtime failures and type-rejected calls separately.

Four manual criteria preserve reported evidence. The app never imports or executes your package; passing finite fixtures, reading or a reported green check does not grant mastery or Python expertise. Mutable aliases/concurrent changes, blocked callables, deep immutability and async completion are outside this contract. Advanced context/concurrency/measurement work remains later teaching.
