A practical review asks whether several correct ideas still work when connected. This project reads the earlier ingestion service, creates an immutable latest-value report and computes an audit fingerprint for requested positions. You implement three functions: decode_page, prepare and analyse. The supplied asynchronous client, profiling tools and worker rehearsal make the contracts observable. The academy serves the starter and saves reported/manual evidence; it never runs your package inside its API.

Start by naming the boundaries. The old service returns exactly items and next_cursor. Each item has id, revision and value, with values from zero to one million. decode_page checks this public shape, copies values into exact Datum objects, requires ordered full keys and verifies that a non-null cursor names the last returned item. It must not silently accept an added private field, coerce true into 1 or confuse value zero with missing data. Reading a page does not grant permission; the server still checks the configured bearer and namespace.

prepare borrows up to 256 source rows, checks every full id/revision key for conflicts, then selects the highest revision for each id and sorts at most 64 selected items. Validate old revisions too: choosing the latest first must not hide conflicting historical input. The previous Python value libraries accept only zero through 60000. Keep that narrower contract. A valid service value of one million can be decoded but must be refused at the reporting adapter rather than clamped or used to widen an older library.

Snapshot, Record, typed map_rows and Row keep their earlier public rules. The report stores no live ORM object, borrowed response or mutable input list. The cache belongs to one analysis call and holds at most eight immutable fingerprints, with namespace/id/revision keys. The batch is frozen; another invocation starts fresh. This is a local pure-computation cache, not a permission mechanism or a promise that mutable database data will stay current.

## Guided practice

Predict the printed value, then explain which boundary this small illustration leaves unevaluated.

```python
rows = [("a", 1, 9), ("a", 8, 0), ("b", 3, 7)]
latest: dict[str, tuple[int, int]] = {}
for name, revision, value in rows:
    if name not in latest or revision > latest[name][0]:
        latest[name] = (revision, value)
print(latest["a"][1])
```

## Independent practice

Implement decode_page and prepare. Test zero, revision gaps, unsorted input, equal duplicates, conflicts in an obsolete revision, exact service output and values beyond the earlier library domain. Explain which function rejects each case.

## Check your work

Show preserved service values before adapter refusal. Compare copied objects after changing the input list. The small dictionary illustration does not prove transaction snapshots or service permissions.

Use the [Composed Python practical review project](/projects#python-practical-review). Record actual commands and outcomes, preserve the submitted version and keep credentials private.
