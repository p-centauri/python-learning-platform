## Give each piece of data a place

This is lesson 3 of 9. A list keeps a sequence of items. A dictionary connects keys to values. A tuple represents a fixed sequence. A set keeps unique values and is useful for membership checks. Choose the structure that matches what the program must do.

```python
rows = [
    {"category": "food", "amount_cents": 425},
    {"category": "travel", "amount_cents": 150},
]
assert rows[0]["amount_cents"] == 425
assert len(rows) == 2
categories = {row["category"] for row in rows}
assert categories == {"food", "travel"}
```

Positions start at zero. The first expense is `rows[0]`. A missing dictionary key raises KeyError; `row.get("note", "")` is useful when a field is genuinely optional. Do not use a default to hide a missing required amount. `in` checks dictionary keys, list values, or set members depending on the collection.

## Clean text deliberately

```python
raw = "  Food  "
category = raw.strip().lower()
assert category == "food"
assert raw == "  Food  "
```

Strings cannot be changed in place. These methods return new strings, so keep their return value. In this project, category names have surrounding whitespace removed and are converted to lowercase. An empty result is invalid. We do not silently change internal spaces or remove punctuation: `"food, snacks"` is a valid category.

Python text is Unicode. A file contains bytes, which need an encoding to become text. Use UTF-8 explicitly for this project's files. Do not assume one visible character always equals one byte. The CSV library, taught later, handles commas inside quoted fields; splitting every line on a comma would lose that structure.

## Watch for shared objects

```python
first = ["food"]
second = first
second.append("travel")
assert first == ["food", "travel"]
separate = list(first)
separate.append("books")
assert "books" not in first
```

Assignment gives the same list another name. `list(first)` makes a new outer list. With nested dictionaries or lists, inner values can still be shared. The existing ownership lesson explores that next level of detail.

## Guided practice

Add a books expense to `rows`, then read its category and amount. Build a set of categories and explain why it can contain fewer items than the expense list. Two food purchases are two expenses but only one category.

## Independent task

Create three expense dictionaries, including two with the same category. Normalize their category text and build a list of normalized categories plus a set of unique categories. Keep the raw input dictionaries unchanged by creating new values rather than editing them.

## Check your work

The list should keep all three entries, while the set has only the distinct names. Empty categories need a clear error later; they should not become an invented category. Test one category containing non-ASCII text, such as `café`, and confirm it remains readable.

[Next: decisions and loops](/lessons/python-control-flow)
