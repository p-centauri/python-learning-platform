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
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import select
import test_academy
from app.main import app
from app.content import catalog
from app.models import ProjectFeedback, ProjectReviewAssignment
from app.projects import rubric_content


ARTIFACT = {
    "repository_url": "https://github.com/learner/expenses",
    "revision_ref": "f0e1d2c3",
    "design_notes": "Integer cents keep decimal amounts exact; file ownership stays in the CSV boundary.",
    "evidence": "expenses.py validates rows before totals; tests/test_regression.py covers repeated calls and bad amounts.",
    "test_status": "passed",
    "test_command": "python -m unittest discover -s tests -v",
    "test_output": "Ran 16 tests in 0.1s\nOK",
    "change_summary": "",
}


class SubmissionTests(unittest.TestCase):
    setUp = test_academy.AcademyTests.setUp
    tearDown = test_academy.AcademyTests.tearDown
    register = test_academy.AcademyTests.register
    other_learner = test_academy.AcademyTests.other_learner

    def draft(self, project="python-expenses"):
        response = self.client.post(f"/api/projects/{project}/submissions")
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def submitted(self, project="python-expenses"):
        row = self.draft(project)
        self.assertEqual(
            self.client.put(f"/api/project-submissions/{row['id']}", json=ARTIFACT).status_code, 200
        )
        response = self.client.post(f"/api/project-submissions/{row['id']}/submit")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def feedback(self, row, score=2):
        return {
            "ratings": {
                c["id"]: {"score": score, "evidence": "Inspected the exact commit and its regression cases."}
                for c in row["rubric"]["criteria"]
            },
            "summary": "The evidence supports the stated behavior for the submitted version.",
            "next_steps": "Keep these regression checks and document the remaining edge cases.",
        }

    def test_authentication_and_draft_isolation(self):
        with TestClient(app) as anonymous:
            self.assertEqual(anonymous.get("/api/projects/python-expenses/submissions").status_code, 401)
            self.assertEqual(anonymous.get("/api/project-reviews").status_code, 401)
        row = self.draft()
        other = self.other_learner()
        self.assertEqual(other.get("/api/projects/python-expenses/submissions").json()["submissions"], [])
        for method, suffix, payload in [
            ("get", "", None),
            ("put", "", ARTIFACT),
            ("delete", "", None),
            ("post", "/submit", None),
            ("post", "/reviewers", {"email": "learner@example.com"}),
            ("post", "/feedback", self.feedback(row)),
        ]:
            response = getattr(other, method)(
                f"/api/project-submissions/{row['id']}{suffix}",
                **({"json": payload} if payload is not None else {}),
            )
            self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(self.client.post("/api/projects/missing/submissions").status_code, 404)

    def test_draft_save_resume_discard_and_no_progress_writes(self):
        row = self.draft()
        self.assertEqual(self.draft()["id"], row["id"])
        partial = {"design_notes": "A saved, unfinished thought."}
        self.assertEqual(
            self.client.put(f"/api/project-submissions/{row['id']}", json=partial).status_code, 200
        )
        self.assertEqual(
            self.client.get(f"/api/project-submissions/{row['id']}").json()["artifact"]["design_notes"],
            partial["design_notes"],
        )
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)
        projects = self.client.get("/api/projects").json()
        self.assertTrue(all(not t["completed"] for p in projects for t in p["tasks"]))
        self.assertEqual(self.client.delete(f"/api/project-submissions/{row['id']}").status_code, 204)
        self.assertEqual(self.draft()["revision"], 1)

    def test_artifact_validation_safe_urls_and_submit_requirements(self):
        row = self.draft()
        path = f"/api/project-submissions/{row['id']}"
        for payload in [
            {"repository_url": "javascript:alert(1)"},
            {"repository_url": "https://a:b@example.com/repo"},
            {"repository_url": "http://example.com"},
            {"repository_url": "https://example.com:bad"},
            {"repository_url": "https://example.com/\nx"},
            {"test_status": "verified"},
            {"user_id": 2},
            {"design_notes": "x" * 12001},
        ]:
            self.assertEqual(self.client.put(path, json=payload).status_code, 422)
        self.assertEqual(self.client.post(path + "/submit").status_code, 422)
        for changes in [{"design_notes": " " * 40}, {"revision_ref": ""}, {"test_output": ""}]:
            self.client.put(path, json={**ARTIFACT, **changes})
            self.assertEqual(self.client.post(path + "/submit").status_code, 422)
        self.client.put(
            path, json={**ARTIFACT, "test_status": "not-run", "test_command": "", "test_output": ""}
        )
        self.assertEqual(self.client.post(path + "/submit").status_code, 200)

    def test_submitted_version_and_feedback_are_fixed_and_idempotent(self):
        row = self.submitted()
        path = f"/api/project-submissions/{row['id']}"
        self.assertEqual(self.client.post(path + "/submit").json(), row)
        self.assertEqual(self.client.put(path, json={**ARTIFACT, "design_notes": "Changed"}).status_code, 409)
        self.assertEqual(self.client.delete(path).status_code, 409)
        payload = self.feedback(row)
        first = self.client.post(path + "/feedback", json=payload)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.json()["feedback"][0]["kind"], "self")
        self.assertEqual(self.client.post(path + "/feedback", json=payload).json(), first.json())
        self.assertEqual(self.client.post(path + "/feedback", json=self.feedback(row, 3)).status_code, 409)
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)

    def test_invitation_access_revoke_reinvite_and_human_identity(self):
        reviewer = self.other_learner()
        email = reviewer.get("/api/auth/me").json()["email"]
        row = self.submitted()
        path = f"/api/project-submissions/{row['id']}"
        draft = self.draft("python-task-inbox")
        self.assertEqual(
            self.client.post(
                f"/api/project-submissions/{draft['id']}/reviewers", json={"email": email}
            ).status_code,
            409,
        )
        self.assertEqual(
            self.client.post(path + "/reviewers", json={"email": "learner@example.com"}).status_code, 422
        )
        self.assertEqual(
            self.client.post(path + "/reviewers", json={"email": "unregistered@example.com"}).status_code, 422
        )
        self.assertEqual(reviewer.get(path).status_code, 404)
        grant = self.client.post(path + "/reviewers", json={"email": email.upper()}).json()
        self.assertEqual(reviewer.get("/api/project-reviews").json()[0]["id"], row["id"])
        visible = reviewer.get(path).json()
        self.assertFalse(visible["is_owner"])
        self.assertEqual(visible["assignments"], [])
        self.assertEqual(reviewer.get(f"/api/project-submissions/{draft['id']}").status_code, 404)
        self.assertEqual(reviewer.put(path, json=ARTIFACT).status_code, 404)
        self.assertEqual(
            reviewer.post(path + "/reviewers", json={"email": "learner@example.com"}).status_code, 404
        )
        result = reviewer.post(path + "/feedback", json=self.feedback(row, 1))
        self.assertEqual(result.status_code, 201, result.text)
        feedback = result.json()["feedback"][0]
        self.assertEqual(feedback["kind"], "human")
        self.assertEqual(feedback["outcome"], "changes-requested")
        self.assertTrue(reviewer.get("/api/project-reviews").json()[0]["reviewed"])
        assignment_id = grant["assignments"][0]["id"]
        self.assertEqual(self.client.delete(path + f"/reviewers/{assignment_id}").status_code, 200)
        self.assertEqual(reviewer.get(path).status_code, 404)
        self.assertEqual(reviewer.get("/api/project-reviews").json(), [])
        self.assertEqual(len(self.client.get(path).json()["feedback"]), 1)
        self.client.post(path + "/reviewers", json={"email": email})
        self.assertEqual(reviewer.get(path).status_code, 200)
        with self.factory() as db:
            self.assertEqual(len(list(db.scalars(select(ProjectReviewAssignment)))), 1)
            self.assertEqual(len(list(db.scalars(select(ProjectFeedback)))), 1)

    def test_reviews_require_exact_criteria_strict_scores_and_evidence(self):
        row = self.submitted()
        path = f"/api/project-submissions/{row['id']}/feedback"
        criterion = row["rubric"]["criteria"][0]["id"]
        for score in [True, "2", 1.5, -1, 4]:
            payload = self.feedback(row)
            payload["ratings"][criterion]["score"] = score
            self.assertEqual(self.client.post(path, json=payload).status_code, 422)
        for changes in [
            {"kind": "human"},
            {"summary": " " * 40},
            {"ratings": {}},
            {"ratings": {"unknown": {"score": 2, "evidence": "Valid evidence string."}}},
        ]:
            self.assertEqual(self.client.post(path, json={**self.feedback(row), **changes}).status_code, 422)
        payload = self.feedback(row)
        payload["ratings"].pop(criterion)
        self.assertEqual(self.client.post(path, json=payload).status_code, 422)
        with self.factory() as db:
            self.assertEqual(len(list(db.scalars(select(ProjectFeedback)))), 0)

    def test_revision_preserves_old_artifact_rubric_feedback_and_requires_change_summary(self):
        old = self.submitted()
        self.client.post(f"/api/project-submissions/{old['id']}/feedback", json=self.feedback(old))
        current = deepcopy(rubric_content())
        current["version"] = "future-rubric"
        current["projects"]["python-expenses"][0]["expectation"] = "Changed expectation"
        with patch("app.projects.rubric_content", return_value=current):
            draft = self.draft()
        self.assertEqual(draft["parent_id"], old["id"])
        self.assertEqual(draft["revision"], 2)
        self.assertEqual(draft["artifact"], ARTIFACT)
        self.assertEqual(draft["rubric"]["version"], "future-rubric")
        self.assertEqual(self.client.post(f"/api/project-submissions/{draft['id']}/submit").status_code, 422)
        revised = {
            **ARTIFACT,
            "revision_ref": "new-commit",
            "change_summary": "Added the missing CSV failure regression requested in feedback.",
        }
        self.client.put(f"/api/project-submissions/{draft['id']}", json=revised)
        self.client.post(f"/api/project-submissions/{draft['id']}/submit")
        history = self.client.get("/api/projects/python-expenses/submissions").json()["submissions"]
        self.assertEqual([s["revision"] for s in history], [2, 1])
        self.assertEqual(history[1]["artifact"], ARTIFACT)
        self.assertEqual(history[1]["rubric"], old["rubric"])
        self.assertEqual(len(history[1]["feedback"]), 1)
        self.assertEqual(history[0]["feedback"], [])
        self.assertEqual(history[0]["assignments"], [])

    def test_every_project_has_a_specific_rubric(self):
        content = rubric_content()
        self.assertEqual(set(content["projects"]), {p["id"] for p in catalog()["projects"]})
        for project in catalog()["projects"]:
            row = self.draft(project["id"])
            self.assertEqual(row["rubric"]["project_title"], project["title"])
            expected = {"exam-knowledge": 8, "exam-repair": 7, "exam-design": 7}.get(project["id"], 4)
            self.assertEqual(len(row["rubric"]["criteria"]), expected)
            self.assertEqual(len({c["id"] for c in row["rubric"]["criteria"]}), expected)
        self.assertEqual([s["score"] for s in content["scale"]], [0, 1, 2, 3])


class SubmissionMigrationTests(unittest.TestCase):
    def test_upgrade_downgrade_preserves_prior_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "migration.db"
            env = {**os.environ, "DATABASE_URL": f"sqlite:///{path}"}

            def migrate(*args):
                result = subprocess.run(
                    [sys.executable, "-m", "alembic", *args], env=env, capture_output=True, text=True
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            migrate("upgrade", "c731ab204e19")
            with closing(sqlite3.connect(path)) as db, db:
                db.execute("INSERT INTO users VALUES (1,'kept@example.com','Kept','unchanged','2026-09-30')")
                db.execute(
                    "INSERT INTO learning_preferences VALUES (1,'python',3,'recommended','2026-09-30')"
                )
                db.execute("INSERT INTO project_progress VALUES (1,1,'python-expenses','setup','2026-09-30')")
            migrate("upgrade", "head")
            migrate("check")
            with closing(sqlite3.connect(path)) as db, db:
                self.assertEqual(db.execute("SELECT count(*) FROM project_submissions").fetchone()[0], 0)
                db.execute(
                    "INSERT INTO project_submissions VALUES (1,1,'python-expenses',1,NULL,'submitted',?,?, '2026-09-30','2026-09-30','2026-09-30')",
                    (json.dumps({"version": "test"}), json.dumps(ARTIFACT)),
                )
                db.execute(
                    "INSERT INTO project_feedback VALUES (1,1,1,'self','{}','Summary','Next actions','2026-09-30')"
                )
            migrate("downgrade", "c731ab204e19")
            with closing(sqlite3.connect(path)) as db, db:
                self.assertEqual(db.execute("SELECT name FROM users").fetchone()[0], "Kept")
                self.assertEqual(db.execute("SELECT weekly_hours FROM learning_preferences").fetchone()[0], 3)
                self.assertEqual(db.execute("SELECT task_id FROM project_progress").fetchone()[0], "setup")
            migrate("upgrade", "head")
            migrate("check")
