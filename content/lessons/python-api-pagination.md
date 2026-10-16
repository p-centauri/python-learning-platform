## The idea in plain language

A page contract needs an order, a limit and a continuation position. Without ORDER BY there is no application promise about row order. This lab orders C-collated ASCII id, then revision. Both fields matter because several revisions can share one id.

The cursor is the last returned id/revision. The next query always filters the authorized namespace, then id greater than cursor id OR equal id and revision greater than cursor revision. The driver binds those values. Fetch limit+1 rows: return at most limit, and emit a next cursor only when one extra row demonstrates more data. Returning a cursor just because the page was full can invent a next page.

The API accepts canonical query strings for limits from 1 to 32 and paired cursor fields. HTTP query values begin as text; the API deliberately validates this syntax before converting an integer. Body JSON has a different strict integer policy. Incomplete/malformed cursor fields yield a 422 response rather than guess what the caller meant.

An unsigned cursor is not authorization and should not be treated as tamper-proof. Clients can choose a different position within their own permitted namespace; they still cannot read another namespace. Every page repeats permission checking and namespace SQL filtering. Signing a cursor can preserve format/state integrity but does not replace resource permission.

Keyset pagination over changing data is not a frozen snapshot. A newly backfilled key behind an already-used cursor can be missed. This append-only fixed-fixture lab makes no complete concurrent snapshot guarantee. Later work should choose snapshot/version rules if that matters. A page limit also does not bound all database scanning/planning/latency; index/EXPLAIN evidence comes separately.

The local example shows the complete key ordering. Actual PostgreSQL API tests verify equal-id revisions, the extra-row rule, no duplicate fixed-fixture pages, empty results and forbidden/crafted positions.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
keys = [("b", 1), ("a", 2), ("a", 1)]
ordered = sorted(keys)
print(ordered[:2])
print([key for key in ordered if key > ("a", 2)])
```

## Guided practice

Trace full-key order, namespace scope, continuation predicate and the extra row. Explain fixed-fixture results versus a changing dataset.

## Independent practice

Implement read_page and follow real API pages. Try paired/unpaired cursors, exact-full/final pages and another namespace.

## Check your work

Positions are not permission; count limits are not query deadlines or a stable concurrent snapshot.

Continue to [Service failure evidence & the ingestion API lab](/lessons/python-service-evidence).
