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
from uuid import uuid4
from fastapi.testclient import TestClient
import test_academy
from app.main import app
from app.content import lessons
from app.interactivity import interaction_content, sections_for
from app.models import ExerciseAttempt, LessonCheckpointAttempt, utcnow


class InteractiveTests(unittest.TestCase):
    setUp = test_academy.AcademyTests.setUp
    tearDown = test_academy.AcademyTests.tearDown
    register = test_academy.AcademyTests.register
    other_learner = test_academy.AcademyTests.other_learner

    def payload(self, lesson="python-values", which=0, **changes):
        q = interaction_content()["lessons"][lesson]["checkpoints"][which]
        return {
            "answer": q["answer"],
            "version": interaction_content()["version"],
            "request_key": str(uuid4()),
            **changes,
        }

    def record(self, lesson="python-values", which=0, **changes):
        q = interaction_content()["lessons"][lesson]["checkpoints"][which]
        r = self.client.post(
            f"/api/lesson-activities/{lesson}/checkpoints/{q['id']}/attempts",
            json=self.payload(lesson, which, **changes),
        )
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def test_authentication_account_scoped_history_and_private_keys(self):
        with TestClient(app) as anonymous:
            for path in ["/api/glossary", "/api/lesson-activities/python-values"]:
                self.assertEqual(anonymous.get(path).status_code, 401)
        active = self.client.get("/api/lesson-activities/python-values").json()
        self.assertEqual(active["history"], [])
        for key in ["answer", "explanation", "validation", "definition_snapshot"]:
            self.assertNotIn(f'"{key}"', json.dumps(active))
        mine = self.record()
        self.assertEqual(self.client.get("/api/lesson-activities/python-values").json()["history"], [mine])
        self.assertEqual(
            self.other_learner().get("/api/lesson-activities/python-values").json()["history"], []
        )

    def test_strict_answers_version_uuid_and_lesson_membership(self):
        endpoint = "/api/lesson-activities/python-values/checkpoints/python-values-predict/attempts"
        for change in [
            {"answer": True},
            {"answer": "1"},
            {"answer": -1},
            {"answer": 3},
            {"answer": 6},
            {"request_key": "bad"},
            {"score": 100},
            {"user_id": 2},
            {"version": True},
        ]:
            r = self.client.post(endpoint, json=self.payload(**change))
            self.assertEqual(r.status_code, 422, r.text)
        self.assertEqual(self.client.post(endpoint, json=self.payload(version="old")).status_code, 409)
        self.assertEqual(self.client.get("/api/lesson-activities/missing").status_code, 404)
        self.assertEqual(
            self.client.post(
                "/api/lesson-activities/python-values/checkpoints/python-start-predict/attempts",
                json=self.payload(),
            ).status_code,
            404,
        )

    def test_correct_wrong_fixed_feedback_and_no_mastery_or_reading_changes(self):
        q = interaction_content()["lessons"]["python-values"]["checkpoints"][0]
        wrong = self.record(answer=(q["answer"] + 1) % 3)
        self.assertFalse(wrong["result"]["correct"])
        right = self.record()
        self.assertTrue(right["result"]["correct"])
        self.assertEqual(right["result"]["expected"], "12")
        dashboard = self.client.get("/api/dashboard").json()
        self.assertEqual(dashboard["mastery"], 0)
        self.assertEqual(dashboard["completed_lessons"], 0)
        self.assertEqual(dashboard["attempts"], 0)
        self.assertEqual(self.client.get("/api/reviews").json(), [])
        self.assertEqual(self.client.get("/api/recall").json()["summary"]["fresh_delayed"]["total"], 0)

    def test_network_retry_is_idempotent_and_conflicting_key_is_rejected(self):
        endpoint = "/api/lesson-activities/python-values/checkpoints/python-values-predict/attempts"
        payload = self.payload()
        first = self.client.post(endpoint, json=payload).json()
        self.assertEqual(self.client.post(endpoint, json=payload).json(), first)
        changed = {**payload, "answer": (payload["answer"] + 1) % 3}
        self.assertEqual(self.client.post(endpoint, json=changed).status_code, 409)
        self.assertEqual(len(self.client.get("/api/lesson-activities/python-values").json()["history"]), 1)

    def test_history_and_successful_retry_keep_pinned_question_after_content_change(self):
        payload = self.payload()
        saved = self.record(**payload)
        modified = deepcopy(interaction_content())
        modified["version"] = "future"
        modified["lessons"]["python-values"]["checkpoints"][0]["explanation"] = "changed"
        modified["lessons"]["python-values"]["checkpoints"] = []
        with patch("app.interactivity.interaction_content", return_value=modified):
            r = self.client.post(
                "/api/lesson-activities/python-values/checkpoints/python-values-predict/attempts",
                json=payload,
            )
            self.assertEqual(r.json(), saved)
            history = self.client.get("/api/lesson-activities/python-values").json()["history"]
            self.assertEqual(history, [saved])
        self.assertNotEqual(saved["result"]["explanation"], "changed")

    def copies(self, n, age=0):
        original = self.record()
        with self.factory.begin() as db:
            source = db.get(LessonCheckpointAttempt, original["id"])
            for _ in range(n):
                db.add(
                    LessonCheckpointAttempt(
                        user_id=source.user_id,
                        lesson_id=source.lesson_id,
                        checkpoint_id=source.checkpoint_id,
                        request_key=str(uuid4()),
                        answer=source.answer,
                        definition_snapshot=deepcopy(source.definition_snapshot),
                        result=deepcopy(source.result),
                        created_at=utcnow() - timedelta(days=age),
                    )
                )
        return original

    def test_attempt_quota_preserves_saved_feedback_and_retry(self):
        self.copies(39)
        payload = self.payload()
        endpoint = "/api/lesson-activities/python-values/checkpoints/python-values-predict/attempts"
        self.assertEqual(self.client.post(endpoint, json=payload).status_code, 429)
        with self.factory() as db:
            source = db.get(LessonCheckpointAttempt, 1)
            replay = self.payload(
                answer=source.answer,
                version=source.definition_snapshot["version"],
                request_key=source.request_key,
            )
        self.assertEqual(self.client.post(endpoint, json=replay).status_code, 201)
        self.assertEqual(len(self.client.get("/api/lesson-activities/python-values").json()["history"]), 40)

    def test_recent_history_is_bounded_without_deleting_older_attempts(self):
        self.copies(54, age=1)
        response = self.client.get("/api/lesson-activities/python-values").json()
        self.assertEqual(response["history_limit"], 50)
        self.assertEqual(len(response["history"]), 50)
        with self.factory() as db:
            self.assertEqual(len(list(db.query(LessonCheckpointAttempt))), 55)

    def test_sections_skip_code_fences_and_navigation_stays_in_published_track(self):
        sample = "## First `value`\n```python\n## not a heading\n```\n## Last\n"
        self.assertEqual(
            sections_for(sample),
            [{"id": "lesson-section-1", "title": "First value"}, {"id": "lesson-section-2", "title": "Last"}],
        )
        for lesson in lessons():
            data = self.client.get(f"/api/lessons/{lesson['id']}").json()
            self.assertTrue(data["sections"])
            for direction in ["previous", "next"]:
                link = data["navigation"][direction]
                if link:
                    target = next(item for item in lessons() if item["id"] == link["id"])
                    self.assertEqual(target["track_id"], lesson["track_id"])
        values = self.client.get("/api/lessons/python-values").json()
        self.assertEqual(values["navigation"]["previous"]["id"], "python-start")
        self.assertEqual(values["navigation"]["next"]["id"], "python-collections")

    def test_glossary_links_and_global_search(self):
        data = self.client.get("/api/glossary").json()
        self.assertEqual(len(data["terms"]), len(interaction_content()["glossary"]))
        term = next(t for t in data["terms"] if t["id"] == "idempotency-key")
        self.assertEqual(term["lessons"][0]["id"], "http-idempotency")
        self.assertTrue(
            any(
                r["href"] == "/glossary#idempotency-key"
                for r in self.client.get("/api/search?q=idempotency%20key").json()
            )
        )

    def test_guided_submission_schedules_exposure_without_inventing_mistakes(self):
        self.record(answer=0)
        data = self.client.get("/api/recall").json()
        topic = next(t for t in data["topics"] if t["id"] == "python-values")
        self.assertFalse(topic["due"])
        self.assertEqual(topic["incorrect"], 0)
        self.assertEqual(topic["source_recognition"]["total"], 0)
        self.assertEqual(topic["fresh_delayed"]["total"], 0)
        self.assertEqual(
            self.client.post(
                "/api/recall/topics/python-values/sessions", json={"mode": "delayed"}
            ).status_code,
            409,
        )

    def test_checkpoint_during_delayed_check_is_observed_assistance(self):
        source = self.client.post("/api/exercises/python-values-check-1/attempts", json={"answer": 0}).json()
        with self.factory.begin() as db:
            db.get(ExerciseAttempt, source["id"]).created_at = utcnow() - timedelta(days=2)
        active = self.client.post(
            "/api/recall/topics/python-values/sessions", json={"mode": "delayed"}
        ).json()
        self.record()
        done = self.client.post(
            f"/api/recall/sessions/{active['id']}/submit", json={"answer": "63", "used_help": False}
        ).json()
        self.assertTrue(done["result"]["observed_study"])
        self.assertEqual(done["result"]["evidence_kind"], "assisted")
        self.assertEqual(
            self.client.get("/api/recall/topics/python-values").json()["topic"]["fresh_delayed"]["total"], 0
        )


class InteractiveContentTests(unittest.TestCase):
    def test_all_published_lessons_have_real_unique_tasks_diagrams_and_defined_terms(self):
        bank = interaction_content()
        self.assertEqual(set(bank["lessons"]), {item["id"] for item in lessons()})
        glossary = {t["id"]: t for t in bank["glossary"]}
        ids = []
        prompts = []
        for lesson_id, bundle in bank["lessons"].items():
            self.assertEqual([q["kind"] for q in bundle["checkpoints"]], ["predict", "debug"])
            self.assertEqual(len(bundle["diagram"]["steps"]), 3)
            for step in bundle["diagram"]["steps"]:
                self.assertTrue(step["label"] and step["detail"])
            for term in bundle["glossary_ids"]:
                self.assertIn(lesson_id, glossary[term]["lesson_ids"])
            for q in bundle["checkpoints"]:
                ids.append(q["id"])
                prompts.append(q["prompt"] + "\n" + q["code"])
                self.assertEqual(len(set(q["options"])), 3)
                self.assertIn(q["answer"], range(3))
                self.assertTrue(q["explanation"] and q["code"])
        self.assertEqual(len(ids), 2 * len(lessons()))
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(len(set(prompts)), len(ids))

    def test_trusted_prediction_outputs_match_authored_choices(self):
        questions = [
            q
            for b in interaction_content()["lessons"].values()
            for q in b["checkpoints"]
            if "validation" in q
        ]
        self.assertGreaterEqual(len(questions), 15)
        for q in questions:
            with self.subTest(id=q["id"]):
                result = subprocess.run(
                    [sys.executable, "-I", "-c", q["validation"]], text=True, capture_output=True, timeout=5
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                expected = q["options"][q["answer"]].replace(", then ", "\n")
                self.assertEqual(result.stdout.strip(), expected)


class InteractiveMigrationTests(unittest.TestCase):
    def test_upgrade_downgrade_preserves_account_recall_and_coding_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "migration.db"
            env = {**os.environ, "DATABASE_URL": f"sqlite:///{path}"}

            def migrate(*args):
                r = subprocess.run(
                    [sys.executable, "-m", "alembic", *args], env=env, text=True, capture_output=True
                )
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

            migrate("upgrade", "f064de537b42")
            with closing(sqlite3.connect(path)) as db, db:
                db.execute("INSERT INTO users VALUES (1,'kept@example.com','Kept','unchanged','2026-09-30')")
                db.execute(
                    "INSERT INTO coding_attempts VALUES (1,1,'exercise','key','fixed source','{}','{}','2026-09-30')"
                )
                db.execute(
                    "INSERT INTO recall_sessions VALUES (1,1,'python-values',NULL,'qid','submitted','practice','{}','63',0,'{}','2026-09-30','2026-09-30','2026-09-30')"
                )
            migrate("upgrade", "head")
            migrate("check")
            with closing(sqlite3.connect(path)) as db, db:
                db.execute(
                    "INSERT INTO lesson_checkpoint_attempts VALUES (1,1,'python-values','qid','uuid',0,'{}','{}','2026-09-30')"
                )
            migrate("downgrade", "f064de537b42")
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute("SELECT name FROM users").fetchone()[0], "Kept")
                self.assertEqual(db.execute("SELECT code FROM coding_attempts").fetchone()[0], "fixed source")
                self.assertEqual(db.execute("SELECT answer FROM recall_sessions").fetchone()[0], "63")
            migrate("upgrade", "head")
            migrate("check")
