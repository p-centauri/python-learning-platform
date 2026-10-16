"""Explicit local server, no schema changes or built-in credentials. Quiet import."""

import argparse
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import json
import os
from fastapi import FastAPI
import uvicorn
from academy_ingestion_service import create_app, make_engine
from academy_ingestion_service.database import url_from_dsn


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8010)
    args = parser.parse_args()
    dsn = os.environ.get("ACADEMY_SERVICE_DSN")
    configuration = os.environ.get("ACADEMY_SERVICE_TOKENS")
    if not dsn or not configuration:
        parser.error("configure a disposable DSN and private token-to-namespace JSON mapping")
    tokens: object = json.loads(configuration)
    if not isinstance(tokens, dict) or not all(type(k) is str and type(v) is str for k, v in tokens.items()):
        parser.error("credential configuration must map strings to namespace strings")
    engine = make_engine(url_from_dsn(dsn))
    try:
        app = create_app(engine, tokens)

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncIterator[None]:
            try:
                yield
            finally:
                engine.dispose()

        app.router.lifespan_context = lifespan
        uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
