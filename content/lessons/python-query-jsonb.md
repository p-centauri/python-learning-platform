JSONB is useful for optional metadata with a changing shape. Keep namespace/id/revision in relational columns with constraints and foreign keys. Putting stable identity only inside a JSON object makes it harder to enforce the same relationships. In this lab, query_note stores an object body beside its complete fact key.

A missing key, JSON null and an empty string are different states. The key-existence operator ? distinguishes a missing field from an existing field. The -> operator extracts JSONB; ->> extracts text, which can collapse some distinctions into SQL null. Use the operator that matches the question instead of assuming every extraction preserves the original state.

Containment uses @>. A body matches {"region": null} only when it contains that explicit key/value. It does not match a missing region or region set to an empty string. An object can also contain additional fields. The lab's Filter validates a bounded object with kind/region keys, rejects duplicates and wrong types, and makes an independent canonical copy. It accepts null and bounded printable strings, including empty text.

Bind the JSON document as a parameter and cast that value to JSONB. A label containing a quote must remain data. Do not concatenate it into SQL. The live test inserts a label that looks like SQL and verifies that it matches only its actual fact.

Search semantics also depend on order. First rank each namespace/id's revisions newest first. Select its newest row, then use EXISTS on notes with the complete key and JSONB containment. Several matching notes must not duplicate the fact; an old matching note must not make an old revision current.

## Try a small example

```python
missing: dict[str, object] = {}
explicit: dict[str, object] = {"region": None}
print("region" in explicit and "region" not in missing)
```

Expected output: `True`. This in-memory illustration is separate from database evidence.

## Try it in PostgreSQL

Run this literal example only on your disposable PostgreSQL store; the maintainer verifier evaluates it on PostgreSQL 17.

```sql
SELECT '{"region":null}'::jsonb @> '{"region":null}'::jsonb AS null_match,
'{}'::jsonb ? 'region' AS missing_has_key,
'{"region":""}'::jsonb ->> 'region' AS empty_text;
```

The SQL returns true, false and an empty string.

## Guided practice

Predict the small result before checking it. Use the second checkpoint to diagnose the query or evidence boundary. The diagram and glossary describe the same idea in simple words.

## Independent practice

Implement search.sql. Test equal-value deterministic order, two matching notes, missing current metadata, explicit JSON null, empty strings and another namespace. Keep the final result limit after newest selection and matching. The returned fields are the allowed fact values, not the whole metadata object.

The schema's object/byte CHECK is verified on actual PostgreSQL. That constraint is a stored-value bound, not a network parser or complete authorization rule. The query library assumes the application already authorized its namespace.

Explain why JSONB storage alone does not make a query faster. Match operators to index support and measure the workload separately. A GIN index supports this lab's containment query; it does not automatically optimize every JSON expression or sorting requirement.

## Check your work

State the full scope/key, what each output row means and what the failure case proves. Record the commands you actually ran and any skipped cases. Explain the result in your own words before revisiting private recall with guidance closed.
