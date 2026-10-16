"""Real privacy/recovery behavior; no production email/provider fixtures."""

import json
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import select
import test_academy as helpers
from app.main import app
from app.models import AccountRecoveryKey, ExamAttempt
from app.auth import token_digest

PASSWORD = "a-long-test-passphrase"
NEW_PASSWORD = "a-different-test-passphrase"


class EverydayTests(unittest.TestCase):
    setUp = helpers.AcademyTests.setUp
    tearDown = helpers.AcademyTests.tearDown
    register = helpers.AcademyTests.register
    other_learner = helpers.AcademyTests.other_learner

    def key(self):
        response = self.client.post("/api/account/recovery-key", json={"current_password": PASSWORD})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["recovery_key"]

    def reset(self, key, **changes):
        return self.client.post(
            "/api/account/recover",
            json={
                "email": "learner@example.com",
                "recovery_key": key,
                "new_password": NEW_PASSWORD,
                "confirm_password": NEW_PASSWORD,
                **changes,
            },
        )

    def test_key_is_hashed_rotated_one_use_and_every_session_revoked(self):
        first = self.key()
        second = self.key()
        self.assertNotEqual(first, second)
        with self.factory() as db:
            key = db.scalar(select(AccountRecoveryKey))
            self.assertEqual(key.token_hash, token_digest(second))
            self.assertNotIn(second, json.dumps({"hash": key.token_hash}))
        other = TestClient(app, headers={"X-Academy-Request": "1"})
        self.addCleanup(other.close)
        self.assertEqual(
            other.post(
                "/api/auth/login", json={"email": "learner@example.com", "password": PASSWORD}
            ).status_code,
            200,
        )
        self.assertEqual(self.reset(first).status_code, 401)
        self.assertEqual(self.reset(second, confirm_password="mismatched-new-passphrase").status_code, 422)
        result = self.reset(second)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(other.get("/api/auth/me").status_code, 401)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.assertEqual(self.reset(second).status_code, 401)
        self.assertEqual(
            self.client.post(
                "/api/auth/login", json={"email": "learner@example.com", "password": PASSWORD}
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.post(
                "/api/auth/login", json={"email": "learner@example.com", "password": NEW_PASSWORD}
            ).status_code,
            200,
        )
        self.assertFalse(self.client.get("/api/account").json()["recovery_enabled"])
        with self.factory() as db:
            self.assertIsNotNone(db.scalar(select(AccountRecoveryKey)).used_at)

    def test_key_requires_password_strict_inputs_and_consistent_failed_recovery(self):
        key = self.key()
        self.assertEqual(
            self.client.post(
                "/api/account/recovery-key", json={"current_password": "incorrect-passphrase"}
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.post(
                "/api/account/recovery-key", json={"current_password": PASSWORD, "user_id": 99}
            ).status_code,
            422,
        )
        wrong = "academy-recovery-" + "a" * 43
        known = self.reset(wrong)
        unknown = self.reset(wrong, email="missing@example.com")
        self.assertEqual(known.status_code, unknown.status_code)
        self.assertEqual(known.json(), unknown.json())
        self.assertEqual(
            self.client.request(
                "DELETE", "/api/account/recovery-key", json={"current_password": PASSWORD}
            ).status_code,
            204,
        )
        self.assertEqual(self.reset(key).status_code, 401)

    def test_password_change_and_session_control_are_owned(self):
        key = self.key()
        other = self.other_learner()
        foreign = other.get("/api/account/sessions").json()[0]["id"]
        self.assertEqual(self.client.delete("/api/account/sessions/" + foreign).status_code, 404)
        current = self.client.get("/api/account/sessions").json()[0]
        self.assertTrue(current["current"])
        self.assertEqual(len(current["id"]), 24)
        self.assertNotIn("token_hash", current)
        result = self.client.post(
            "/api/account/password",
            json={
                "current_password": PASSWORD,
                "new_password": NEW_PASSWORD,
                "confirm_password": NEW_PASSWORD,
            },
        )
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.assertEqual(self.reset(key).status_code, 401)
        self.assertEqual(other.get("/api/auth/me").status_code, 200)

    def test_export_carries_owned_drafts_and_evidence_without_active_keys_or_credentials(self):
        self.key()
        other = self.other_learner()
        self.client.put("/api/lessons/python-values/note", json={"body": "My own note with `literal code`."})
        other.put("/api/lessons/python-values/note", json={"body": "foreign private marker"})
        exam = self.client.post("/api/exams/start", json={"exam_id": "python-beginner-v1"}).json()
        self.client.put(
            f"/api/exams/attempts/{exam['id']}/answer",
            json={"question_id": exam["questions"][0]["id"], "answer": 1},
        )
        self.client.put(
            "/api/coding/python-exact-cents/draft", json={"code": "def parse_cents(text):\n    return 0\n"}
        )
        with self.factory.begin() as db:
            row = db.get(ExamAttempt, exam["id"])
            snapshot = dict(row.definition_snapshot)
            snapshot["private_export_marker"] = "hidden key marker"
            row.definition_snapshot = snapshot
        result = self.client.get("/api/account/export?format=json")
        self.assertEqual(result.status_code, 200, result.text)
        data = result.json()
        self.assertEqual(data["format"], "academy-evidence-v1")
        self.assertTrue(data["coding_drafts"])
        self.assertEqual(data['notes'][0]['body'], 'My own note with `literal code`.')
        self.assertEqual(data["exams"][0]["answers"], {exam["questions"][0]["id"]: 1})
        self.assertIsNone(data["exams"][0]["result"])
        self.assertNotIn("hidden key marker", result.text)
        self.assertNotIn("foreign private marker", result.text)

        def check(value):
            if isinstance(value, dict):
                self.assertFalse(
                    {"definition_snapshot", "password_hash", "token_hash", "recovery_key"} & value.keys()
                )
                for v in value.values():
                    check(v)
            elif isinstance(value, list):
                for v in value:
                    check(v)

        check(data)
        for question in data["exams"][0]["questions"]:
            self.assertNotIn("answer", question)
            self.assertNotIn("explanation", question)
        markdown = self.client.get("/api/account/export?format=markdown")
        self.assertEqual(markdown.status_code, 200)
        self.assertIn("# Engineering Academy", markdown.text)
        self.assertIn("attachment;", markdown.headers["content-disposition"])
        anonymous = TestClient(app)
        self.addCleanup(anonymous.close)
        self.assertEqual(anonymous.get("/api/account/export").status_code, 401)
        self.assertEqual(self.client.get("/api/account/export?format=database").status_code, 422)
        self.assertNotIn("hash_password", result.text)

    def test_body_is_bounded_and_recovery_uses_auth_throttle(self):
        self.assertEqual(
            self.client.post("/api/account/recover", content=b" " * (262144 + 1)).status_code, 413
        )
        for _ in range(19):
            self.client.post("/api/account/recover", json={})
        self.assertEqual(self.client.post("/api/account/recover", json={}).status_code, 429)
