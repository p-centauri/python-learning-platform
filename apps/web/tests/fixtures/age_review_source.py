"""Age only an explicitly named browser-test account's practice fixture."""

from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import sys

email = sys.argv[1]
if not (email.startswith("recall-e2e-") and email.endswith("@example.com")):
    raise SystemExit("Only recall browser-test account fixtures may be changed.")
path = Path(__file__).resolve().parents[4] / "apps/api/academy.db"
with closing(sqlite3.connect(path)) as db, db:
    row = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if row is None:
        raise SystemExit("The test account must already be registered.")
    count = db.execute(
        "SELECT count(*) FROM exercise_attempts WHERE user_id=? AND exercise_id='python-values-check-1'",
        (row[0],),
    ).fetchone()[0]
    if not 1 <= count <= 6:
        raise SystemExit("Expected one to six owned practice fixtures.")
    timestamp = (datetime.now(timezone.utc) - timedelta(days=2)).replace(tzinfo=None).isoformat(sep=" ")
    db.execute(
        "UPDATE exercise_attempts SET created_at=? WHERE user_id=? AND exercise_id='python-values-check-1'",
        (timestamp, row[0]),
    )
print("Only this test account's practice timestamps were aged for the delayed-review journey.")
