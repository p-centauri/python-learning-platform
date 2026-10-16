from contextlib import closing
from copy import deepcopy
from datetime import timedelta
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
import test_academy
from app.main import app
from app.content import lessons, exercise_by_id
from app.models import ExerciseAttempt, utcnow
from app.retention import review_content


class RetentionTests(unittest.TestCase):
    setUp = test_academy.AcademyTests.setUp
    tearDown = test_academy.AcademyTests.tearDown
    register = test_academy.AcademyTests.register
    other_learner = test_academy.AcademyTests.other_learner
    topic = "python-values"

    def source(self, days=2, correct=False, exercise="python-values-check-1"):
        _, definition = exercise_by_id(exercise)
        response = self.client.post(
            f"/api/exercises/{exercise}/attempts",
            json={
                "answer": definition["answer"]
                if correct
                else (definition["answer"] + 1) % len(definition["options"])
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        with self.factory.begin() as db:
            db.get(ExerciseAttempt, response.json()["id"]).created_at = utcnow() - timedelta(days=days)
        return response.json()["id"]

    def begin(self, mode="practice", topic=None):
        response = self.client.post(f"/api/recall/topics/{topic or self.topic}/sessions", json={"mode": mode})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def answer(self, session, answer="63", used_help=False):
        response = self.client.post(
            f"/api/recall/sessions/{session['id']}/submit", json={"answer": answer, "used_help": used_help}
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def detail(self):
        return self.client.get(f"/api/recall/topics/{self.topic}").json()

    def test_empty_evidence_full_coverage_and_no_answers_in_catalog(self):
        data = self.client.get("/api/recall").json()
        self.assertEqual(data["topics"], [])
        self.assertEqual(len(data["catalog"]), len(lessons()))
        self.assertEqual(data["summary"]["fresh_delayed"], {"correct": 0, "total": 0})
        for forbidden in ["accepted", "explanation", "validation", "definition_snapshot", "options"]:
            self.assertNotIn(f'"{forbidden}"', json.dumps(data))
        self.assertFalse(self.detail()["topic"]["due"])

    def test_authentication_and_ownership_for_every_mutation(self):
        with TestClient(app) as anonymous:
            self.assertEqual(anonymous.get("/api/recall").status_code, 401)
        row = self.begin()
        other = self.other_learner()
        self.assertIsNone(other.get("/api/recall/topics/python-values").json()["active"])
        for method, suffix, data in [
            ("get", "", None),
            ("put", "", {"answer": "63", "used_help": False}),
            ("post", "/submit", {"answer": "63", "used_help": False}),
            ("post", "/discard", None),
        ]:
            r = getattr(other, method)(
                f"/api/recall/sessions/{row['id']}{suffix}", **({"json": data} if data else {})
            )
            self.assertEqual(r.status_code, 404)
        self.assertEqual(self.client.get("/api/recall/topics/missing").status_code, 404)

    def test_recorded_mistakes_recur_without_inventing_diagnoses(self):
        self.source()
        self.assertFalse(self.detail()["topic"]["recurring"])
        self.source(days=1.5)
        topic = self.detail()["topic"]
        self.assertEqual(topic["source_incorrect"], 2)
        self.assertEqual(topic["source_questions_missed"], 1)
        self.assertTrue(topic["recurring"])
        self.assertTrue(topic["due"])
        self.assertEqual(self.client.get("/api/recall").json()["summary"]["recurring"], 1)

    def test_active_answer_save_resume_strict_fields_and_no_early_solution(self):
        row = self.begin()
        self.assertEqual(self.begin()["id"], row["id"])
        serialized = json.dumps(row)
        for field in ["accepted", "explanation", "validation", "definition_snapshot", "sources"]:
            self.assertNotIn(f'"{field}"', serialized)
        self.assertIsNone(row["result"])
        payload = {"answer": "  63  ", "used_help": True}
        self.assertEqual(self.client.put(f"/api/recall/sessions/{row['id']}", json=payload).status_code, 200)
        saved = self.client.get(f"/api/recall/sessions/{row['id']}").json()
        self.assertEqual(saved["answer"], payload["answer"])
        self.assertTrue(saved["used_help"])
        for change in [
            {"answer": True},
            {"answer": "x" * 121},
            {"used_help": "false"},
            {"score": 100},
            {"mode": "delayed"},
            {"user_id": 2},
        ]:
            self.assertEqual(
                self.client.put(f"/api/recall/sessions/{row['id']}", json={**payload, **change}).status_code,
                422,
            )
        self.assertEqual(
            self.client.post(
                f"/api/recall/sessions/{row['id']}/submit", json={"answer": " ", "used_help": False}
            ).status_code,
            422,
        )

    def test_immediate_wrong_check_and_unchanged_mastery_and_legacy_schedule(self):
        self.source()
        before = self.client.get("/api/dashboard").json()
        schedule = self.client.get("/api/reviews").json()
        row = self.answer(self.begin(), answer="9")
        self.assertFalse(row["result"]["correct"])
        self.assertEqual(row["result"]["evidence_kind"], "immediate")
        self.assertEqual(row["result"]["expected"], "63")
        self.assertEqual(self.detail()["topic"]["check_incorrect"], 1)
        self.assertEqual(self.detail()["topic"]["fresh_delayed"]["total"], 0)
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], before["mastery"])
        self.assertEqual(self.client.get("/api/reviews").json(), schedule)
        self.assertEqual(self.client.get("/api/dashboard").json()["completed_lessons"], 0)

    def test_delayed_gate_fresh_result_and_bounded_interval(self):
        self.source(days=0)
        self.assertEqual(
            self.client.post(
                "/api/recall/topics/python-values/sessions", json={"mode": "delayed"}
            ).status_code,
            409,
        )
        future = utcnow() + timedelta(days=2)
        with patch("app.retention.utcnow", return_value=future):
            row = self.answer(self.begin("delayed"))
            self.assertTrue(row["result"]["correct"])
            self.assertEqual(row["result"]["evidence_kind"], "fresh-delayed")
            self.assertEqual(row["result"]["interval_days"], 3)
            self.assertFalse(self.detail()["topic"]["due"])
            self.assertEqual(self.detail()["topic"]["fresh_delayed"], {"correct": 1, "total": 1})
        with patch("app.retention.utcnow", return_value=future + timedelta(days=4)):
            second = self.answer(self.begin("delayed"), answer="0")
            self.assertEqual(second["result"]["interval_days"], 6)
        with patch("app.retention.utcnow", return_value=future + timedelta(days=11)):
            repeated = self.answer(self.begin("delayed"))
            self.assertFalse(repeated["fresh"])
            self.assertEqual(repeated["result"]["evidence_kind"], "repeated-delayed")
            self.assertEqual(repeated["result"]["interval_days"], 6)
            self.assertEqual(self.detail()["topic"]["fresh_delayed"]["total"], 2)

    def test_assistance_and_intervening_practice_excluded_from_retention(self):
        self.source()
        row = self.answer(self.begin("delayed"), used_help=True)
        self.assertEqual(row["result"]["evidence_kind"], "assisted")
        self.assertEqual(self.detail()["topic"]["fresh_delayed"]["total"], 0)
        other_topic = "python-ownership"
        self.source(exercise="python-alias")
        row = self.begin("delayed", topic=other_topic)
        self.source(days=0, exercise="python-alias")
        result = self.answer(row, answer="9")["result"]
        self.assertTrue(result["observed_study"])
        self.assertEqual(result["evidence_kind"], "assisted")

    def test_abandoned_question_counts_seen_and_no_grade(self):
        first = self.begin()
        self.client.post(f"/api/recall/sessions/{first['id']}/discard")
        self.assertEqual(
            self.client.post(
                f"/api/recall/sessions/{first['id']}/submit", json={"answer": "63", "used_help": False}
            ).status_code,
            409,
        )
        second = self.begin()
        self.assertNotEqual(second["question"]["id"], first["question"]["id"])
        self.client.post(f"/api/recall/sessions/{second['id']}/discard")
        repeated = self.begin()
        self.assertFalse(repeated["fresh"])
        self.assertEqual(repeated["question"]["id"], first["question"]["id"])
        self.assertEqual(self.detail()["topic"]["fresh_delayed"]["total"], 0)

    def test_future_content_cannot_rewrite_pinned_feedback_and_results(self):
        row = self.begin()
        modified = deepcopy(review_content())
        topic = next(t for t in modified["concepts"] if t["id"] == self.topic)
        topic["questions"][0]["accepted"] = ["999"]
        topic["questions"][0]["explanation"] = "changed"
        modified["version"] = "future"
        with patch("app.retention.review_content", return_value=modified):
            done = self.answer(row, answer=" 63 ")
        self.assertTrue(done["result"]["correct"])
        self.assertEqual(done["version"], row["version"])
        self.assertNotEqual(done["result"]["explanation"], "changed")
        self.assertEqual(self.answer(done, answer="different"), done)
        self.assertEqual(
            self.client.put(
                f"/api/recall/sessions/{done['id']}", json={"answer": "different", "used_help": False}
            ).status_code,
            409,
        )
        self.assertEqual(self.client.post(f"/api/recall/sessions/{done['id']}/discard").status_code, 409)

    def test_new_study_requires_another_gap_and_new_mistake_brings_schedule_forward(self):
        self.source()
        now = utcnow()
        with patch("app.retention.utcnow", return_value=now):
            done = self.answer(self.begin("delayed"))
            next_due = done["result"]["next_due_at"]
        self.source(days=0)
        topic = self.detail()["topic"]
        self.assertLess(topic["due_at"], next_due)
        self.assertFalse(topic["due"])
        with patch("app.retention.utcnow", return_value=now + timedelta(days=1.1)):
            self.assertTrue(self.detail()["topic"]["due"])
            immediate = self.begin()
            self.answer(immediate, answer="0")
            self.assertFalse(self.detail()["topic"]["due"])

    def test_python_values_are_case_sensitive_and_terms_follow_the_stated_policy(self):
        row = self.begin(topic="python-functions")
        self.assertFalse(self.answer(row, answer="none")["result"]["correct"])
        row = self.begin(topic="python-protocols")
        self.assertTrue(self.answer(row, answer=" Protocol ")["result"]["correct"])
        row = self.begin(topic="llm-contracts")
        self.assertTrue(self.answer(row, answer=" NO ")["result"]["correct"])

    def test_exam_answers_and_coding_results_do_not_create_mistakes(self):
        self.client.post("/api/exams/python-beginner-v1/attempts")
        self.assertEqual(self.client.get("/api/recall").json()["topics"], [])
        self.assertEqual(
            self.client.put(
                "/api/coding/python-exact-cents/draft", json={"code": "broken source"}
            ).status_code,
            200,
        )
        self.assertEqual(self.client.get("/api/recall").json()["topics"], [])

    def test_start_quota_and_existing_resume(self):
        first = self.begin()
        for i in range(19):
            if i == 0:
                self.client.post(f"/api/recall/sessions/{first['id']}/discard")
            row = self.begin()
            self.client.post(f"/api/recall/sessions/{row['id']}/discard")
        response = self.client.post("/api/recall/topics/python-values/sessions", json={"mode": "practice"})
        self.assertEqual(response.status_code, 429)

    def test_plan_prioritizes_due_checks_then_resumes_without_duplicate_scenarios(self):
        self.source()
        saved = self.client.put(
            "/api/learning-plan",
            json={"goal": "python", "weekly_hours": 1, "starting_mode": "recommended"},
        )
        self.assertEqual(saved.status_code, 200)
        plan = saved.json()["plan"]
        self.assertEqual(plan["items"][0]["href"], "/review/python-values")
        self.assertLessEqual(plan["scheduled_minutes"], 60)
        self.assertFalse(
            any(item["href"].startswith("/practice/python-values-check") for item in plan["items"])
        )
        row = self.begin("delayed")
        plan = self.client.get("/api/learning-plan").json()["plan"]
        self.assertEqual(plan["items"][0]["href"], f"/review/checks/{row['id']}")
        self.assertIn("Resume", plan["items"][0]["reason"])
        self.answer(row)
        plan = self.client.get("/api/learning-plan").json()["plan"]
        self.assertFalse(any(item["href"].startswith("/review/") for item in plan["items"]))

    def test_plan_excludes_topics_outside_goal_and_never_sends_short_answer_keys(self):
        row = self.begin(topic="rag-evidence")
        response = self.client.put(
            "/api/learning-plan",
            json={"goal": "python", "weekly_hours": 2, "starting_mode": "recommended"},
        ).json()
        self.assertFalse(any(i["href"] == f"/review/checks/{row['id']}" for i in response["plan"]["items"]))
        for private in ['"accepted"', '"explanation"', '"definition_snapshot"', '"question"']:
            self.assertNotIn(private, json.dumps(response))
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)


class RecallContentTests(unittest.TestCase):
    def test_coverage_private_keys_and_distinct_authored_questions(self):
        content = review_content()
        self.assertEqual(len(content["concepts"]), len(lessons()))
        self.assertEqual(
            {t["lesson_id"] for t in content["concepts"]}, {lesson["id"] for lesson in lessons()}
        )
        covered = [key for t in content["concepts"] for key in t["sources"]]
        source = [e["id"] for lesson in lessons() for e in lesson["exercises"]]
        self.assertEqual(sorted(covered), sorted(source))
        questions = [q for t in content["concepts"] for q in t["questions"]]
        self.assertEqual(len(questions), 2 * len(lessons()))
        self.assertEqual(len({q["id"] for q in questions}), len(questions))
        for q in questions:
            self.assertTrue(q["accepted"] and q["explanation"])
            self.assertNotIn("options", q)
            self.assertNotIn(q["prompt"], [e["prompt"] for lesson in lessons() for e in lesson["exercises"]])

    def test_author_owned_prediction_snippets_match_exact_keys(self):
        # Only trusted, authored content executes here, never API/submitted text.
        snippets = [q for t in review_content()["concepts"] for q in t["questions"] if "validation" in q]
        self.assertGreater(len(snippets), 20)
        for q in snippets:
            with self.subTest(question=q["id"]):
                result = subprocess.run(
                    [sys.executable, "-I", "-c", q["validation"]], capture_output=True, text=True, timeout=5
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(result.stdout.strip().casefold(), [a.strip().casefold() for a in q["accepted"]])


class RecallMigrationTests(unittest.TestCase):
    def test_upgrade_downgrade_preserves_coding_projects_and_account_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "migration.db"
            env = {**os.environ, "DATABASE_URL": f"sqlite:///{path}"}

            def migrate(*args):
                r = subprocess.run(
                    [sys.executable, "-m", "alembic", *args], env=env, capture_output=True, text=True
                )
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

            migrate("upgrade", "e953cd426a31")
            with closing(sqlite3.connect(path)) as db, db:
                db.execute("INSERT INTO users VALUES (1,'kept@example.com','Kept','unchanged','2026-09-30')")
                db.execute(
                    "INSERT INTO learning_preferences VALUES (1,'python',3,'recommended','2026-09-30')"
                )
                db.execute(
                    "INSERT INTO coding_drafts VALUES (1,1,'python-exact-cents','kept source','2026-09-30')"
                )
                db.execute(
                    "INSERT INTO coding_attempts VALUES (1,1,'python-exact-cents','key','fixed source','{}','{}','2026-09-30')"
                )
                db.execute(
                    "INSERT INTO project_submissions VALUES (1,1,'python-expenses',1,NULL,'submitted','{}','{}','2026-09-30','2026-09-30','2026-09-30')"
                )
            migrate("upgrade", "head")
            migrate("check")
            with closing(sqlite3.connect(path)) as db, db:
                db.execute(
                    "INSERT INTO recall_sessions VALUES (1,1,'python-values','python-values','qid','active','practice','{}','',0,NULL,'2026-09-30','2026-09-30',NULL)"
                )
            migrate("downgrade", "e953cd426a31")
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute("SELECT name FROM users").fetchone()[0], "Kept")
                self.assertEqual(db.execute("SELECT weekly_hours FROM learning_preferences").fetchone()[0], 3)
                self.assertEqual(db.execute("SELECT code FROM coding_drafts").fetchone()[0], "kept source")
                self.assertEqual(db.execute("SELECT code FROM coding_attempts").fetchone()[0], "fixed source")
                self.assertEqual(
                    db.execute("SELECT status FROM project_submissions").fetchone()[0], "submitted"
                )
            migrate("upgrade", "head")
            migrate("check")
