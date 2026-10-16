import argparse
from importlib.resources import files
import json
import sys

import httpx

from .http import open_feed
from .models import FeedError, RecordError
from .parser import summarize

DEMO = b'{"id":"api","value":10}\n{"id":"worker","value":5}\n'


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and summarize a bounded NDJSON feed")
    parser.add_argument("--demo", action="store_true", help="Use a deterministic offline HTTP transport")
    parser.add_argument("--url", help="Trusted HTTPS feed; no redirects or automatic retries")
    args = parser.parse_args()
    if args.demo and args.url:
        parser.error("Choose --demo or --url")
    if not args.demo and not args.url:
        parser.error("Choose --demo or a trusted --url")
    defaults = json.loads(files("academy_ingest").joinpath("defaults.json").read_text(encoding="utf-8"))
    url = args.url or defaults["demo_url"]

    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "application/x-ndjson"}, stream=httpx.ByteStream(DEMO))

    transport = httpx.MockTransport(handle) if args.demo else None
    try:
        with httpx.Client(
            transport=transport,
            timeout=httpx.Timeout(5.0, connect=2.0, pool=2.0),
            limits=httpx.Limits(max_connections=4, max_keepalive_connections=2),
            follow_redirects=False,
            trust_env=False,
        ) as client:
            with open_feed(url, client=client) as records:
                report = summarize(records)
        # Do not print a partial success before the whole feed and cleanup succeed.
        print(json.dumps(report, sort_keys=True))
        return 0
    except (FeedError, RecordError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
