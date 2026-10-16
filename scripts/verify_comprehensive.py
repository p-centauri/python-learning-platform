"""Verify authored repair code in actual isolated containers; never run learner code here."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/runner"))
from runner.sandbox import execute  # noqa: E402
from runner.verification import verify  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    exam = json.loads((ROOT / "content/assessments/practical-repair-v1.json").read_text())
    definition = exam["execution"]
    base = ROOT / "content/exam-packs/practical-repair-v1"
    code = (base / "reference/core.py").read_text()
    assert len(code.encode()) <= 16384 and len(code) <= 12000
    assert len(definition["tests"]) == 23 and sum(t["public"] for t in definition["tests"]) == 8
    # Independent fixed expected observations catch accidental fixture/reference drift.
    public = {t["name"]: t for t in definition["tests"] if t["public"]}
    assert public["Order reservation and outbox"]["expected"] == {
        "results": ["created"],
        "stock": 1,
        "orders": 1,
        "outbox": 1,
    }
    assert public["Atomic rollback"]["expected"] == {
        "results": ["rolled-back", "created"],
        "stock": 1,
        "orders": 1,
        "outbox": 1,
    }
    assert public["Commit then lost acknowledgment"]["expected"] == {
        "effects": 3,
        "acks": 1,
        "retries": 0,
        "quarantined": 0,
    }
    assert public["Scoped supporting citations"]["expected"] == {
        "citations": ["a"],
        "answer": "refund policy",
    }
    assert public["Expense replay receipt"]["expected"] == {
        "results": ["created", "replayed"],
        "expense_cents": 100,
        "receipts": 1,
    }
    assert public["One query, full keys and order grain"]["expected"] == {
        "rows": [[1, 100, 5], [2, 100, 0]],
        "selects": 1,
    }
    assert public["Cache namespace and source replacement"]["expected"] == ["old", None, "new"]
    assert public["Bounded async failure cleanup"]["expected"] == {
        "results": ["a", "error", "c"],
        "peak": 2,
        "live": 0,
    }
    verification = verify()
    reference = execute(code, definition)
    assert reference["status"] == "passed" and reference["passed"] == 23, reference
    broken_definition = {**definition, "tests": [t for t in definition["tests"] if t["public"]]}
    broken = execute((base / "starter/core.py").read_text(), broken_definition)
    assert broken["passed"] == 0 and broken["total"] == 8, broken
    report = {
        "exam_version": exam["version"],
        "execution_digest": sha256(
            json.dumps(definition, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "startup_checks": verification["checks"],
        "maintained_reference": {
            "passed": reference["passed"],
            "total": reference["total"],
            "duration_ms": reference["duration_ms"],
        },
        "deliberate_starter": {
            "passed": broken["passed"],
            "total": broken["total"],
            "duration_ms": broken["duration_ms"],
        },
        "scope": "Actual fresh-container offline core contracts. HTTP/Docker release, PostgreSQL concurrency, real broker/model, architecture and semantic quality remain rubric evidence.",
    }
    if args.report_output:
        args.report_output.parent.mkdir(parents=True, exist_ok=True)
        args.report_output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
