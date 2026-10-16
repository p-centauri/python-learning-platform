## The idea in plain language

Logs help explain what happened, but they can also copy private input into another system. Start with the question an operator needs to answer: did reporting start, finish, or fail? A small event name and a configured source label are enough for this lab. A successful count is useful; raw records, credentials, URLs and exception bodies are unnecessary.

Get a named logger for library code. Let the application decide handlers, formatters and destinations. Calling basicConfig during import or adding global handlers inside a helper changes the host application's behavior. This package imports quietly and accepts an injected logger, so tests and applications control logging independently.

Use level and message deliberately. INFO describes a normal start or success; WARNING records the bounded reporter failure. Extra fields belong on the LogRecord, but they do not automatically appear in every formatter. Do not collide with reserved attributes such as message or levelname. Parameterized messages can defer formatting, but they do not redact sensitive arguments by themselves.

A failure message may contain the offending input. logging.exception or exc_info can therefore leak it through a traceback. Here we record only an allowlisted event and re-raise the same exception to the caller. That is a narrow lab policy, not a universal observability solution. Reliable logger handlers are an explicit assumption; deployments still need their own retention, access and operational decisions.

## Worked example

Run this small example locally, then explain the output in your own words.

```python
import logging

logger = logging.getLogger("academy.example")
events: list[str] = []
class Capture(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        events.append(record.getMessage())

handler = Capture()
old_level = logger.level
logger.addHandler(handler)
logger.setLevel(logging.INFO)
try:
    logger.info("feed_report_succeeded", extra={"source_id": "demo", "record_count": 1})
finally:
    logger.removeHandler(handler)
    handler.close()
    logger.setLevel(old_level)
print(events)  # ['feed_report_succeeded']
```

## Guided practice

Run the caplog tests and inspect message, level, source_id, record_count and exc_info separately. Raise an exception containing a fake secret and confirm the captured records never contain that secret. Do not use a real credential in a test.

## Independent practice

Write the reporting wrapper with two possible terminal events. A source that fails after its first record should emit failure only. Explain why a no-success assertion matters and why inspecting a formatted string alone can miss unsafe record fields.

## Check your work

Your code has no global logging configuration and no payload dumps. Tests exercise real log emission, preserved errors and absent success on late failure. Explain the logger reliability assumption and what remains deployment work.

Continue to [Bounded regex rules & the policy lab](/lessons/python-regex-contracts).
