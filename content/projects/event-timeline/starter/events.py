"""Deliberately buggy learner program. Repair it to match README.md and the tests."""

import json
from datetime import datetime, timezone


def normalize_label(text):
    if not isinstance(text, str):
        raise ValueError("label must be text")
    label = text.strip().lower()
    if not label:
        raise ValueError("label cannot be empty")
    return label


def build_timeline(payload):
    rows = json.loads(payload.decode("latin-1"))
    if not isinstance(rows, list):
        raise ValueError("input must be a list")
    result = []
    for number, row in enumerate(rows, start=1):
        try:
            if not isinstance(row, dict) or set(row) != {"label", "timestamp"}:
                raise ValueError("expected label and timestamp fields")
            label = normalize_label(row["label"])
            if not isinstance(row["timestamp"], str):
                raise ValueError("timestamp must be text")
            instant = datetime.fromisoformat(row["timestamp"])
            if instant.tzinfo is None or instant.utcoffset() is None:
                raise ValueError("timestamp needs a UTC offset")
            instant = instant.replace(tzinfo=timezone.utc)
        except (ValueError, OverflowError) as exc:
            raise ValueError(f"record {number}: {exc}") from exc
        result.append((instant, label))
    result.sort(key=lambda row: row[0], reverse=True)
    return [{"label": label, "timestamp": instant.isoformat()} for instant, label in result]
