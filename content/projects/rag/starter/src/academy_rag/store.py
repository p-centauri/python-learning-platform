from contextlib import contextmanager
from dataclasses import asdict, replace
from pathlib import Path
import sqlite3
from typing import Iterator
from academy_retrieval import Spec
from academy_retrieval.contracts import integer
from .contracts import Record
from .support import canonical, chunks, decode_record


class Index:
    """An explicitly initialized separate local file; every operation owns/closes its connection."""

    def __init__(self, path: Path, spec: Spec = Spec()) -> None:
        if not isinstance(path, Path) or type(spec) is not Spec:
            raise ValueError("explicit path and exact vector spec required")
        self.path = path.resolve()
        self.spec = replace(spec)

    @contextmanager
    def transaction(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True, timeout=1, isolation_level=None)
        try:
            db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def initialize(self) -> None:
        db = sqlite3.connect(self.path, timeout=1, isolation_level=None)
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "CREATE TABLE IF NOT EXISTS academy_rag_meta (id INTEGER PRIMARY KEY CHECK(id=1), schema TEXT NOT NULL, spec BLOB NOT NULL, epoch INTEGER NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS academy_rag_docs (tenant TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL, payload BLOB NOT NULL, PRIMARY KEY(tenant,id))"
            )
            db.execute(
                "INSERT OR IGNORE INTO academy_rag_meta VALUES (1, 'rag-store-v1', ?, 0)",
                (canonical(asdict(self.spec)),),
            )
            self.state(db)
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def state(self, db: sqlite3.Connection) -> tuple[int, tuple[Record, ...]]:
        rows = db.execute("SELECT schema,spec,epoch FROM academy_rag_meta WHERE id=1").fetchall()
        if len(rows) != 1 or rows[0][0] != "rag-store-v1" or rows[0][1] != canonical(asdict(self.spec)):
            raise ValueError("unsupported index schema or vector identity")
        epoch = integer(rows[0][2], 0, 1000000)
        saved = db.execute(
            "SELECT tenant,id,revision,payload FROM academy_rag_docs ORDER BY tenant,id LIMIT 17"
        ).fetchall()
        if len(saved) > 16:
            raise ValueError("document identity cap exceeded")
        records: list[Record] = []
        for tenant, id, revision, payload in saved:
            item = decode_record(payload, self.spec)
            if (item.tenant, item.id, item.revision) != (tenant, id, revision):
                raise ValueError("stored source identity mismatch")
            records.append(item)
        result = tuple(records)
        chunks(result, self.spec)
        return epoch, result

    def snapshot(self) -> tuple[int, tuple[Record, ...]]:
        with self.transaction() as db:
            return self.state(db)
