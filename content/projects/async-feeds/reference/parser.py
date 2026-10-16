from collections.abc import AsyncGenerator, AsyncIterable
import json
import re

from .models import MAX_LINE_BYTES, Record, RecordError


def _record(raw: bytes, line: int) -> Record:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecordError(f"line {line}: invalid UTF-8 or JSON") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"id", "value"}
        or not isinstance(value["id"], str)
        or re.fullmatch(r"[a-z][a-z0-9-]{0,31}", value["id"]) is None
        or type(value["value"]) is not int
        or not 0 <= value["value"] <= 60000
    ):
        raise RecordError(f"line {line}: expected a valid id and integer value")
    return Record(value["id"], value["value"])


async def iter_records(chunks: AsyncIterable[bytes]) -> AsyncGenerator[Record, None]:
    buffer = bytearray()
    line = 1
    async for chunk in chunks:
        if not isinstance(chunk, bytes):
            raise RecordError(f"line {line}: expected bytes")
        offset = 0
        while offset < len(chunk):
            end = chunk.find(b"\n", offset)
            stop = len(chunk) if end == -1 else end
            if len(buffer) + stop - offset > MAX_LINE_BYTES:
                raise RecordError(f"line {line}: record exceeds byte limit")
            buffer.extend(chunk[offset:stop])
            if end == -1:
                break
            raw = bytes(buffer)
            buffer.clear()
            record = _record(raw, line)
            line += 1
            offset = end + 1
            yield record
    if buffer:
        yield _record(bytes(buffer), line)
