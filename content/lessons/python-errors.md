## An error is information

This is lesson 6 of 9. A traceback shows the calls that led to a failure. Read the final exception type and message, then find the relevant line in your own code. A SyntaxError means Python could not understand the program; an exception such as ValueError happens while understood code is running.

```python
def read_count(text):
    try:
        count = int(text)
    except ValueError as exc:
        raise ValueError("count must be a whole number") from exc
    if count < 0:
        raise ValueError("count cannot be negative")
    return count

assert read_count("3") == 3
assert read_count("0") == 0
```

The `try` contains the operation expected to fail. `except ValueError` handles that particular conversion error. `from exc` keeps the original failure attached so a developer can inspect the cause. A successful conversion still needs the negative-value check: reading a value and deciding whether it is allowed are separate steps.

## Add context without hiding the failure

An error saying “invalid amount” is more useful when it also says which expense was invalid. Catch the conversion error near the row boundary and raise a message such as `record 3: amount needs digits`. A record number counts CSV records, not necessarily physical lines: one quoted field may contain a newline.

Do not use `except Exception: return 0` in a parser. That can hide a typo, a missing dictionary key or a bug in your program. Worse, it turns failure into an apparently valid amount. At the command-line boundary, catch expected input and file errors, print a short message to stderr, and return a nonzero exit status. Unexpected programming bugs should remain visible during development.

## Reproduce before guessing

Make the smallest input that still fails. Check values with `print(repr(value))` when invisible spaces may matter. For longer investigations, use `breakpoint()` to pause and inspect the program locally. Remove temporary debugging prints from a CLI that promises JSON on stdout: extra text would break its output contract. Do not paste private input into shared logs.

## Guided practice

Call `read_count("three")` in a separate script and read the traceback. Then call `read_count("-1")`. The first fails during conversion; the second fails the rule after conversion. Explain why both are errors even though their causes differ.

## Independent task

Wrap the category function from the previous lesson with a record number. If record 4 has an empty category, raise a message that includes `record 4` and `category`. Keep the original ValueError as the cause. Test it with a small try/except block that checks the message rather than swallowing the failure.

## Check your work

Good input still returns a value. Bad input never becomes an invented zero or category. For the expense tracker, one invalid record stops the report: there must be no partial success JSON on stdout. That rule will guide when we print the completed report.

[Next: files, CSV and JSON](/lessons/python-files)
