## Let the data choose the next step

This is lesson 4 of 9. An `if` chooses between branches. A `for` loop visits each item. Indentation tells Python which statements belong inside a branch, loop or function. Use four spaces consistently; mixing tabs and spaces makes code hard to read and can cause errors.

```python
amounts = [250, 0, 175]
labels = []
for amount in amounts:
    if amount == 0:
        labels.append("free")
    else:
        labels.append("paid")
assert labels == ["paid", "free", "paid"]
```

The comparison uses `==`; assignment uses `=`. A colon starts each block. The final assertion is outside the loop, so it runs after all three amounts have been processed.

## Accumulate one category at a time

```python
rows = [("food", 250), ("travel", 175), ("food", 100)]
totals = {}
for category, cents in rows:
    previous = totals.get(category, 0)
    totals[category] = previous + cents
assert totals == {"food": 350, "travel": 175}
```

Start with an empty dictionary. On the first food expense, there is no total, so use zero. On the second food expense, add to 250 rather than starting again. Keep `totals = {}` outside the loop; putting it inside would erase earlier work.

A comprehension is a compact way to build a collection, such as `[n * 2 for n in [1, 2]]`. Use a normal loop when several validation steps need readable error messages. Shorter code is not automatically clearer.

## Empty input is still input

If `rows` is empty, the loop runs zero times and the totals stay empty. This is a useful default. For our project, a CSV with a correct header and no expenses produces a zero total and zero rows. A file with no header is a different input error.

Use `enumerate(rows, start=2)` to attach logical record numbers after a header. `continue` skips the rest of the current iteration, while `break` ends the loop. Our project's rule is to stop the whole report on an invalid record, not quietly skip it. Choose control flow from that rule rather than from convenience. A `while` loop repeats while a condition is true; ensure its state eventually changes so it can stop.

## Guided practice

Walk through the totals example on paper. Write down the dictionary after each row. Then add a zero-valued food expense and confirm the total stays 350 while the number of expenses increases.

## Independent task

Count how many expenses belong to each category. Use the same pattern, but add one for each row instead of adding cents. Test empty input, one row, and two rows in the same category. Do not remove items from a list while looping over it; build a new collection when filtering is needed.

## Check your work

The original example should produce counts of food: 2 and travel: 1. Empty input should produce `{}`. Explain why the starting value belongs before the loop and why each row must update the existing value.

[Next: functions and amount validation](/lessons/python-functions)
