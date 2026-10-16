## Turn a symptom into a small failing example

This is lesson 5 of 5. Debugging is the process of finding why actual behavior differs from the promised behavior. Start by writing both down. “The report is wrong” is vague; “a 10:00+05:00 event appears after a 06:00+00:00 event” points to a specific rule you can test.

```python
from datetime import datetime, timezone

def utc_text(text):
    value = datetime.fromisoformat(text)
    return value.astimezone(timezone.utc).isoformat()

assert utc_text("2024-06-01T10:00:00+05:00") == "2024-06-01T05:00:00+00:00"
```

This worked example assumes valid offset-aware input. The lab still needs validation for missing fields, wrong types and missing offsets. First reproduce one bug with a tiny input, then fix the cause. Keep the failing case as a regression test so a later edit cannot quietly bring the bug back.

## Inspect instead of guessing

For unexpected text, `repr(value)` exposes escapes and whitespace. Inspect `type(value)` when a function may be receiving bytes instead of str. For dates, inspect the value, its `tzinfo`, and its `utcoffset()`. Avoid printing private input or tokens into shared logs.

A debugger lets you pause before a suspicious statement. In your local copy, run `python -m pdb cli.py sample.json`. At the `(Pdb)` prompt, `n` runs the next line, `s` steps into a call, `p expression` prints a value, `where` shows the call stack, `c` continues, and `q` quits. You can also insert `breakpoint()` at a useful line. Step into `build_timeline`, inspect the decoded text, and follow one parsed timestamp to its UTC conversion. Remove temporary breakpoints before handing in the program.

## Guided practice

[Download the event-timeline repair lab](/api/projects/python-event-timeline/starter). Run `python cli.py sample.json`, then `python -m unittest discover -s tests -v`. Unlike the first project's unfinished functions, this starter runs and contains deliberate bugs. A plausible output is not proof of correctness. Compare parsed output with `expected.json` and read the named test failures.

Locate the faulty transformation before changing it. Fix one failure, rerun its test, then run the whole suite to look for a broken neighboring behavior. Do not change expected results to agree with incorrect code.

## Independent repair task

Repair UTF-8 decoding, label normalization, timestamp conversion and ordering. The exact README contract is authoritative. Keep every event and preserve input order for equal instants. Reject bad records with their position in the error; never return partial success after a later record fails. The final solution should run with only the standard library.

Add at least two tests of your own and write a short bug diary: symptom, smallest reproduction, cause, change and test. Your code runs locally. The academy does not execute it or certify a repair from checked milestones.

## Explained approach and finish check

Decode bytes once, parse JSON, validate the top-level list and each record, then build a fresh list of normalized records. Use aware datetimes for conversion and ordering; format strings only for output. A stable sort keeps equal-instant records in input order. Review invalid input as well as happy paths and run the command from another working directory.

Use the [project checklist](/projects#python-event-timeline) to track your evidence. Once this module is understood, continue to [references, mutation and ownership](/lessons/python-ownership) before deeper intermediate object design and typing.
