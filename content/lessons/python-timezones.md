## Convert the clock reading; do not relabel it

This is lesson 4 of 5. A UTC offset says how far a clock reading is from UTC at that moment. To express the same instant in another zone, use `astimezone`. Using `replace(tzinfo=...)` changes attached information without converting the clock fields.

```python
from datetime import datetime, timedelta, timezone

source = datetime.fromisoformat("2024-06-01T12:00:00+05:00")
converted = source.astimezone(timezone.utc)
relabelled = source.replace(tzinfo=timezone.utc)
assert converted.hour == 7
assert relabelled.hour == 12
assert converted == source
assert relabelled != source
```

That five-hour difference is not cosmetic. Relabelling can move an event to the wrong part of a timeline. Attaching a zone to a naive reading is only appropriate when its source zone is already known and any ambiguity is resolved; it is not a generic conversion method.

## A named zone contains changing rules

`ZoneInfo("Europe/Berlin")` uses a named region's historical rules, including seasonal clock changes. A fixed `+01:00` offset does not mean “Berlin all year.” Python's zoneinfo uses installed IANA time-zone data. Some systems, especially Windows, may need the `tzdata` package in the project environment. If a named zone is unavailable, report that requirement rather than substituting a guessed offset. The repair lab uses explicit offsets and needs no named-zone database.

On a machine with the data installed, try this separately:

```python
from zoneinfo import ZoneInfo

berlin = ZoneInfo("Europe/Berlin")
summer = datetime(2024, 7, 1, 12, tzinfo=timezone.utc).astimezone(berlin)
assert summer.utcoffset() == timedelta(hours=2)
```

A local clock time can occur twice when clocks move backward, or not exist when they move forward. The `fold` attribute distinguishes the repeated occurrence; it does not by itself validate nonexistent local times. For a recurring appointment, retain its named zone and decide how these cases should behave. The beginner lab avoids that scheduling problem by requiring explicit offsets.

## Measure duration with the right clock

For elapsed time between stored events, convert both aware values to UTC before subtracting them. This is especially useful across a daylight-saving change: subtracting datetimes sharing the same zone object can follow wall-clock arithmetic rather than the elapsed timeline you meant.

For timing work in the current process, use a monotonic clock such as `time.perf_counter()`. Calendar time can jump if the system clock is adjusted; a monotonic clock is intended for measuring differences, not producing event timestamps. Do not save its arbitrary starting point as a calendar date.

## Guided practice

Compare `10:00+05:00` and `06:00+00:00` on the same day. Convert both to UTC before deciding which happened first. Then try sorting their original strings and explain why a text ordering is not the same question.

## Independent task

Compute elapsed seconds between `2024-10-27T02:30:00+02:00` and `2024-10-27T02:30:00+01:00`. Write a test for the result and one for equal instants using different offsets. Keep this calculation separate from any display formatting.

## Check your work

The first pair is one hour apart even though the local clock fields match. Equal instants must give zero elapsed seconds. In the timeline lab, normalize to UTC and sort by those datetime values while preserving ties.

[Next: debugging and the repair lab](/lessons/python-debugging)
