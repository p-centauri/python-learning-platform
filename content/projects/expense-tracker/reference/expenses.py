"""Maintainer reference for checking the learner contract; excluded from downloads."""

import csv
from pathlib import Path


def parse_amount(text):
    parts = text.strip().split(".")
    if len(parts) > 2 or not parts[0] or any(c not in "0123456789" for c in parts[0]):
        raise ValueError("amount needs digits before at most one dot")
    fraction = parts[1] if len(parts) == 2 else ""
    if len(parts) == 2 and (not 1 <= len(fraction) <= 2 or any(c not in "0123456789" for c in fraction)):
        raise ValueError("amount needs one or two digits after the dot")
    return int(parts[0]) * 100 + int(fraction.ljust(2, "0"))


def summarize_rows(rows):
    totals = {}
    count = total = 0
    for number, row in enumerate(rows, start=2):
        try:
            if set(row) != {"category", "amount"} or not all(isinstance(v, str) for v in row.values()):
                raise ValueError("expected category and amount text fields")
            category = row["category"].strip().lower()
            if not category:
                raise ValueError("category cannot be empty")
            cents = parse_amount(row["amount"])
        except ValueError as exc:
            raise ValueError(f"record {number}: {exc}") from exc
        count += 1
        total += cents
        totals[category] = totals.get(category, 0) + cents
    return {"row_count": count, "total_cents": total, "by_category": totals}


def summarize_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source, strict=True)
        if reader.fieldnames != ["category", "amount"]:
            raise ValueError("header must be category,amount")
        return summarize_rows(reader)
