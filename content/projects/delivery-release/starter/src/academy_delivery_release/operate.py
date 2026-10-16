"""Supplied explicit CLI; no database work during import."""
import argparse
import logging
import os
import sys
import uvicorn
from alembic.util.exc import CommandError
from sqlalchemy.exc import DBAPIError, TimeoutError as PoolTimeout
from academy_delivery_schema import BusyMigration, NotReady, check, downgrade, upgrade
from academy_ingestion_service import make_engine
from academy_ingestion_service.database import url_from_dsn
from .contracts import ConfigurationError, Reason
from .operations import assess, create_release, load_settings
from .support import emit


def main() -> int:
    parser = argparse.ArgumentParser(description="Owned local lab operations only")
    parser.add_argument("action", choices=("prepare", "check", "serve", "rollback"))
    parser.add_argument("--port", type=int, default=8011)
    parser.add_argument("--target", choices=("delivery_003", "service_002"))
    parser.add_argument("--allow-loss", action="store_true")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be 1024..65535")
    if args.action == "rollback" and (not args.target or not args.allow_loss):
        parser.error("rollback requires a named target and --allow-loss; read RUNBOOK.md")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        settings = load_settings(os.environ)
    except ConfigurationError:
        print("invalid release configuration", file=sys.stderr)
        return 2
    if args.action == "serve":
        release = create_release(settings)
        uvicorn.run(release.app, host="127.0.0.1", port=args.port, access_log=False, log_level="warning", timeout_graceful_shutdown=3)
        return 0
    engine = make_engine(url_from_dsn(settings.dsn))
    try:
        if args.action == "prepare":
            upgrade(engine)
            check(engine)
            emit("prepared", Reason.READY)
        elif args.action == "check":
            result = assess(engine)
            emit("checked", result.reason)
            if not result.ready:
                return 1
            check(engine)
        else:
            downgrade(engine, args.target, allow_loss=True)
            emit("rollback", Reason.SCHEMA_HEAD)
        return 0
    except (DBAPIError, PoolTimeout, BusyMigration):
        emit("operation-refused", Reason.STORAGE_UNAVAILABLE)
        return 1
    except (NotReady, CommandError):
        emit("operation-refused", Reason.SCHEMA_CONTRACT)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
