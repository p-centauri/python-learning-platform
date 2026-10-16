from contextlib import closing
from datetime import timedelta
from types import SimpleNamespace
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import select
import test_academy
from app.main import app
from app.content import lessons
from app.models import ExamAttempt, LearningPreferences, ReviewItem, utcnow
from app.study_plan import plan_content, route_for, build_plan


class PlanTests(unittest.TestCase):
    setUp = test_academy.AcademyTests.setUp
    tearDown = test_academy.AcademyTests.tearDown
    register = test_academy.AcademyTests.register
    other_learner = test_academy.AcademyTests.other_learner

    def save(self, **changes):
        payload = {"goal": "python", "weekly_hours": 1, "starting_mode": "recommended", **changes}
        response = self.client.put("/api/learning-plan", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def exam(self, skill="Collections", correct=1, total=4, **changes):
        with self.factory.begin() as db:
            row = ExamAttempt(
                user_id=1,
                exam_id="python-beginner-v1",
                status="submitted",
                definition_snapshot={
                    "title": "Saved Python test",
                    "questions": [{"answer": 3, "explanation": "private"}],
                },
                answers={"private": 3},
                result={
                    "score": 25,
                    "categories": [{"skill": skill, "correct": correct, "total": total}],
                    "evaluation": {"meets_target": False},
                    "explanations": [{"answer": 3}],
                },
                submitted_at=utcnow(),
                **changes,
            )
            db.add(row)
            db.flush()
            return row.id

    def test_authentication_and_strict_input(self):
        with TestClient(app) as anonymous:
            self.assertEqual(anonymous.get("/api/learning-plan").status_code, 401)
        for change in [
            {"weekly_hours": 0},
            {"weekly_hours": 21},
            {"weekly_hours": True},
            {"weekly_hours": 1.5},
            {"weekly_hours": "3"},
            {"goal": "unknown"},
            {"starting_mode": "skip"},
            {"user_id": 2},
        ]:
            payload = {"goal": "python", "weekly_hours": 3, **change}
            self.assertEqual(self.client.put("/api/learning-plan", json=payload).status_code, 422)
        self.assertIsNone(self.client.get("/api/learning-plan").json()["preferences"])

    def test_preferences_persist_update_and_are_isolated(self):
        self.assertIsNone(self.client.get("/api/learning-plan").json()["plan"])
        saved = self.save(goal="backend", weekly_hours=3)
        self.assertEqual(saved, self.client.get("/api/learning-plan").json())
        self.assertIsNone(self.other_learner().get("/api/learning-plan").json()["preferences"])
        self.save(goal="applied-ai", weekly_hours=8, starting_mode="from-start")
        with self.factory() as db:
            self.assertEqual(len(list(db.scalars(select(LearningPreferences)))), 1)
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)
        self.assertEqual(self.client.get("/api/dashboard").json()["completed_lessons"], 0)

    def test_goals_budget_and_prerequisite_order(self):
        for goal in plan_content()["goals"]:
            result = self.save(goal=goal["id"], weekly_hours=2)["plan"]
            self.assertGreater(len(result["items"]), 0)
            self.assertLessEqual(sum(item["minutes"] for item in result["items"]), 120)
            route = [item["id"] for item in result["route"]]
            self.assertEqual(len(route), len(set(route)))
            for lesson in route_for(goal, lessons()):
                for prerequisite in lesson["prerequisites"]:
                    self.assertLess(route.index(prerequisite), route.index(lesson["id"]))
            if goal["id"] == "python":
                self.assertNotIn("rag-evidence", route)
            if goal["id"] == "applied-ai":
                self.assertIn("rag-evidence", route)
        self.assertTrue(
            all(
                key in {lesson["id"] for lesson in lessons()}
                for key in plan_content()["topic_lessons"].values()
            )
        )

    def test_reading_then_practice_moves_queue_without_inventing_mastery(self):
        first = self.save()["plan"]["items"][0]
        self.assertEqual(first["id"], "python-start")
        self.client.put("/api/lessons/python-start/complete")
        plan = self.client.get("/api/learning-plan").json()["plan"]
        self.assertEqual(plan["items"][0]["kind"], "practice")
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)
        for exercise in lessons()[0]["exercises"]:
            self.client.post(f"/api/exercises/{exercise['id']}/attempts", json={"answer": exercise["answer"]})
        plan = self.client.get("/api/learning-plan").json()["plan"]
        self.assertEqual(plan["items"][0]["id"], "python-values")

    def test_submitted_weak_topics_explain_start_and_never_leak_answers(self):
        self.exam()
        data = self.save()
        self.assertEqual(data["plan"]["starting_point"]["id"], "python-collections")
        self.assertIn("1/4", data["plan"]["starting_point"]["reason"])
        serialized = json.dumps(data)
        for field in ['"answers"', '"questions"', '"explanations"', '"definition_snapshot"']:
            self.assertNotIn(field, serialized)
        self.assertEqual(self.client.get("/api/dashboard").json()["completed_lessons"], 0)
        plan = self.save(starting_mode="from-start")["plan"]
        self.assertEqual(plan["items"][0]["id"], "python-start")

    def test_latest_submitted_result_wins_and_active_is_ignored(self):
        self.exam()
        with self.factory.begin() as db:
            db.add(
                ExamAttempt(
                    user_id=1,
                    exam_id="python-beginner-v1",
                    status="submitted",
                    submitted_at=utcnow() + timedelta(seconds=1),
                    definition_snapshot={"title": "New result"},
                    result={"score": 100, "categories": [], "evaluation": {"meets_target": True}},
                )
            )
            db.add(
                ExamAttempt(
                    user_id=1,
                    exam_id="python-beginner-v1",
                    status="active",
                    definition_snapshot={"title": "Active private"},
                    result=None,
                )
            )
        plan = self.save()["plan"]
        self.assertEqual(plan["starting_point"]["id"], "python-text-bytes")
        self.assertEqual(len(plan["evidence"]), 1)
        self.assertEqual(plan["evidence"][0]["title"], "New result")
        self.client.put("/api/lessons/python-text-bytes/complete")
        refreshed = self.client.get("/api/learning-plan").json()["plan"]
        self.assertEqual(refreshed["items"][0]["lesson_id"], "python-text-bytes")
        self.assertNotEqual(refreshed["starting_point"]["id"], "python-start")

    def test_due_reviews_first_future_reviews_excluded_and_no_duplicate_tasks(self):
        exercise = lessons()[0]["exercises"][0]
        with self.factory.begin() as db:
            db.add(ReviewItem(user_id=1, exercise_id=exercise["id"], due_at=utcnow() - timedelta(days=1)))
            db.add(
                ReviewItem(
                    user_id=1,
                    exercise_id=lessons()[1]["exercises"][0]["id"],
                    due_at=utcnow() + timedelta(days=5),
                )
            )
        items = self.save()["plan"]["items"]
        self.assertEqual(items[0]["kind"], "review")
        self.assertTrue(items[0]["href"].endswith("?review=1"))
        self.assertEqual(len([i for i in items if i["id"] == exercise["id"]]), 1)
        self.assertEqual(len([i for i in items if i["kind"] == "review"]), 1)

    def test_new_weak_result_requires_fresh_reinforcement_and_uncovered_topics_are_honest(self):
        lesson = next(lesson for lesson in lessons() if lesson["id"] == "python-collections")
        self.client.put("/api/lessons/python-collections/complete")
        for exercise in lesson["exercises"]:
            self.client.post(f"/api/exercises/{exercise['id']}/attempts", json={"answer": exercise["answer"]})
        self.exam()
        self.assertEqual(self.save()["plan"]["items"][0]["lesson_id"], lesson["id"])
        for exercise in lesson["exercises"]:
            self.client.post(f"/api/exercises/{exercise['id']}/attempts", json={"answer": exercise["answer"]})
        self.assertNotEqual(
            self.client.get("/api/learning-plan").json()["plan"]["starting_point"]["id"], lesson["id"]
        )
        self.exam(skill="Async & concurrency")
        self.assertIn(
            "Async & concurrency", self.client.get("/api/learning-plan").json()["plan"]["uncovered_topics"]
        )

    def test_finished_path_has_an_honest_empty_queue(self):
        selected = [lesson for lesson in lessons() if lesson["track_id"] == "python"]
        attempts = [
            SimpleNamespace(exercise_id=e["id"], score=100, is_review=False)
            for lesson in selected
            for e in lesson["exercises"]
        ]
        result = build_plan(
            SimpleNamespace(goal="python", weekly_hours=20, starting_mode="recommended"),
            lessons(),
            {lesson["id"] for lesson in selected},
            attempts,
            [],
            [],
        )
        self.assertEqual(result["items"], [])
        self.assertIsNone(result["starting_point"])
        self.assertEqual(result["scheduled_minutes"], 0)


class PlanMigrationTests(unittest.TestCase):
    def test_upgrade_preserves_users_and_downgrade_removes_only_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "migration.db"
            env = {**os.environ, "DATABASE_URL": f"sqlite:///{path}"}

            def migrate(*args):
                result = subprocess.run(
                    [sys.executable, "-m", "alembic", *args], env=env, capture_output=True, text=True
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            migrate("upgrade", "b92a4d781f10")
            with closing(sqlite3.connect(path)) as db, db:
                db.execute(
                    "INSERT INTO users(id,email,name,password_hash,created_at) VALUES (1,'preserved@example.com','Preserved','unchanged','2026-09-30')"
                )
            migrate("upgrade", "head")
            migrate("check")
            with closing(sqlite3.connect(path)) as db, db:
                self.assertEqual(db.execute("SELECT count(*) FROM learning_preferences").fetchone()[0], 0)
                db.execute(
                    "INSERT INTO learning_preferences VALUES (1,'python',3,'recommended','2026-09-30')"
                )
            migrate("downgrade", "b92a4d781f10")
            with closing(sqlite3.connect(path)) as db, db:
                self.assertEqual(db.execute("SELECT name FROM users WHERE id=1").fetchone()[0], "Preserved")
            migrate("upgrade", "head")
