"""Provided wrapper; fix the transformations in events.py."""

import argparse
import json
from pathlib import Path
import sys
from events import build_timeline


def main(argv=None):
    parser = argparse.ArgumentParser(description="Normalize and order an event timeline")
    parser.add_argument("json_path", help="UTF-8 JSON list of label/timestamp records")
    args = parser.parse_args(argv)
    try:
        report = build_timeline(Path(args.json_path).read_bytes())
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
