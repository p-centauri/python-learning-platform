# Repair an event timeline

This program runs but contains intentional mistakes. Fix `events.py` while preserving the two public functions. Keep the provided CLI contract and tests. Python 3.13+ is required; no third-party packages or named time-zone database are needed for this lab.

```sh
python cli.py sample.json
python -m unittest discover -s tests -v
python -m pdb cli.py sample.json
```

Use your project environment's Python. Expected test failures are the starting point of the exercise. For example, inspect the decoded text with `repr`, compare an event before and after UTC conversion, and inspect the ordering key. In pdb, `n` steps over, `s` steps into, `p expression` inspects, `where` shows the stack, `c` continues and `q` exits.

## Contract

`normalize_label(text)` accepts a string. Strip surrounding whitespace, casefold, then normalize to Unicode NFC. Reject non-string or empty-after-cleaning input with ValueError. Preserve internal whitespace and punctuation. This is a policy for report labels, not an identity or security rule.

`build_timeline(payload)` accepts UTF-8 encoded bytes containing JSON. Decode strictly as UTF-8: never ignore or replace invalid bytes. The top level must be a list. Each item must be an object containing exactly `label` and `timestamp`; both values must be strings. An empty list is valid.

A timestamp may use any form parsed by Python 3.13 `datetime.fromisoformat`, but it must have an explicit usable offset. Date-only and naive values are rejected. No surrounding-whitespace cleanup is promised for timestamps. This is not a strict RFC 3339 validator. Impossible dates and UTC conversion overflow must be reported as ValueError with record context.

Normalize labels and convert each instant to UTC. Return a new list of dictionaries with `label` and `timestamp`. Format timestamp using UTC datetime.isoformat(), including `+00:00` and fractional seconds when needed. Order events from earliest to latest. Preserve every record, including duplicates, and preserve input order for equal instants. Each call must be independent.

For record errors, raise ValueError mentioning the one-based record number. Invalid UTF-8 or JSON and a non-list top level must fail (ValueError subclasses are acceptable). Never return a partial list when a later record is invalid. The function is intended for small local files; it loads the JSON document in memory and is not a streaming large-data service.

The supplied CLI accepts one file path. Success: exit 0, one JSON document on stdout, no stderr. Expected invalid input/file failure: exit 2, nonempty stderr and empty stdout. It must work from another working directory with absolute script/input paths. Importing modules must not execute the command.

## Repair process

1. Record the sample's incorrect behavior and run the tests.
2. Reduce one failed case to a tiny input. Inspect the relevant value and transformation.
3. Fix the cause; run that test, then the whole suite. Preserve the expected contract.
4. Add at least two new regression tests and a short bug diary explaining symptoms, causes and fixes.
5. Compare the sample against expected.json as parsed values, not formatted whitespace.

The supplied tests are public acceptance examples, not exhaustive grading. Show a reviewer your fixes, added cases, and why converting a timestamp differs from relabelling it. Explain how you avoid text corruption and preserve repeated events. Checklists in the academy are self-reported; the app does not execute or grade this code. The expense-tracker starter remains a separate project with its own unchanged label rules.
