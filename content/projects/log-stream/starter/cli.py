"""Print a summary only after successful reading and cleanup."""

import argparse
import json
from pathlib import Path
import sys
from stream import RecordError, open_readings, summarize


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize service logs one record at a time")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        with open_readings(args.path) as readings:
            report = summarize(readings)
    except (RecordError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
