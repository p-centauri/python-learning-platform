## The idea in plain language

An envelope is the message shape around a fact. Its schema number tells the reader how to interpret that shape. The fact's identity has a different purpose: namespace, id and revision still identify the same event after a wire-format change.

Version one in this lab puts all fields beside schema. Version two groups identity into key and the value into data, with kind reading. Both become the same existing Event. A compatible reader explicitly understands both shapes; a new publisher defaults to version two. The lab does not rewrite old messages or pretend to understand every future version.

Validate before applying an effect. Accept exact bytes with a 1024-byte parser limit, decode UTF-8, reject duplicate JSON field names at every level and reject non-finite constants. Then require the supported version's exact keys, kind, value types and ranges. An extra field is rejected under this contract instead of silently ignored. A JSON true is not an integer revision.

Compare the payload namespace with the authorized stream namespace. A valid-looking event from another scope must not be applied. Authorization itself belongs to the surrounding application; a matching field is not a login credential.

Unknown versions and malformed shapes remain pending for inspection. They are not successful effects and must not be acknowledged as if they were. Later operational tooling can define repair or quarantine with its own audit and acceptance policy.

The small parser guard follows retrieval by the Redis client. One requested entry can still contain a large hostile wire payload before validation. This trusted local lab does not establish complete hostile-network memory protection.

## Worked example

This local illustration explains one boundary. Actual broker/database/process evidence comes from the lab.

```python
version_one_key = ("scope", "a", 1)
version_two_key = ("scope", "a", 1)
print(version_one_key == version_two_key)
```

## Guided practice

Choose a supported exact shape. Check bytes, fields, types, ranges and authorized scope. Map supported shapes to the same Event key.

## Independent practice

Implement or inspect the matching lab contract. Save an actual before/after observation and explain the stable key, current transport state and failure boundary.

## Check your work

Wire shape and stable fact identity have different purposes. Unsupported schemas must not produce guessed effects or success acknowledgments. Label offline skips, modeled failures, actual process exits and controlled restarts honestly.

Continue to [Confirm broker acceptance before completing the producer job](/lessons/python-stream-acceptance).
