## A date, a local reading and an instant differ

This is lesson 3 of 5. A `date` gives a calendar day. A `datetime` gives a date and a clock reading. An aware datetime also has time-zone information that can identify an instant. A naive datetime lacks that information; do not silently assume it means the server's local zone or UTC.

```python
from datetime import date, datetime, timedelta, timezone

day = date.fromisoformat("2024-02-28")
assert day + timedelta(days=1) == date(2024, 2, 29)
local_reading = datetime.fromisoformat("2024-02-29T10:00:00")
assert local_reading.tzinfo is None
known_instant = datetime.fromisoformat("2024-02-29T10:00:00+05:00")
assert known_instant.utcoffset() == timedelta(hours=5)
```

Let calendar types handle month lengths and leap years. Adding one to the text's day number does not know whether February has ended. A timedelta describes a duration; it is not a “calendar month” unit.

## Parse, then enforce your rule

The timeline lab accepts timestamp strings understood by Python 3.13's `datetime.fromisoformat`, provided they include usable offset information. It is deliberately not a strict RFC 3339 validator. A successfully parsed date-only string is still not enough for an event instant. The lab rejects naive values rather than guessing their zone.

```python
def require_instant(text):
    value = datetime.fromisoformat(text)
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp needs a UTC offset")
    return value

value = require_instant("2024-06-01T12:00:00+05:00")
assert value.astimezone(timezone.utc).hour == 7
```

Parsing checks whether Python understands the representation. Your application must still decide whether it is suitable for the task. For malformed input, keep the record number and the field name in the error. Do not replace failed parsing with today's date: that creates convincing but incorrect data.

## Format at the output boundary

Use `.isoformat()` when producing machine-readable timestamp strings. For the lab, first convert to UTC, then call isoformat. The result should use `+00:00`; the default formatting keeps fractional seconds when needed. For a display such as “day/month/year,” an explicit format may be appropriate, but that display string is a poor internal value for arithmetic or ordering.

Dates such as `03/04/2024` are ambiguous without an agreed format. If a product accepts those strings, document whether day or month comes first. Avoid letting the current machine's regional settings silently choose the contract.

## Guided practice

Parse `2024-02-30` as a date and inspect the error in a small separate script. Then compare two aware timestamps that represent the same instant with different offsets. Explain why the printed hour alone does not identify when an event occurred.

## Independent task

Write a function that accepts an offset-aware ISO timestamp and returns its UTC ISO string. Test a positive offset, a negative offset, `Z`, missing offset information and an impossible date. Treat bad input as an error, not a request to use the current time.

## Check your work

`2024-06-01T12:00:00+05:00` must become `2024-06-01T07:00:00+00:00`. The function should produce the same output regardless of your machine's local time zone. Next we will explain conversion versus simply changing the time-zone label.

[Next: time zones and elapsed time](/lessons/python-timezones)
