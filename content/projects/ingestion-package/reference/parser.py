from collections.abc import Generator, Iterable
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


def iter_records(chunks: Iterable[bytes]) -> Generator[Record, None, None]:
    buffer = bytearray()
    line = 1
    for chunk in chunks:
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


def summarize(records: Iterable[Record]) -> dict[str, int]:
    count = total = 0
    for record in records:
        count += 1
        total += record.value
    return {"count": count, "total": total}
