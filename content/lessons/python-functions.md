## Give a function one clear job

This is lesson 5 of 9. A function receives inputs and returns a result. Keeping calculation separate from printing makes the calculation easier to test and reuse. Local names belong to that function call unless you deliberately use a different scope.

```python
def format_cents(cents):
    return f"{cents // 100}.{cents % 100:02d}"

assert format_cents(425) == "4.25"
assert format_cents(0) == "0.00"
```

`return` sends a value back to the caller. `print` displays a value and returns None. If you replace return with print here, the screen may look right but the assertions fail because the caller receives None. This formatter assumes a non-negative integer; validation belongs where external text enters the program.

## Validate before converting

Our project's accepted amount text is: ASCII digits, optionally followed by a dot and one or two digits. Surrounding whitespace is ignored. Negative signs, currency symbols, commas, scientific notation and an empty fractional part are rejected. Leading zeros are allowed. Put these rules in one function:

```python
def parse_amount(text):
    cleaned = text.strip()
    parts = cleaned.split(".")
    if len(parts) > 2:
        raise ValueError("amount has too many dots")
    whole = parts[0]
    fraction = parts[1] if len(parts) == 2 else ""
    if not whole or any(ch not in "0123456789" for ch in whole):
        raise ValueError("amount needs digits before the dot")
    if len(parts) == 2 and (
        not 1 <= len(fraction) <= 2
        or any(ch not in "0123456789" for ch in fraction)
    ):
        raise ValueError("amount needs one or two digits after the dot")
    return int(whole) * 100 + int(fraction.ljust(2, "0"))

assert parse_amount("12.3") == 1230
assert parse_amount(" 0 ") == 0
```

`ljust(2, "0")` adds zeros on the right: `"3"` becomes `"30"` and an empty string becomes `"00"`. Validate first so a malformed amount cannot be mistaken for a legitimate zero. The project accepts strings at this boundary; it does not promise to accept arbitrary Python objects.

## A common mistake

Do not store totals in a module-global dictionary or a mutable default argument. Two calls should not share results unless that sharing is part of the function's contract. Create fresh state inside the summary function. A function with a default such as `rows=[]` reuses that list across calls; prefer an explicit argument or a None default when needed.

## Guided practice

Trace `parse_amount("4.05")`: whole is `"4"`, fraction is `"05"`, and the returned value is 405. Then trace `"4.005"` and identify the branch that rejects it. Read the error instead of catching everything and returning zero.

## Independent task

Write `normalize_category(text)` that strips outside whitespace, converts to lowercase, and raises ValueError when the result is empty. Keep internal spaces and commas. It should return `"food, snacks"` for `" Food, Snacks "` without modifying any caller-owned dictionary.

## Check your work

Try valid text, whitespace-only text and a non-ASCII category. A useful function contract states accepted input, returned output, and the error for bad input. Next we will add that error to a helpful message for the user.

[Next: errors and debugging](/lessons/python-errors)
