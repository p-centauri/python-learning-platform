"""Private local backup and isolated restoration; never overwrites a live database."""

import argparse
from contextlib import closing
from datetime import datetime, timezone
from hashlib import file_digest
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))

def write_json(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as out:
        json.dump(data, out, indent=2)
        out.write("\n")


def archive_digest(path):
    with path.open("rb") as source:
        return file_digest(source, "sha256").hexdigest()


def snapshot_sqlite(path):
    from app.operations import fingerprint
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///" + str(path), hide_parameters=True)
    try:
        return fingerprint(engine)
    finally:
        engine.dispose()


def compose(args):
    if not args.project or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,62}", args.project):
        raise ValueError("Supply the exact Compose project name.")
    command = ["docker", "compose", "-f", str(ROOT / "docker-compose.yml"), "-p", args.project]
    if args.env_file:
        command += ["--env-file", str(args.env_file.resolve())]
    return command


def command(argv, **kwargs):
    run = subprocess.run(argv, stderr=subprocess.PIPE, timeout=180, **kwargs)
    if run.returncode:
        raise RuntimeError(
            "Maintenance command failed; no live database was overwritten. Inspect the configured services privately."
        )
    return run


def pg_fingerprint(args, target=None):
    option = ["--database", target] if target else []
    # A one-off trusted reader also works while the serving API is stopped.
    run = command(
        compose(args) + ["run", "--rm", "--no-deps", "-T", "api", "python", "-m", "app.operations", *option],
        stdout=subprocess.PIPE,
    )
    return json.loads(run.stdout)


def pg_sql(args, sql):
    return command(
        compose(args)
        + [
            "exec",
            "-T",
            "db",
            "sh",
            "-c",
            'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"',
        ],
        input=sql.encode(),
        stdout=subprocess.PIPE,
    )


def postgres_backup(args):
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists() or args.output.with_suffix(args.output.suffix + ".json").exists():
        raise ValueError("Choose a new backup filename.")
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as out:
            command(
                compose(args)
                + [
                    "exec",
                    "-T",
                    "db",
                    "sh",
                    "-c",
                    'exec pg_dump --format=custom --no-owner --no-acl -U "$POSTGRES_USER" -d "$POSTGRES_DB"',
                ],
                stdout=out,
            )
        provenance = pg_fingerprint(args)
        metadata = {
            "format": "academy-db-backup-v1",
            "kind": "postgresql",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sha256": archive_digest(args.output),
            "head": provenance["head"],
            "content_digest": provenance["content_digest"],
            "scope": "Consistent pg_dump snapshot. Restore into a new isolated database only; no live overwrite. Source comparison requires stopped writers.",
        }
        write_json(args.output.with_suffix(args.output.suffix + ".json"), metadata)
        return {
            "backup": str(args.output),
            "kind": "postgresql",
            "bytes": args.output.stat().st_size,
            "sha256": metadata["sha256"],
        }
    except BaseException:
        args.output.unlink(missing_ok=True)
        raise


def check_archive(args, kind):
    if not args.archive.is_file():
        raise ValueError("Backup file not found.")
    metadata = json.loads(args.archive.with_suffix(args.archive.suffix + ".json").read_text())
    if (
        metadata.get("format") != "academy-db-backup-v1"
        or metadata.get("kind") != kind
        or metadata.get("sha256") != archive_digest(args.archive)
    ):
        raise ValueError("Backup type or digest mismatch; restoration stopped.")
    return metadata


def postgres_restore(args):
    metadata = check_archive(args, "postgresql")
    target = "academy_restore_" + secrets.token_hex(8)
    created = False
    keep = False
    try:
        pg_sql(
            args,
            f"SELECT format('CREATE DATABASE %I OWNER %I TEMPLATE template0', '{target}', pg_get_userbyid(nspowner)) FROM pg_namespace WHERE nspname='public' \\gexec\n",
        )
        created = True
        with args.archive.open("rb") as source:
            command(
                compose(args)
                + [
                    "run",
                    "--rm",
                    "--no-deps",
                    "-T",
                    "-e",
                    "RESTORE_TARGET=" + target,
                    "db-setup",
                    "sh",
                    "-c",
                    'export PGUSER="$ACADEMY_APP_USER" PGPASSWORD="$ACADEMY_APP_PASSWORD"; exec pg_restore --exit-on-error --single-transaction --clean --if-exists --no-owner --no-acl -d "$RESTORE_TARGET"',
                ],
                stdin=source,
                stdout=subprocess.PIPE,
            )
        restored = pg_fingerprint(args, target)
        if restored["head"] != metadata["head"] or restored["content_digest"] != metadata["content_digest"]:
            raise ValueError(
                "Restore requires the recorded migration/content version. No live state changed."
            )
        source_matches = None
        if args.compare_source:
            source = pg_fingerprint(args)
            source_matches = source["tables"] == restored["tables"] and source["head"] == restored["head"]
            if not source_matches:
                raise ValueError(
                    "Restored records differ from the current source. A valid backup snapshot may differ when writers were not stopped."
                )
        keep = args.keep_restored_database
        return {
            "restored": True,
            "target_removed": not keep,
            "restored_database": target if keep else None,
            "head": restored["head"],
            "table_count": len(restored["tables"]),
            "record_count": sum(t["rows"] for t in restored["tables"].values()),
            "source_matches": source_matches,
            "role": restored["role"],
            "scope": "Actual archive restored to a new database with FK/schema validation; live state unchanged. No traffic served from the target.",
        }
    finally:
        if created:
            if not keep:
                pg_sql(args, f'DROP DATABASE "{target}" WITH (FORCE);')


def sqlite_backup(args):
    from app.operations import content_digest

    if not args.database.is_file():
        raise ValueError("SQLite database not found.")
    if args.output.exists() or args.output.with_suffix(args.output.suffix + ".json").exists():
        raise ValueError("Choose a new backup filename.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    try:
        with (
            closing(sqlite3.connect(f"file:{args.database.resolve()}?mode=ro", uri=True)) as source,
            closing(sqlite3.connect(args.output)) as out,
        ):
            source.backup(out)
        facts = snapshot_sqlite(args.output)
        metadata = {
            "format": "academy-db-backup-v1",
            "kind": "sqlite",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sha256": archive_digest(args.output),
            "facts": facts,
            "content_digest": content_digest(),
        }
        write_json(args.output.with_suffix(args.output.suffix + ".json"), metadata)
        return {
            "backup": str(args.output),
            "kind": "sqlite",
            "head": facts["head"],
            "tables": len(facts["tables"]),
            "sha256": metadata["sha256"],
        }
    except BaseException:
        args.output.unlink(missing_ok=True)
        raise


def sqlite_restore(args):
    from app.operations import content_digest

    metadata = check_archive(args, "sqlite")
    if metadata["content_digest"] != content_digest():
        raise ValueError("Use the recorded content version before restoring this snapshot.")
    with tempfile.TemporaryDirectory(prefix="academy-restore-check-") as folder:
        target = Path(folder) / "restored.db"
        shutil.copy2(args.archive, target)
        facts = snapshot_sqlite(target)
        assert facts["tables"] == metadata["facts"]["tables"] and facts["head"] == metadata["facts"]["head"]
    return {
        "restored": True,
        "target_removed": True,
        "head": facts["head"],
        "table_count": len(facts["tables"]),
        "record_count": sum(t["rows"] for t in facts["tables"].values()),
        "source_matches": True,
        "scope": "Actual isolated copy passes SQLite integrity/FK checks and exact backup fingerprints; live database unchanged.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ["postgres-backup", "postgres-restore-check"]:
        p = sub.add_parser(name)
        p.add_argument("--project", required=True)
        p.add_argument("--env-file", type=Path)
        p.add_argument("--output" if name.endswith("backup") else "--archive", type=Path, required=True)
        if name.endswith("check"):
            p.add_argument(
                "--compare-source", action="store_true", help="Use only while source writers are stopped."
            )
            p.add_argument(
                "--keep-restored-database",
                action="store_true",
                help="Retain a successfully verified NEW database for operator-controlled recovery. Failures still remove it; never overwrites live state.",
            )
    p = sub.add_parser("sqlite-backup")
    p.add_argument("--database", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("sqlite-restore-check")
    p.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    actions = {
        "postgres-backup": postgres_backup,
        "postgres-restore-check": postgres_restore,
        "sqlite-backup": sqlite_backup,
        "sqlite-restore-check": sqlite_restore,
    }
    try:
        print(json.dumps(actions[args.mode](args), indent=2))
    except Exception as error:
        print(
            f"Backup/restore stopped ({type(error).__name__}). No live database was overwritten.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
