"""Provided command wrapper. Implement expenses.py; keep this CLI contract."""

import argparse
import csv
import json
import sys

from expenses import summarize_csv


def main(argv=None):
    parser = argparse.ArgumentParser(description="Summarize an expense CSV as JSON")
    parser.add_argument("csv_path", help="UTF-8 CSV with category,amount header")
    args = parser.parse_args(argv)
    try:
        report = summarize_csv(args.csv_path)
    except (OSError, ValueError, csv.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
