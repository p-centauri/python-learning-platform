from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator
from .contracts import Context


class Store:
    """Separate explicit local DB; notes and operation receipts share a transaction."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=0.2, isolation_level=None)
        try:
            db.execute("PRAGMA foreign_keys=ON")
            yield db
        finally:
            db.close()

    def initialize(self) -> None:
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if tables:
                    if tables != {"metadata", "notes", "receipts"}:
                        raise ValueError("unexpected tool database")
                    if db.execute("SELECT version FROM metadata").fetchall() != [("tool-store-v1",)]:
                        raise ValueError("tool schema mismatch")
                else:
                    db.execute("CREATE TABLE metadata(version TEXT NOT NULL)")
                    db.execute("INSERT INTO metadata VALUES ('tool-store-v1')")
                    db.execute(
                        "CREATE TABLE notes(id INTEGER PRIMARY KEY, tenant TEXT NOT NULL, actor TEXT NOT NULL, label TEXT NOT NULL, source_digest TEXT NOT NULL)"
                    )
                    db.execute(
                        "CREATE TABLE receipts(tenant TEXT NOT NULL, actor TEXT NOT NULL, operation_id TEXT NOT NULL, fingerprint TEXT NOT NULL, note_id INTEGER NOT NULL REFERENCES notes(id), PRIMARY KEY(tenant, actor, operation_id))"
                    )
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def commit(self, context: Context, fingerprint: str, title: str, digest: str) -> tuple[int, bool]:
        scope = (context.principal.tenant, context.actor, context.operation_id)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    "SELECT fingerprint,note_id FROM receipts WHERE tenant=? AND actor=? AND operation_id=?",
                    scope,
                ).fetchone()
                if row is not None:
                    if row[0] != fingerprint:
                        raise ValueError("operation_conflict")
                    db.execute("COMMIT")
                    return int(row[1]), True
                count = db.execute(
                    "SELECT count(*) FROM notes WHERE tenant=? AND actor=?", scope[:2]
                ).fetchone()[0]
                total = db.execute("SELECT count(*) FROM notes").fetchone()[0]
                if count >= context.max_notes or total >= 32:
                    raise ValueError("effect_limit")
                cursor = db.execute(
                    "INSERT INTO notes(tenant,actor,label,source_digest) VALUES (?,?,?,?)",
                    (*scope[:2], title, digest),
                )
                note_id = cursor.lastrowid
                if note_id is None:
                    raise ValueError("missing local note id")
                db.execute("INSERT INTO receipts VALUES (?,?,?,?,?)", (*scope, fingerprint, note_id))
                db.execute("COMMIT")
                return note_id, False
            except BaseException:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise

    def counts(self, context: Context) -> tuple[int, int]:
        scope = (context.principal.tenant, context.actor)
        with self.connection() as db:
            notes = db.execute("SELECT count(*) FROM notes WHERE tenant=? AND actor=?", scope).fetchone()[0]
            receipts = db.execute(
                "SELECT count(*) FROM receipts WHERE tenant=? AND actor=?", scope
            ).fetchone()[0]
            return int(notes), int(receipts)
