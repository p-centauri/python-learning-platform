## Give the HTTP client a clear owner

Reuse a client within a useful scope and close it at that scope's end. This is lesson 5 of 8. A client manages reusable connections and common settings. Opening a new client for every tiny operation loses reuse; leaving a long-lived client unclosed leaves its lifetime unclear.

The CLI owns a client. The ingestion function borrows it, owns one streamed response, and leaves the client open for further work. This is the same ownership idea you practiced with files, now applied to network resources.

## An offline request still exercises client behavior

```python
import httpx

seen: list[str] = []
def handle(request: httpx.Request) -> httpx.Response:
    seen.append(request.method)
    return httpx.Response(200, json={"ready": True})

with httpx.Client(
    transport=httpx.MockTransport(handle),
    timeout=httpx.Timeout(5.0, connect=2.0, pool=2.0),
    limits=httpx.Limits(max_connections=4, max_keepalive_connections=2),
    trust_env=False,
) as client:
    response = client.get("https://feed.example.test/health")
    response.raise_for_status()
    assert response.json() == {"ready": True}
    assert not client.is_closed
assert client.is_closed
assert seen == ["GET"]
```

MockTransport supplies the response without real DNS, TLS or sockets. It makes tests deterministic; it cannot prove that a deployed network or certificate configuration works. Keep TLS verification enabled for real requests. The lab disables environment proxy settings so the CLI's configured behavior is explicit.

## Timeouts have different jobs

Connect bounds establishing a connection. Read bounds waiting for a chunk. Write bounds sending a chunk. Pool bounds waiting for an available connection. A read timeout is not a total request deadline: a server sending small chunks often enough can keep a stream alive longer. Pool limits bound connections, not every waiting task or the total work queued by an application.

## Guided practice

Trace the client context and response context in the starter contract. Observe requests through MockTransport and inspect the request's configured timeout values. Decide which function owns each close operation.

## Independent task

Test that finishing, failing or abandoning one feed leaves the borrowed client usable. Add a connect-timeout test without contacting a live host. Keep credentials and response bodies out of failure messages.

## Check your work

Explain the difference between client reuse, response closure, pool limits and deadlines. Continue with [HTTP chunks and bounded parsing](/lessons/python-http-streams).
