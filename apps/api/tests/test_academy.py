import unittest
from datetime import timedelta
from types import SimpleNamespace
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.auth import hash_password, verify_password
from app.content import catalog, lessons
from app.config import settings
from app.database import Base, get_db
from app.main import app, auth_requests
from app.mastery import mastery_scores
from app.models import LoginSession, ReviewItem, utcnow
from app.seed import seed


class AcademyTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )

        @event.listens_for(self.engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(self.engine, expire_on_commit=False)
        with self.factory.begin() as db:
            seed(db)

        def database_override():
            with self.factory() as db:
                try:
                    yield db
                    db.commit()
                except Exception:
                    db.rollback()
                    raise

        app.dependency_overrides[get_db] = database_override
        auth_requests.clear()
        self.client = TestClient(app, headers={"X-Academy-Request": "1"})
        self.register(self.client, "learner@example.com")

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def register(self, client, email):
        result = client.post(
            "/api/auth/register",
            json={"email": email, "name": "Engineer", "password": "a-long-test-passphrase"},
        )
        self.assertEqual(result.status_code, 201, result.text)
        return result

    def other_learner(self):
        client = TestClient(app, headers={"X-Academy-Request": "1"})
        self.addCleanup(client.close)
        self.register(client, "other@example.com")
        return client

    def answer(self, answer=1, **extra):
        return self.client.post("/api/exercises/python-alias/attempts", json={"answer": answer, **extra})

    def test_password_hash_is_salted_and_verifies(self):
        first = hash_password("a-long-test-passphrase")
        self.assertNotEqual(first, hash_password("a-long-test-passphrase"))
        self.assertTrue(verify_password("a-long-test-passphrase", first))
        self.assertFalse(verify_password("wrong-password", first))

    def test_cookie_flags_and_hashed_session_storage(self):
        result = self.register(self.client, "cookie@example.com")
        cookie = result.headers["set-cookie"].lower()
        self.assertIn("httponly", cookie)
        self.assertIn("samesite=lax", cookie)
        with self.factory() as db:
            hashes = list(db.scalars(select(LoginSession.token_hash)))
        self.assertNotIn(self.client.cookies["academy_session"], hashes)
        self.assertTrue(all(len(h) == 64 for h in hashes))

    def test_login_logout_and_expiration(self):
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)
        self.assertEqual(self.client.get("/api/dashboard").status_code, 401)
        bad = self.client.post(
            "/api/auth/login", json={"email": "learner@example.com", "password": "incorrect-password"}
        )
        self.assertEqual(bad.status_code, 401)
        good = self.client.post(
            "/api/auth/login", json={"email": "LEARNER@example.com", "password": "a-long-test-passphrase"}
        )
        self.assertEqual(good.status_code, 200)
        with self.factory.begin() as db:
            for session in db.scalars(select(LoginSession)):
                session.expires_at = utcnow() - timedelta(seconds=1)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_mutations_require_custom_header_and_allowed_origin(self):
        self.assertEqual(
            self.client.put(
                "/api/lessons/python-ownership/complete", headers={"X-Academy-Request": ""}
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.put(
                "/api/lessons/python-ownership/complete", headers={"Origin": "https://evil.example"}
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.put(
                "/api/lessons/python-ownership/complete", headers={"Origin": "http://localhost:3000"}
            ).status_code,
            200,
        )

    def test_auth_rate_limit(self):
        for _ in range(19):
            self.client.post("/api/auth/login", json={"email": "invalid", "password": "short"})
        self.assertEqual(self.client.post("/api/auth/login", json={}).status_code, 429)

    def test_duplicate_email_and_invalid_values(self):
        result = self.client.post(
            "/api/auth/register",
            json={"email": "LEARNER@example.com", "name": "Engineer", "password": "a-long-test-passphrase"},
        )
        self.assertEqual(result.status_code, 409)
        self.assertEqual(self.client.put("/api/lessons/missing/note", json={"body": "x"}).status_code, 404)
        self.assertEqual(
            self.client.put("/api/lessons/python-ownership/note", json={"body": "x" * 20001}).status_code, 422
        )
        self.assertEqual(self.answer(answer=20).status_code, 422)
        self.assertEqual(self.answer(answer=True).status_code, 422)

    def test_reading_completion_is_idempotent_and_not_mastery(self):
        for _ in range(3):
            self.assertEqual(self.client.put("/api/lessons/python-ownership/complete").status_code, 200)
        dashboard = self.client.get("/api/dashboard").json()
        self.assertEqual(dashboard["completed_lessons"], 1)
        self.assertEqual(dashboard["mastery"], 0)
        self.assertEqual(dashboard["next_lesson"]["id"], "python-start")
        self.assertEqual(dashboard["streak"], 1)

    def test_notes_bookmarks_and_progress_are_user_scoped(self):
        self.client.put(
            "/api/lessons/python-ownership/note", json={"body": "privatezebra <script>alert(1)</script>"}
        )
        self.client.put("/api/lessons/python-ownership/bookmark", json={"enabled": True})
        self.client.put("/api/lessons/python-ownership/complete")
        other = self.other_learner()
        mine = self.client.get("/api/lessons/python-ownership").json()
        theirs = other.get("/api/lessons/python-ownership").json()
        self.assertTrue(mine["bookmarked"])
        self.assertEqual(theirs["note"], "")
        self.assertFalse(theirs["bookmarked"])
        self.assertFalse(theirs["completed"])
        self.assertEqual(other.get("/api/search?q=privatezebra").json(), [])
        self.assertEqual(len(self.client.get("/api/search?q=privatezebra").json()), 1)
        self.client.put("/api/lessons/python-ownership/bookmark", json={"enabled": False})
        self.assertEqual(self.client.get("/api/bookmarks").json(), [])

    def test_catalog_and_lesson_hide_exercise_answer_keys(self):
        for path in ["/api/curriculum", "/api/lessons/python-ownership", "/api/exercises/python-alias"]:
            result = self.client.get(path)
            self.assertEqual(result.status_code, 200)
            self.assertNotIn('"answer":', result.text)
            self.assertNotIn('"answer":1', result.text)
            self.assertNotIn("Only the outer mapping was copied", result.text)
        self.assertIsNone(self.client.get("/api/exercises/python-alias").json()["solution"])

    def test_wrong_answers_do_not_reveal_solution(self):
        response = self.answer(answer=0).json()
        self.assertEqual(response["score"], 0)
        self.assertIsNone(response["solution"])
        self.assertEqual(self.client.get("/api/exercises/python-alias").json()["attempts"][0]["score"], 0)

    def test_hints_are_progressive_and_persisted(self):
        for count in [1, 2, 3, 3]:
            response = self.client.post("/api/exercises/python-alias/hint")
            self.assertEqual(len(response.json()["hints"]), count)
        self.answer()
        detail = self.client.get("/api/exercises/python-alias").json()
        self.assertEqual(detail["attempts"][0]["hints_used"], 3)
        skill = next(s for s in self.client.get("/api/dashboard").json()["skills"] if s["skill"] == "Python")
        self.assertEqual(skill["score"], 20)  # 40% evidence on one of two questions.

    def test_repeat_success_does_not_farm_mastery(self):
        self.answer()
        before = self.client.get("/api/dashboard").json()
        for _ in range(5):
            self.answer()
        after = self.client.get("/api/dashboard").json()
        self.assertEqual(before["mastery"], after["mastery"])
        self.assertEqual(after["solved_exercises"], 1)

    def test_reveal_disqualifies_future_mastery_credit(self):
        self.assertTrue(self.client.post("/api/exercises/python-alias/reveal").json()["solution"])
        self.answer()
        dashboard = self.client.get("/api/dashboard").json()
        self.assertEqual(dashboard["mastery"], 0)
        self.assertEqual(dashboard["solved_exercises"], 0)

    def test_review_requires_due_date_and_spaces_success(self):
        self.answer()
        self.assertEqual(self.answer(review=True).status_code, 409)
        with self.factory.begin() as db:
            item = db.scalar(select(ReviewItem))
            item.due_at = utcnow() - timedelta(seconds=1)
        self.assertTrue(self.client.get("/api/reviews").json()[0]["due"])
        self.assertEqual(self.answer(review=True).status_code, 201)
        item = self.client.get("/api/reviews").json()[0]
        self.assertEqual(item["interval_days"], 6)
        self.assertEqual(item["repetitions"], 1)
        self.assertFalse(item["due"])
        self.assertEqual(self.answer(review=True).status_code, 409)

    def test_normal_practice_cannot_postpone_due_review(self):
        self.answer(answer=0)
        original = self.client.get("/api/reviews").json()[0]["due_at"]
        self.answer()
        self.assertEqual(self.client.get("/api/reviews").json()[0]["due_at"], original)

    def test_exam_secrecy_resume_ownership_and_submission(self):
        started = self.client.post("/api/exams/start").json()
        attempt_id = started["id"]
        self.assertIsNone(started["result"])
        self.assertTrue(all("answer" not in q and "explanation" not in q for q in started["questions"]))
        self.assertEqual(self.client.post("/api/exams/start").json()["id"], attempt_id)
        other = self.other_learner()
        self.assertEqual(other.get(f"/api/exams/attempts/{attempt_id}").status_code, 404)
        self.assertEqual(other.post(f"/api/exams/attempts/{attempt_id}/submit").status_code, 404)
        self.assertEqual(self.client.post(f"/api/exams/attempts/{attempt_id}/submit").status_code, 422)
        for q in catalog()["exam"]["questions"]:
            saved = self.client.put(
                f"/api/exams/attempts/{attempt_id}/answer",
                json={"question_id": q["id"], "answer": q["answer"]},
            )
            self.assertEqual(saved.status_code, 200)
        result = self.client.post(f"/api/exams/attempts/{attempt_id}/submit").json()
        self.assertEqual(result["result"]["score"], 100)
        self.assertEqual(len(result["result"]["explanations"]), 10)
        self.assertEqual(self.client.post(f"/api/exams/attempts/{attempt_id}/submit").json(), result)
        self.assertEqual(
            self.client.put(
                f"/api/exams/attempts/{attempt_id}/answer", json={"question_id": "exam-python", "answer": 0}
            ).status_code,
            409,
        )

    def test_exam_rejects_unknown_question_and_invalid_option(self):
        attempt_id = self.client.post("/api/exams/start").json()["id"]
        for question, answer in [("missing", 0), ("exam-python", 19)]:
            self.assertEqual(
                self.client.put(
                    f"/api/exams/attempts/{attempt_id}/answer",
                    json={"question_id": question, "answer": answer},
                ).status_code,
                422,
            )

    def test_project_checklist_is_persistent_and_user_scoped(self):
        path = "/api/projects/backend/tasks/contract"
        self.client.put(path, json={"enabled": True})
        self.client.put(path, json={"enabled": True})
        self.assertTrue(
            next(p for p in self.client.get("/api/projects").json() if p["id"] == "backend")["tasks"][0][
                "completed"
            ]
        )
        self.assertFalse(
            next(p for p in self.other_learner().get("/api/projects").json() if p["id"] == "backend")[
                "tasks"
            ][0]["completed"]
        )
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)
        self.assertEqual(
            self.client.put("/api/projects/backend/tasks/missing", json={"enabled": True}).status_code, 404
        )

    def test_seed_is_repeatable(self):
        with self.factory.begin() as db:
            seed(db)
            seed(db)
        self.assertEqual(len(self.client.get("/api/curriculum").json()["lessons"]), len(lessons()))


class ContentTests(unittest.TestCase):
    def test_content_integrity_and_dependency_graph(self):
        data = catalog()
        ids = {lesson["id"] for lesson in lessons()}
        self.assertEqual(len(ids), len(lessons()))
        self.assertEqual(len(data["tracks"]), 23)
        exercises = [e for lesson in lessons() for e in lesson["exercises"]]
        self.assertEqual(len({e["id"] for e in exercises}), len(exercises))
        self.assertEqual(len({e["prompt"] for e in exercises}), len(exercises))
        self.assertFalse({e["prompt"] for e in exercises} & {q["prompt"] for q in data["exam"]["questions"]})
        visiting, visited = set(), set()

        def visit(id):
            self.assertNotIn(id, visiting, "cyclic prerequisites")
            if id in visited:
                return
            visiting.add(id)
            lesson = next(lesson for lesson in lessons() if lesson["id"] == id)
            self.assertTrue((settings.content_dir / lesson["path"]).is_file())
            self.assertGreater(len((settings.content_dir / lesson["path"]).read_text().split()), 200)
            for dependency in lesson["prerequisites"]:
                self.assertIn(dependency, ids)
                visit(dependency)
            visiting.remove(id)
            visited.add(id)

        for lesson in lessons():
            visit(lesson["id"])
            self.assertGreaterEqual(len(lesson["exercises"]), 2)
            for e in lesson["exercises"]:
                self.assertEqual(len(e["hints"]), 3)
                self.assertTrue(0 <= e["answer"] < len(e["options"]))

    def test_mastery_first_attempt_and_reveal_boundaries(self):
        definitions = [{"skill": "test", "exercises": [{"id": "x"}]}]

        def attempt(id, score, revealed=False, hints=0, review=False):
            return SimpleNamespace(
                id=id, exercise_id="x", score=score, revealed=revealed, hints_used=hints, is_review=review
            )

        self.assertEqual(mastery_scores(definitions, [attempt(1, 0), attempt(2, 100)])[0]["score"], 30)
        self.assertEqual(
            mastery_scores(definitions, [attempt(1, 100), attempt(2, 0, hints=3)])[0]["score"], 100
        )
        self.assertEqual(
            mastery_scores(definitions, [attempt(1, 0), attempt(2, 100, revealed=True)])[0]["score"], 0
        )
        self.assertEqual(
            mastery_scores(definitions, [attempt(1, 0), attempt(2, 100, review=True)])[0]["score"], 0
        )


if __name__ == "__main__":
    unittest.main()
