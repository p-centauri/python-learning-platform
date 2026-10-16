## Text is not the same as bytes

This is lesson 1 of 5 in **Python in practice: text, time & debugging**. Complete the foundations module first. This module ends with repairing an event-timeline program: the files look reasonable, but names are corrupted and events appear in the wrong order.

A Python `str` represents text. A `bytes` value represents a sequence of numbers from 0 to 255, such as data read from a file or network. An encoding tells us how to convert between those numbers and text. UTF-8 is the encoding required by our lab.

```python
name = "café"
wire = name.encode("utf-8")
assert len(name) == 4
assert len(wire) == 5
assert wire.decode("utf-8") == name
```

`encode` turns text into bytes; `decode` turns bytes into text. Some characters need several bytes, so counting bytes does not count letters. Even `len(text)` counts Unicode code points, not always the visible symbols a person would count. Cutting raw bytes at an arbitrary position can split an encoded character.

## Do not hide broken input

```python
try:
    b"\xff".decode("utf-8")
except UnicodeDecodeError:
    invalid = True
else:
    invalid = False
assert invalid
```

Decoding with `errors="ignore"` would discard invalid bytes. That may hide data loss rather than fix the source. In this lab, reject invalid UTF-8 with a useful error. Decode once at the input boundary, then keep working with text. Encode again only when writing bytes.

## Equal-looking labels may differ

```python
import unicodedata

first = "café"
second = "cafe\u0301"
assert first != second
assert unicodedata.normalize("NFC", first) == unicodedata.normalize("NFC", second)
assert "Straße".casefold() == "strasse"
```

The second spelling stores the accent separately. NFC is a normalization form that gives canonically equivalent spellings a consistent representation. `casefold()` supports more case-insensitive comparisons than `lower()`. Neither operation proves that two user identities are the same, and normalization should not be applied blindly to passwords or legal names.

Our lab has an explicit label rule: strip surrounding whitespace, casefold, then normalize to NFC. Reject a label that becomes empty. Keep punctuation and internal spaces. This is a reporting policy, not a universal rule for every text field.

## Guided practice

Print `repr(first)`, `repr(second)` and their lengths. Normalize both, then compare again. Decode the UTF-8 bytes with latin-1 and inspect the wrong-looking result. A successful decode does not prove you chose the right encoding.

## Independent task

Write `normalize_label(text)` following the lab's rule. Check padded text, `Straße`, the two café spellings, and whitespace-only input. Reject non-string input with ValueError instead of silently converting it with str.

## Check your work

Both café spellings should produce the same label, and `Straße` should become `strasse`. The input bytes must either decode correctly or produce an error. You should be able to explain which change handles encoding and which change handles text comparison.

[Next: collection patterns](/lessons/python-collection-patterns)
