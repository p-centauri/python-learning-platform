from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from runner.sandbox import execute, python_case, checked, PROFILE
from runner.verification import verify
from runner import main

CONTENT = json.loads((Path(__file__).resolve().parents[3] / "content/coding-exercises.json").read_text())
REFERENCES = {
    "python-exact-cents": """import re
def parse_cents(text):
    if not isinstance(text, str) or not re.fullmatch(r"[0-9]+(?:\\.[0-9]{1,2})?", text):
        raise ValueError("Use digits and up to two decimals.")
    whole, _, fraction = text.partition(".")
    return int(whole)*100 + int(fraction.ljust(2,"0"))
""",
    "python-category-totals": """def category_totals(rows):
    totals = {}
    for row in rows:
        if not isinstance(row, dict): raise ValueError("Invalid row")
        category, cents = row.get("category"), row.get("cents")
        if not isinstance(category,str) or not category.strip() or type(cents) is not int or cents < 0:
            raise ValueError("Invalid category or amount")
        name = category.strip()
        totals[name] = totals.get(name,0) + cents
    return totals
""",
    "python-retry-delay": """def retry_delay(attempt, cap):
    if type(attempt) is not int or type(cap) is not int or attempt < 1 or cap < 1:
        raise ValueError("Use positive integers")
    return cap if attempt-1 >= cap.bit_length() else min(1 << (attempt-1), cap)
""",
    "sql-paid-totals": """SELECT c.id AS customer_id, COALESCE(SUM(o.total_cents),0) AS total_cents
FROM customers c LEFT JOIN orders o ON o.customer_id=c.id AND o.status='paid'
GROUP BY c.id ORDER BY c.id;""",
    "sql-latest-event": """SELECT DISTINCT ON (order_id) order_id, event_type
FROM events ORDER BY order_id, occurred_at DESC, id DESC;""",
    "sql-tenant-invoices": """SELECT id AS invoice_id, amount_cents FROM invoices
WHERE tenant_id=7 AND paid=false ORDER BY id;""",
}


class SandboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Real Docker probes must pass before these source strings execute.
        cls.verification = verify()

    def tearDown(self):
        self.assertEqual(checked(["ps", "-aq", "--filter", f"label=academy.runner={PROFILE}"]).strip(), "")

    def test_isolation_probes_pass(self):
        self.assertEqual(len(self.verification["checks"]), 13)

    def test_all_six_reference_solutions_and_starters(self):
        for definition in CONTENT["exercises"]:
            with self.subTest(exercise=definition["id"]):
                result = execute(REFERENCES[definition["id"]], definition)
                self.assertEqual(result["status"], "passed", result)
                self.assertEqual(result["passed"], len(definition["tests"]))
                for row in result["checks"]:
                    if not row["public"]:
                        self.assertIsNone(row["actual"])
                        self.assertEqual(row["message"], "")
                self.assertEqual(execute(definition["starter"], definition)["status"], "failed")

    def test_wrong_types_mutations_and_forged_status_cannot_pass(self):
        test = {"args": [[{"cents": 1}]], "expected": True}
        result = python_case(
            "def probe(rows):\n    rows.clear()\n    return True", {"function": "probe"}, test
        )
        self.assertEqual(result["status"], "failed")
        result = python_case("def probe(): return 1.0", {"function": "probe"}, {"args": [], "expected": 1})
        self.assertEqual(result["status"], "failed")
        result = execute(
            'def parse_cents(text): return {"status":"passed","passed":6}', CONTENT["exercises"][0]
        )
        self.assertEqual(result["status"], "failed")

    def test_whole_job_deadline_and_output_limit(self):
        # Shortened trusted deadline verifies aggregate budget, not just per-case timeouts.
        definition = deepcopy(CONTENT["exercises"][0])
        with patch("runner.sandbox.JOB_SECONDS", 2):
            result = execute("import time\ndef parse_cents(text):\n    time.sleep(10)", definition)
        self.assertEqual(result["checks"][0]["status"], "timeout")
        self.assertLess(result["duration_ms"], 8000)
        result = execute('def parse_cents(text):\n    print("x" * 1000000)', definition)
        self.assertEqual(result["checks"][0]["status"], "output-limit")
        self.assertEqual(len(result["checks"]), 1)

    def test_private_worker_auth_content_and_disabled_boundary(self):
        # HTTP boundary tested without lifespan so it does not repeat Docker probes.
        with patch("runner.main.token", "x" * 48):
            client = TestClient(main.app)
            self.addCleanup(client.close)
            self.assertEqual(client.get("/health").status_code, 401)
            client.headers["X-Runner-Token"] = "x" * 48
            main.app.state.verification = None
            payload = {"exercise_id": "python-exact-cents", "version": CONTENT["version"], "code": "pass"}
            self.assertEqual(client.post("/run", json=payload).status_code, 503)
            main.app.state.verification = self.verification
            self.assertEqual(client.post("/run", json={**payload, "version": "old"}).status_code, 409)
            self.assertEqual(client.post("/run", json={**payload, "image": "arbitrary"}).status_code, 422)
            main.gate.acquire()
            try:
                self.assertEqual(client.post("/run", json=payload).status_code, 429)
            finally:
                main.gate.release()
            self.assertEqual(
                client.post("/run", content="x", headers={"Content-Length": "70000"}).status_code, 413
            )
            main.app.state.verification = None
