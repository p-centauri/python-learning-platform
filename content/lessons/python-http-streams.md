## A network chunk is not a record

Separate transport chunks from complete application records. This is lesson 6 of 8. One chunk can contain half a JSON line or several lines. A UTF-8 character can also cross a chunk boundary. Decoding each chunk independently or parsing one JSON value per chunk will fail on valid data.

For newline-delimited JSON, accumulate bytes only until LF completes a bounded line, then decode and validate that line. Keep a partial line for the next chunk. A final nonempty line can be accepted without LF under this lab's contract.

```python
import json

chunks = [b'{"id":"a",', b'"value":2}\n{"id":"b","value":3}\n']
buffer = bytearray()
records: list[dict[str, object]] = []
for chunk in chunks:
    buffer.extend(chunk)
    while b"\n" in buffer:
        raw, _, rest = buffer.partition(b"\n")
        records.append(json.loads(raw.decode("utf-8")))
        buffer = rest
assert [r["value"] for r in records] == [2, 3]
assert buffer == b""
```

This tiny demonstration retains a list and has no size checks. The project implementation must instead yield records and check the pending byte length before copying each segment. Do not turn the example into an unbounded production parser.

## Bound different layers separately

A 1,024-byte line limit prevents one record from growing without bound. An 8,192-byte body limit bounds this lab's total accepted input. Check actual bytes rather than trusting Content-Length. Count LF toward the body; exclude LF from the line limit, while CR in CRLF remains a line byte. The exact limits are allowed.

Use streamed raw reads of 256 bytes and reject compression in this bounded contract. Otherwise a small compressed input could expand dramatically after decoding. These checks bound application input and pending parser state, not all memory in the operating system or HTTP stack.

## Guided practice

Implement iter_records and run the split-byte, multi-line and exact-limit tests. Ensure generator creation consumes nothing and the first complete record is yielded before another chunk is requested.

## Independent task

Add two different chunkings of the same body and show they produce identical records. Add an oversized line assembled across chunks. Verify malformed input after a valid row stops the whole summary.

## Check your work

Explain the maximum retained parser state and which buffers belong to the transport. Continue with [HTTP failures and retry decisions](/lessons/python-http-failures).
