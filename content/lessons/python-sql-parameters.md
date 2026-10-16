## The idea in plain language

Pass SQL text and values through separate arguments. In Psycopg 2, use unquoted %s placeholders for values and a tuple/list as the second execute argument. A single value needs (value,), including the comma. The placeholder remains %s even for integer values; it is not Python string interpolation.

For example, cursor.execute("SELECT value FROM feed_record WHERE namespace=%s AND id=%s AND revision=%s", (namespace, id, revision)) binds the values. Never build a query with f-strings, percent formatting or string concatenation of caller values. A quote in O'Reilly should remain data rather than break SQL syntax. The lab tests punctuation-shaped input using SELECT %s::text and proves the table still exists.

Values and identifiers are different. A table/schema/column name is SQL structure, not a value placeholder. For trusted chosen identifiers use psycopg2.sql.SQL with Identifier; do not let arbitrary callers choose database objects. The supplied fixtures generate their own unique schema and use Identifier to install/drop only that schema. Runtime functions use fixed table names under a caller-configured trusted search_path.

Parameter binding prevents values from becoming SQL structure. It does not authorize access, validate domain ranges, choose a safe search_path or guarantee a query is cheap. Input validation still matters; database privileges and service authorization need their own design. Keep the DSN in local configuration and exclude credentials from evidence.

The worked example constructs separate SQL/value channels without sending a query. Actual driver and PostgreSQL behavior is evaluated in the lab; a string-only assertion would be insufficient evidence.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
statement = "SELECT %s::text"
value = "O'Reilly'); DROP TABLE feed_record; --"
parameters = (value,)
print(statement)
print(len(parameters), parameters[0] == value)
```

## Apply it in the PostgreSQL lab

This requires a real Psycopg connection; it is not executed by the local illustration. The public PostgreSQL test runs this value-binding boundary and then confirms feed_record still exists.

```text
# With an idle, caller-owned connection in the disposable lab:
text = "O'Reilly'); DROP TABLE feed_record; --"
with conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT %s::text", (text,))
        echoed = cursor.fetchone()
        assert echoed == (text,)
# The cursor closed and transaction committed; conn remains open.
```

## Guided practice

Identify SQL structure and values. Explain the one-element tuple and why an identifier cannot use a value placeholder.

## Independent practice

Implement fixed parameterized inserts/reads. Run the punctuation binding case and a raw constraint violation on PostgreSQL.

## Check your work

No interpolation of caller values. Fixed identifiers and bound values still need authorization and a trusted schema.

Continue to [Transactions need one clear owner](/lessons/python-transaction-owners).
