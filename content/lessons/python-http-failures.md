## Preserve failure information and avoid accidental retries

A failure should tell the caller what failed while keeping useful causes. This is lesson 7 of 8. A malformed record is different from a failed connection, an HTTP status rejection or a consumer's own bug. Do not catch every exception and call it bad JSON.

The lab uses RecordError for malformed data and FeedError for its HTTP boundary. It preserves original decoding and HTTP transport exceptions with `raise ... from exc`. A caller's exception propagates unchanged. Every path still closes the owned response.

```python
import httpx

class ExampleFeedError(ValueError):
    pass

def fail_connect() -> None:
    try:
        raise httpx.ConnectTimeout("connection did not complete")
    except httpx.HTTPError as exc:
        raise ExampleFeedError("HTTP connection failed") from exc

try:
    fail_connect()
except ExampleFeedError as error:
    assert isinstance(error.__cause__, httpx.ConnectTimeout)
```

Keep remote bodies, credentials and full secret-bearing URLs out of public errors. Preserve details in controlled diagnostics when needed. The lab accepts only status 200 and its specified media type. It makes one GET, refuses redirects and performs no retries.

## A retry is a policy decision

Retrying after a partial stream may replay records. With future database writes, a timeout may occur after a write committed. Plan stable record IDs, transaction boundaries and deduplication before adding retries. GET being intended as a safe method does not make downstream processing automatically duplicate-free.

Transient failures can justify bounded attempts with backoff, jitter and a total deadline; a permanent validation failure usually cannot. Respect rate limits and Retry-After only under a defined policy. An unlimited retry loop can overload an already struggling dependency. Here the easiest correct contract is to fail visibly and let the caller decide.

## Guided practice

Run the supplied status, redirect, connect-timeout and mid-stream-timeout tests. Check both the error cause and response closure. Show that an HTTPX exception deliberately raised by the consumer is not relabeled by the feed helper.

## Independent task

Design, without implementing it in this contract, how a later database ingestion worker could retry without duplicate writes. Separate retryable transport errors from malformed records. Explain what evidence is needed if an acknowledgment is lost.

## Check your work

Count actual requests in a failure test. Explain why one request and no partial success is the present rule. Continue with [ingestion failure tests](/lessons/python-ingestion-tests).
