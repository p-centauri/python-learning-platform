from contextlib import closing
from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4
from unittest.mock import patch
import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select
import test_academy
from app.main import app
from app.coding import coding_content, runner_request
from app.models import CodingAttempt


class CodingTests(unittest.TestCase):
    setUp = test_academy.AcademyTests.setUp
    tearDown = test_academy.AcademyTests.tearDown
    register = test_academy.AcademyTests.register
    other_learner = test_academy.AcademyTests.other_learner
    path = "/api/coding/python-exact-cents"

    def payload(self, **changes):
        return {
            "code": "def parse_cents(text): return 1",
            "request_key": str(uuid4()),
            "version": coding_content()["version"],
            **changes,
        }

    def result(self):
        tests = coding_content()["exercises"][0]["tests"]
        return {
            "status": "passed",
            "passed": len(tests),
            "total": len(tests),
            "checks": [
                {"status": "passed", "actual": "private-canary", "message": "private-canary"} for t in tests
            ],
            "duration_ms": 12,
            "profile": "test-only",
        }

    def test_authentication_draft_save_offline_and_isolation(self):
        with TestClient(app) as anonymous:
            self.assertEqual(anonymous.get("/api/coding").status_code, 401)
        with patch("app.coding.runner_request", side_effect=HTTPException(503, "Offline")):
            self.assertFalse(self.client.get(self.path).json()["runner"]["ready"])
            self.assertFalse(self.client.get(self.path).json()["draft_saved"])
            self.assertEqual(
                self.client.put(self.path + "/draft", json={"code": "saved thought"}).status_code, 200
            )
            self.assertEqual(self.client.get(self.path).json()["code"], "saved thought")
            self.assertTrue(self.client.get(self.path).json()["draft_saved"])
            self.assertNotEqual(self.other_learner().get(self.path).json()["code"], "saved thought")
        self.assertEqual(self.client.get("/api/coding/missing").status_code, 404)

    def test_private_cases_and_answers_never_enter_public_definitions(self):
        with patch("app.coding.runner_request", side_effect=HTTPException(503, "Offline")):
            catalog = self.client.get("/api/coding").json()
        self.assertEqual(len(catalog["exercises"]), 6)
        self.assertEqual(sum(e["check_count"] for e in catalog["exercises"]), 25)
        for definition, public in zip(coding_content()["exercises"], catalog["exercises"]):
            self.assertEqual(len(public["examples"]), sum(t["public"] for t in definition["tests"]))
            self.assertNotIn("tests", public)
            self.assertNotIn("function", public)
        self.assertNotIn("0003.07", json.dumps(catalog))

    def test_strict_code_size_version_uuid_and_no_client_grades(self):
        for code in [True, "😀" * 5000, "x" * 12001]:
            self.assertEqual(self.client.put(self.path + "/draft", json={"code": code}).status_code, 422)
        for changes, status in [
            ({"code": " "}, 422),
            ({"version": "old"}, 409),
            ({"request_key": "bad"}, 422),
            ({"passed": 6}, 422),
            ({"user_id": 2}, 422),
        ]:
            self.assertEqual(
                self.client.post(self.path + "/attempts", json=self.payload(**changes)).status_code, status
            )
        self.assertEqual(self.client.put(self.path + "/draft", json={"code": ""}).status_code, 200)

    def test_fixed_history_idempotency_privacy_and_no_mastery(self):
        payload = self.payload()
        with patch("app.coding.runner_request", return_value=self.result()) as runner:
            first = self.client.post(self.path + "/attempts", json=payload)
            self.assertEqual(first.status_code, 201, first.text)
            repeated = self.client.post(self.path + "/attempts", json=payload)
            self.assertEqual(repeated.json(), first.json())
            self.assertEqual(runner.call_count, 1)
            self.assertEqual(
                self.client.post(self.path + "/attempts", json={**payload, "code": "different"}).status_code,
                409,
            )
        result = first.json()["result"]
        self.assertTrue(
            all(c["actual"] is None and not c["message"] for c in result["checks"] if not c["public"])
        )
        self.assertNotIn("definition_snapshot", first.json())
        self.client.put(self.path + "/draft", json={"code": "new unfinished draft"})
        with patch("app.coding.runner_request", side_effect=HTTPException(503, "Offline")):
            detail = self.client.get(self.path).json()
            self.assertEqual(detail["attempts"][0]["code"], payload["code"])
            self.assertEqual(self.other_learner().get(self.path).json()["attempts"], [])
        with self.factory() as db:
            self.assertEqual(
                db.scalar(select(CodingAttempt)).definition_snapshot["exercise"],
                coding_content()["exercises"][0],
            )
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)
        self.assertEqual(self.client.get("/api/dashboard").json()["completed_lessons"], 0)

    def test_unavailable_and_invalid_results_do_not_record_grades(self):
        self.client.put(self.path + "/draft", json={"code": "preserved"})
        for result in [
            {},
            {"status": "passed", "passed": 6, "total": 6, "checks": []},
            {**self.result(), "passed": 5},
            {**self.result(), "total": 99},
            {**self.result(), "duration_ms": "bad"},
            {**self.result(), "profile": []},
        ]:
            with patch("app.coding.runner_request", return_value=result):
                self.assertEqual(
                    self.client.post(self.path + "/attempts", json=self.payload()).status_code, 503
                )
        with patch("app.coding.runner_request", side_effect=HTTPException(503, "Unavailable")):
            self.assertEqual(self.client.post(self.path + "/attempts", json=self.payload()).status_code, 503)
            detail = self.client.get(self.path).json()
        self.assertEqual(detail["attempts"], [])
        self.assertEqual(detail["code"], "preserved")

    def test_quota_and_retries(self):
        with patch("app.coding.runner_request", return_value=self.result()) as runner:
            first = self.payload()
            for i in range(8):
                response = self.client.post(self.path + "/attempts", json=first if i == 0 else self.payload())
                self.assertEqual(response.status_code, 201, response.text)
            self.assertEqual(self.client.post(self.path + "/attempts", json=self.payload()).status_code, 429)
            self.assertEqual(self.client.post(self.path + "/attempts", json=first).status_code, 201)
            self.assertEqual(runner.call_count, 8)

    def test_content_changes_leave_recorded_snapshot_and_result_fixed(self):
        with patch("app.coding.runner_request", return_value=self.result()):
            first = self.client.post(self.path + "/attempts", json=self.payload()).json()
        modified = deepcopy(coding_content())
        modified["version"] = "future"
        modified["exercises"][0]["tests"][0]["expected"] = 999
        with (
            patch("app.coding.coding_content", return_value=modified),
            patch("app.coding.runner_request", side_effect=HTTPException(503, "Offline")),
        ):
            self.assertEqual(self.client.get(self.path).json()["attempts"][0], first)

    def test_runner_transport_rejects_malformed_json(self):
        with (
            patch("app.coding.settings.runner_url", "http://runner"),
            patch("app.coding.settings.runner_token", "x" * 48),
        ):
            for response in [
                httpx.Response(503, text="html"),
                httpx.Response(200, json=[]),
                httpx.Response(200, json={}),
            ]:
                with patch("app.coding.httpx.request", return_value=response):
                    if response.text == "{}":
                        self.assertEqual(runner_request("/run", {}), {})
                    else:
                        with self.assertRaises(HTTPException) as caught:
                            runner_request("/run", {})
                        self.assertEqual(caught.exception.status_code, 503)


class CodingMigrationTests(unittest.TestCase):
    def test_preserve_projects_accounts_and_plans_through_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "migration.db"
            env = {**os.environ, "DATABASE_URL": f"sqlite:///{path}"}

            def migrate(*args):
                result = subprocess.run(
                    [sys.executable, "-m", "alembic", *args], env=env, capture_output=True, text=True
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            migrate("upgrade", "d842bc315f20")
            with closing(sqlite3.connect(path)) as db, db:
                db.execute("INSERT INTO users VALUES (1,'kept@example.com','Kept','unchanged','2026-09-30')")
                db.execute(
                    "INSERT INTO learning_preferences VALUES (1,'python',3,'recommended','2026-09-30')"
                )
                db.execute(
                    "INSERT INTO project_submissions VALUES (1,1,'python-expenses',1,NULL,'submitted','{}','{}','2026-09-30','2026-09-30','2026-09-30')"
                )
            migrate("upgrade", "head")
            migrate("check")
            with closing(sqlite3.connect(path)) as db, db:
                db.execute(
                    "INSERT INTO coding_drafts VALUES (1,1,'python-exact-cents','source','2026-09-30')"
                )
            migrate("downgrade", "d842bc315f20")
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute("SELECT name FROM users").fetchone()[0], "Kept")
                self.assertEqual(db.execute("SELECT weekly_hours FROM learning_preferences").fetchone()[0], 3)
                self.assertEqual(
                    db.execute("SELECT status FROM project_submissions").fetchone()[0], "submitted"
                )
            migrate("upgrade", "head")
            migrate("check")
