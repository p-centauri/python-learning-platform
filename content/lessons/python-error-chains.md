## Explain which operation failed and keep the cause

This is lesson 4 of 5. A parser should identify the bad record without turning every programming mistake into a data error. Catch the expected low-level failure near the operation that can produce it, then add useful context.

```python
class RecordError(ValueError):
    pass

def parse_duration(text: str, line: int) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise RecordError(f"line {line}: invalid duration") from exc
    if value < 0:
        raise RecordError(f"line {line}: negative duration")
    return value

assert parse_duration("12", 1) == 12
try:
    parse_duration("twelve", 4)
except RecordError as error:
    assert str(error) == "line 4: invalid duration"
    assert isinstance(error.__cause__, ValueError)
else:
    raise AssertionError("invalid input was accepted")
```

`raise ... from exc` retains the original exception as the cause. A caller can present the shorter domain message, while a traceback still explains the underlying failure. The simple conversion above has its own rules: `int` accepts forms such as surrounding whitespace. The project instead accepts JSON integers and applies a separate range rule.

A custom error gives callers a stable category to handle. A user input problem should not require matching fragments of a traceback. Keep messages specific, but avoid copying entire private records into shared logs. A line number and a concise reason are often enough.

## Cleanup must not hide failure

`finally` runs when control leaves a try block during normal execution or exception propagation. Use it for cleanup that must happen along both paths. A `return` from finally can replace a pending return or suppress an error, so avoid it. If cleanup itself raises, it can become the visible failure; keep the original context available for diagnosis.

Do not catch `BaseException` just to print success. Interrupts and process exit are different from expected malformed records. Even `except Exception` is too broad if it turns unrelated bugs into skipped rows.

## Guided practice

Run the example with a bad value on line 4 and inspect both the custom message and cause. Add a narrow handler around the consuming loop of a generator version. Confirm that bad input found later in the stream still reaches that handler.

## Independent task

Create a bytes-to-JSON record parser. Convert UnicodeDecodeError and JSONDecodeError into RecordError with a one-based line number, preserving the original cause. Keep field-validation failures separate from decoding failures. Reject a blank record instead of silently skipping it.

## Check your work

Use invalid UTF-8, malformed JSON, a valid object with the wrong fields, and a good record followed by a bad one. A failure must retain its actual position. Ensure your wrapper does not catch an unrelated error in a later processing stage.

[Next: context managers and the streaming lab](/lessons/python-context-managers)
