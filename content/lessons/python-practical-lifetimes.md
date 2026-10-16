A composed project needs an owner for every resource. The supplied read_all borrows an explicitly configured HTTPX AsyncClient. It owns each streamed response through async with. Cancelling a read or rejecting status, media, JSON or byte size must close that response; it must not close the borrowed client. The client owner closes it later. Do not catch CancelledError and turn it into a successful empty report. Failure is still failure, even when cleanup succeeds.

The reader uses the original scoped keyset route and limit 32. It admits at most eight pages, caps each decoded body at 8192 bytes and rejects repeated or backwards positions. Individual page/body bounds do not create a hard total request deadline or hostile wire-memory guarantee. Multiple pages can observe different READ COMMITTED snapshots if writers continue. The owned rehearsal stops writing before reading, so its fixed fixture gives a reproducible batch; the adapter does not promise a global snapshot for a live changing service.

The worker rehearsal uses the earlier Resource handoff, owned_resources and request_scope. A factory owns partial setup until it returns a cleanup callback. Once handed off, the stack registers cleanup before proceeding. If a second acquisition fails, the first owned directory is removed and the original exception remains visible. Context tokens restore the previous label on success or failure. A weak reference would not replace a directory close action.

Thread and spawn workers receive immutable file-job descriptions. They open and close their own files; they do not inherit or share the service Engine. Two workers and a pending window of two bound admission. Running callbacks cannot be cancelled merely by cancelling a Future; shutdown waits for admitted work. The installed rehearsal compares ordered thread and process values, checks closed files and restores its owned directory/context. It does not claim that processes are always faster, nor that a blocked callback has a hard deadline.

## Guided practice

Predict the printed value, then explain which boundary this small illustration leaves unevaluated.

```python
from contextlib import ExitStack
events: list[str] = []
with ExitStack() as stack:
    stack.callback(events.append, "directory closed")
    stack.callback(events.append, "response closed")
print(events[0])
```

## Independent practice

Draw a small ownership table for client, response, directory, tracer, Engine and worker pool. Add a cancellation case while a response waits and a failure after the first resource acquisition. Record cleanup and propagation before interpreting performance.

## Check your work

Distinguish borrowed objects from owned lifetimes. Verify that a cancelled read closes its response, retains the client and propagates cancellation; show worker-local files and joined shutdown.

Use the [Composed Python practical review project](/projects#python-practical-review). Record actual commands and outcomes, preserve the submitted version and keep credentials private.
