## Two names can share one object

A Python variable is a name for an object. Giving that object another name does not copy it. If the object is a list, changes made through one name are visible through the other name.

```python
items = ["paid"]
other = items
other.append("exported")
assert items == ["paid", "exported"]
```

Think of two labels on the same box. Adding something through either label changes the same box. This matters when several requests use the same cached data.

## A copy can still share inner values

```python
original = {"tags": ["paid"]}
copied = original.copy()
copied["tags"].append("exported")
assert original["tags"] == ["paid", "exported"]
```

Here, `copy()` creates a new dictionary, but both dictionaries still point to the same inner list. This is called a **shallow copy**: only the outer object is copied.

If this request needs its own tags, copy that list too:

```python
request_data = {**original, "tags": list(original["tags"])}
request_data["tags"].append("request-only")
assert "request-only" not in original["tags"]
```

This works for the list of strings shown here. If the list contains other lists or dictionaries, those inner objects can still be shared. `copy.deepcopy` can copy ordinary nested data, but it is not a good way to duplicate database connections or open files. Decide which data each request owns and is allowed to change.

## A default list is reused

```python
def collect_failed(job_id, failures=[]):
    failures.append(job_id)
    return failures
```

Python creates the default list once when it defines the function. The second call therefore sees items left by the first call. This can happen even when there are no threads or async tasks.

Create a fresh list for calls that do not supply one:

```python
def collect_failed(job_id, failures=None):
    if failures is None:
        failures = []
    failures.append(job_id)
    return failures

assert collect_failed("first") == ["first"]
assert collect_failed("second") == ["second"]
```

If the caller deliberately supplies a list, this version changes that supplied list. Document that behavior so it is not a surprise.

## Async tasks can share data too

At `await`, another task may get a turn to run. If you read a balance, wait for a network call, and then update that balance, the value may have changed while you waited.

An `asyncio.Lock` can make tasks using the same lock take turns. It only coordinates those tasks in the same event loop. It cannot protect a second server process. For data shared across servers, use a suitable database transaction or an update that checks the expected old value.

## Try it in code

Imagine a cached configuration contains a list of permissions. One request adds a temporary permission to that list. The next request then sees it too, because both requests used the same list.

Write a small function that builds request-specific permissions without changing the cached list. Test two requests in sequence. Check that the second request never gets the first request's extra permission. Then explain which objects are shared and which are separate.

You understand this lesson when you can predict those changes and write a test that catches unwanted sharing. Reading the page alone does not prove that skill.

[Continue: object design and typing](/lessons/python-classes)
