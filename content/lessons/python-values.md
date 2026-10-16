## Values have types

This is lesson 2 of 9. External input often arrives as text. Python does not silently turn text into a number just because you want to add it. Start by asking what kind of value you have: a string (`str`), integer (`int`), decimal number, boolean (`bool`), or the special missing-value marker `None`.

```python
text = "250"
cents = int(text)
print(cents + 50)
assert cents + 50 == 300
```

This prints 300. `"250" + "50"` would join the strings into `"25050"`. `"250" + 50` raises TypeError because text and integer addition are different operations. Conversion is an explicit decision, and `int("lunch")` fails with ValueError rather than inventing a number.

## Give amounts a clear rule

Our expense tracker uses a single imaginary currency with two decimal places. It accepts amounts such as `12`, `12.3` and `12.30`, then stores integer cents: 1200, 1230 and 1230. It rejects negatives and amounts with more than two decimal places. Zero is valid. These are this project's rules, not rules for all currencies or financial systems.

```python
whole = 12
fraction = 30
amount_cents = whole * 100 + fraction
assert amount_cents == 1230
assert 1230 + 275 == 1505
```

Integer addition keeps these totals exact. Avoid `int(float(text) * 100)` for this project: binary floating-point can introduce small differences before conversion. We will split and validate the original text in the functions lesson. For more complex decimal calculations, Python also provides Decimal; you do not need it for this bounded exercise.

## Missing and zero are different

```python
limit = 0
chosen = 100 if limit is None else limit
assert chosen == 0
```

Zero is a real number, while None means no value was supplied. `limit or 100` would replace zero because zero counts as false in a condition. Use an explicit None check when that difference matters. `/` performs division; `//` gives floor division, and `%` gives the remainder. For non-negative cents, `cents // 100` and `cents % 100` separate whole units and cents.

## Guided practice

Represent two expenses, 4.25 and 1.50, as integer cents. Add them and split the total into whole units and remaining cents. The total should be 575 cents: five units and 75 cents. Predict the result before running the code.

## Independent task

For 0, 99, 100 and 10005 cents, produce readable text with exactly two digits after the dot. Try `f"{cents // 100}.{cents % 100:02d}"`. The `02d` means an integer padded with zeros to at least two digits. Explain why treating zero as missing would be a bug.

## Check your work

Your outputs should be `0.00`, `0.99`, `1.00` and `100.05`. No float is needed. The aim is to choose and explain a representation, not memorize a formatting trick. Complete the practice exercises, then continue to text and collections.

[Next: text and collections](/lessons/python-collections)
