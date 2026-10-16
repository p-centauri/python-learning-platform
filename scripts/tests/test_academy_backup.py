"""Exercise real backup/restore and refusal paths without touching live academy state."""

from contextlib import closing
from argparse import Namespace
from pathlib import Path
import sqlite3
import tempfile
import unittest

from scripts.academy_backup import sqlite_backup, sqlite_restore


class BackupSafetyTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix="academy-backup-test-")
        self.addCleanup(self.folder.cleanup)
        root = Path(self.folder.name)
        self.source = root / "source.db"
        self.archive = root / "backup.db"
        with closing(sqlite3.connect(self.source)) as db, db:
            db.executescript("""
                PRAGMA foreign_keys=ON;
                CREATE TABLE alembic_version(version_num TEXT PRIMARY KEY);
                INSERT INTO alembic_version VALUES('fixture_v1');
                CREATE TABLE learners(id INTEGER PRIMARY KEY, note TEXT);
                CREATE TABLE evidence(id INTEGER PRIMARY KEY, learner_id INTEGER REFERENCES learners(id));
                INSERT INTO learners VALUES(1, 'Private learner note');
                INSERT INTO evidence VALUES(1, 1);
            """)

    def test_actual_restore_matches_snapshot_and_rejects_changed_archive(self):
        sqlite_backup(Namespace(database=self.source, output=self.archive))
        self.assertEqual(self.archive.stat().st_mode & 0o777, 0o600)
        manifest = self.archive.with_suffix(".db.json")
        self.assertEqual(manifest.stat().st_mode & 0o777, 0o600)
        report = sqlite_restore(Namespace(archive=self.archive))
        self.assertTrue(report["source_matches"])
        self.assertEqual(report["record_count"], 3)
        with closing(sqlite3.connect(self.archive)) as db, db:
            db.execute("UPDATE learners SET note='Changed after backup'")
        with self.assertRaises(ValueError):
            sqlite_restore(Namespace(archive=self.archive))
        with closing(sqlite3.connect(self.source)) as db, db:
            self.assertEqual(db.execute("SELECT note FROM learners").fetchone()[0], "Private learner note")

    def test_backup_refuses_existing_destination_or_manifest_and_live_source(self):
        original = self.source.read_bytes()
        with self.assertRaises(ValueError):
            sqlite_backup(Namespace(database=self.source, output=self.source))
        self.assertEqual(original, self.source.read_bytes())
        self.archive.write_bytes(b"Do not overwrite")
        with self.assertRaises(ValueError):
            sqlite_backup(Namespace(database=self.source, output=self.archive))
        self.assertEqual(self.archive.read_bytes(), b"Do not overwrite")
        self.archive.unlink()
        manifest = self.archive.with_suffix(".db.json")
        manifest.write_bytes(b"Keep existing manifest")
        with self.assertRaises(ValueError):
            sqlite_backup(Namespace(database=self.source, output=self.archive))
        self.assertEqual(manifest.read_bytes(), b"Keep existing manifest")

    def test_invalid_foreign_key_snapshot_is_not_reported_as_a_backup(self):
        with closing(sqlite3.connect(self.source)) as db, db:
            db.execute("INSERT INTO evidence VALUES(2, 999)")
        with self.assertRaises(AssertionError):
            sqlite_backup(Namespace(database=self.source, output=self.archive))
        self.assertFalse(self.archive.exists())
        self.assertFalse(self.archive.with_suffix(".db.json").exists())


if __name__ == "__main__":
    unittest.main()
