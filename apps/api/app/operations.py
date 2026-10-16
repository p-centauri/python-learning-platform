"""Trusted maintenance CLI fingerprints; no API route and no raw learner records."""

import argparse
from datetime import date, datetime, timezone
from hashlib import sha256
import json
import re
from sqlalchemy import MetaData, Table, create_engine, inspect, select, text
from .config import settings


def canonical(value):
    if isinstance(value, datetime):
        return (
            value.replace(tzinfo=timezone.utc).isoformat()
            if not value.tzinfo
            else value.astimezone(timezone.utc).isoformat()
        )
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical(v) for v in value]
    return value


def fingerprint(engine):
    result = {}
    with engine.connect() as conn:
        if conn.dialect.name == "postgresql":
            conn.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"))
        for name in sorted(inspect(conn).get_table_names()):
            table = Table(name, MetaData(), autoload_with=conn)
            encoded = [
                json.dumps(canonical(dict(row)), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                for row in conn.execute(select(table)).mappings()
            ]
            result[name] = {
                "rows": len(encoded),
                "digest": sha256("\n".join(sorted(encoded)).encode()).hexdigest(),
            }
        head = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        role = None
        if conn.dialect.name == "postgresql":
            row = conn.execute(
                text(
                    "SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=current_user"
                )
            ).one()
            role = {
                "superuser": row[0],
                "create_database": row[1],
                "create_role": row[2],
                "replication": row[3],
                "bypass_rls": row[4],
            }
        else:
            assert conn.exec_driver_sql("PRAGMA integrity_check").scalar() == "ok"
            assert not conn.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
    return {"head": head, "tables": result, "role": role, "dialect": engine.dialect.name}


def content_digest():
    files = []
    for path in sorted(settings.content_dir.rglob("*")):
        if path.is_file():
            files.append(
                str(path.relative_to(settings.content_dir)) + ":" + sha256(path.read_bytes()).hexdigest()
            )
    return sha256("\n".join(files).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database")
    args = parser.parse_args()
    from sqlalchemy.engine import make_url

    url = make_url(settings.database_url)
    if args.database:
        if not re.fullmatch(r"academy_restore_[a-z0-9]{16}", args.database) or args.database == url.database:
            parser.error("Only a newly created isolated restore database is allowed.")
        url = url.set(database=args.database)
    engine = create_engine(url, pool_pre_ping=True, hide_parameters=True)
    try:
        data = fingerprint(engine)
        data["content_digest"] = content_digest()
        print(json.dumps(data, indent=2))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
