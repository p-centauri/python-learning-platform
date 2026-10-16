"""Exercise actual lifecycle, secrecy and evidence boundaries rather than UI shape alone."""

from copy import deepcopy
from io import BytesIO
import json
import unittest
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZipFile
from fastapi.testclient import TestClient
from sqlalchemy import select
import test_academy as helpers
from app.main import app
from app.content import exam_by_id
from app.models import ExamAttempt, ExamRun, ProjectSubmission
from app.portfolios import PORTFOLIO_FILES, REPAIR_FILES

TEXT = "Concrete observed evidence and failure reasoning with remaining limits explicitly stated."


class ComprehensiveLifecycleTests(unittest.TestCase):
    setUp = helpers.AcademyTests.setUp
    tearDown = helpers.AcademyTests.tearDown
    register = helpers.AcademyTests.register
    other_learner = helpers.AcademyTests.other_learner

    def start(self, exam):
        response = self.client.post("/api/exams/start", json={"exam_id": exam})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def answer(self, attempt, q, value):
        return self.client.put(
            f"/api/exams/attempts/{attempt}/answer", json={"question_id": q, "answer": value}
        )

    def fill(self, row, correct=True):
        exam = exam_by_id(row["exam_id"])
        for q in exam["questions"]:
            value = TEXT if q.get("kind") == "short" else q["answer"]
            if not correct and q.get("kind") != "short":
                value = [] if isinstance(value, list) else (value + 1) % len(q["options"])
                if value == []:
                    value = [next(i for i in range(len(q["options"])) if i not in q["answer"])]
            self.assertEqual(self.answer(row["id"], q["id"], value).status_code, 200)

    def test_knowledge_mixed_answers_exact_sets_secrecy_and_atomic_review(self):
        row = self.start("engineering-knowledge-v1")
        base = f"/api/exams/attempts/{row['id']}"
        self.assertEqual(len(row["questions"]), 48)
        self.assertNotIn('"explanation"', json.dumps(row))
        self.assertNotIn('"answer":', json.dumps(row))
        multi = next(q for q in row["questions"] if q.get("kind") == "multiple")
        single = next(q for q in row["questions"] if q.get("kind") == "single")
        short = next(q for q in row["questions"] if q.get("kind") == "short")
        for q, value in [
            (multi, [0, 0]),
            (multi, [True]),
            (single, True),
            (single, "0"),
            (short, 0),
            (short, "x" * 1001),
            (multi, [99]),
        ]:
            self.assertEqual(self.answer(row["id"], q["id"], value).status_code, 422)
        self.assertEqual(self.answer(row["id"], multi["id"], []).status_code, 200)
        self.assertEqual(self.client.post(base + "/submit").status_code, 422)
        with patch("app.assessments.exam_by_id", return_value=None):
            self.fill(row)
            result = self.client.post(base + "/submit")
        self.assertEqual(result.status_code, 200, result.text)
        submitted = result.json()
        self.assertEqual(submitted["result"]["score"], 100)
        self.assertEqual(submitted["result"]["total"], 40)
        self.assertEqual(submitted["result"]["manual_count"], 8)
        self.assertEqual(len(submitted["result"]["categories"]), 8)
        self.assertEqual(len(submitted["result"]["explanations"]), 40)
        self.assertEqual(self.client.post(base + "/submit").json(), submitted)
        self.assertEqual(self.answer(row["id"], single["id"], 0).status_code, 409)
        review = self.client.get(
            f"/api/project-submissions/{submitted['result']['review_submission_id']}"
        ).json()
        self.assertEqual(review["feedback"], [])
        self.assertEqual(review["status"], "submitted")
        self.assertEqual(len(review["artifact"]["exam_evidence"]["responses"]), 48)
        with self.factory() as db:
            self.assertEqual(len(list(db.scalars(select(ProjectSubmission)))), 1)
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)

    def test_exact_multi_scoring_wrong_choices_and_recommendations(self):
        row = self.start("engineering-knowledge-v1")
        self.fill(row, correct=False)
        result = self.client.post(f"/api/exams/attempts/{row['id']}/submit").json()["result"]
        self.assertEqual(result["score"], 0)
        self.assertFalse(result["evaluation"]["meets_target"])
        self.assertTrue(result["recommendations"])
        self.assertTrue(result["recommended_exercises"])

    def test_workspace_flags_position_resume_and_owner_boundaries(self):
        row = self.start("engineering-knowledge-v1")
        base = f"/api/exams/attempts/{row['id']}"
        payload = {"flags": [row["questions"][2]["id"]], "position": 2}
        self.assertEqual(self.client.put(base + "/workspace", json=payload).status_code, 200)
        resumed = self.start(row["exam_id"])
        self.assertEqual(resumed["id"], row["id"])
        self.assertEqual(resumed["workspace"]["flags"], payload["flags"])
        self.assertEqual(resumed["workspace"]["position"], 2)
        for invalid in [
            {"flags": ["missing"]},
            {"position": 100},
            {"position": True},
            {"stage": 7},
            {"result": {"score": 100}},
            {"code": "print(1)"},
        ]:
            self.assertEqual(self.client.put(base + "/workspace", json=invalid).status_code, 422)
        other = self.other_learner()
        for method, path, data in [
            ("get", base, None),
            ("get", base + "/runs", None),
            ("post", base + "/advance", None),
            ("put", base + "/workspace", payload),
            ("post", base + "/submit", None),
        ]:
            result = getattr(other, method)(path, **({"json": data} if data is not None else {}))
            self.assertEqual(result.status_code, 404)

    def test_design_incident_visibility_commit_freeze_and_manual_submission(self):
        row = self.start("senior-design-v1")
        base = f"/api/exams/attempts/{row['id']}"
        self.assertEqual(len(row["questions"]), 4)
        self.assertEqual(row["stage"]["index"], 0)
        self.assertNotIn("Traffic increased", json.dumps(row))
        self.assertEqual(self.answer(row["id"], "traffic", TEXT).status_code, 422)
        self.assertEqual(self.client.post(base + "/advance").status_code, 422)
        self.assertEqual(self.client.post(base + "/submit").status_code, 422)
        for stage in range(8):
            current = self.client.get(base).json()
            snapshot = exam_by_id(row["exam_id"])["stages"][stage]
            for q in snapshot["questions"]:
                self.assertEqual(self.answer(row["id"], q["id"], TEXT + " " + q["id"]).status_code, 200)
            if stage < 7:
                self.assertEqual(self.client.post(base + "/advance").status_code, 200)
                for q in snapshot["questions"]:
                    self.assertEqual(self.answer(row["id"], q["id"], TEXT).status_code, 409)
                current = self.client.get(base).json()
                self.assertEqual(current["stage"]["index"], stage + 1)
                self.assertEqual(len(current["questions"]), stage + 5)
        submitted = self.client.post(base + "/submit").json()
        self.assertIsNone(submitted["result"]["score"])
        self.assertEqual(submitted["result"]["manual_count"], 11)
        self.assertEqual(self.client.post(base + "/submit").json(), submitted)
        self.assertEqual(self.client.post(base + "/advance").status_code, 409)

    def fake_result(self):
        checks = exam_by_id("practical-repair-v1")["execution"]["tests"]
        return {
            "status": "passed",
            "passed": len(checks),
            "total": len(checks),
            "profile": "verified-fixture",
            "duration_ms": 10,
            "checks": [
                {
                    "status": "passed",
                    "name": "private marker",
                    "actual": "private marker",
                    "message": "private marker",
                }
                for _ in checks
            ],
        }

    def test_practical_source_runs_fixed_evidence_redaction_idempotency_and_submit(self):
        row = self.start("practical-repair-v1")
        base = f"/api/exams/attempts/{row['id']}"
        self.assertNotIn('"expected"', json.dumps(row))
        self.assertNotIn('"args"', json.dumps(row))
        code = "def repair(case):\n    return {}\n"
        self.assertEqual(self.client.put(base + "/workspace", json={"code": code}).status_code, 200)
        self.fill(row)
        self.assertEqual(self.client.post(base + "/submit").status_code, 422)
        request = {"request_key": str(uuid4())}
        with patch("app.comprehensive.runner_request", return_value=self.fake_result()) as runner:
            run = self.client.post(base + "/runs", json=request)
            self.assertEqual(run.status_code, 201, run.text)
            self.assertEqual(self.client.post(base + "/runs", json=request).json(), run.json())
            runner.assert_called_once()
            self.assertEqual(runner.call_args.args[0], "/exam-run")
        for check in run.json()["result"]["checks"]:
            if not check["public"]:
                self.assertIsNone(check["actual"])
                self.assertEqual(check["message"], "")
                self.assertNotIn("private", check["name"])
        other = self.other_learner()
        self.assertEqual(other.get(base + "/runs").status_code, 404)
        self.client.put(base + "/workspace", json={"code": code + "# edit\n"})
        self.assertEqual(self.client.post(base + "/runs", json=request).status_code, 409)
        self.assertEqual(self.client.post(base + "/submit").status_code, 422)
        self.client.put(base + "/workspace", json={"code": code})
        submitted = self.client.post(base + "/submit").json()
        self.assertEqual(submitted["result"]["run_id"], run.json()["id"])
        review = self.client.get(
            f"/api/project-submissions/{submitted['result']['review_submission_id']}"
        ).json()
        self.assertEqual(review["artifact"]["exam_evidence"]["source"], code)
        self.assertEqual(self.client.post(base + "/submit").json(), submitted)
        self.assertEqual(self.client.put(base + "/workspace", json={"code": "changed"}).status_code, 409)
        self.assertEqual(
            self.client.post(base + "/runs", json={"request_key": str(uuid4())}).status_code, 409
        )
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)

    def test_runner_failure_does_not_create_grade_and_run_budget_is_real(self):
        row = self.start("practical-repair-v1")
        base = f"/api/exams/attempts/{row['id']}"
        self.client.put(base + "/workspace", json={"code": "def repair(case): return {}"})
        with patch("app.comprehensive.runner_request", return_value={"status": "passed"}):
            self.assertEqual(
                self.client.post(base + "/runs", json={"request_key": str(uuid4())}).status_code, 503
            )
        with self.factory() as db:
            self.assertEqual(len(list(db.scalars(select(ExamRun)))), 0)
        with patch("app.comprehensive.runner_request", return_value=self.fake_result()) as runner:
            for _ in range(8):
                self.assertEqual(
                    self.client.post(base + "/runs", json={"request_key": str(uuid4())}).status_code, 201
                )
            self.assertEqual(
                self.client.post(base + "/runs", json={"request_key": str(uuid4())}).status_code, 429
            )
            self.assertEqual(runner.call_count, 8)

    def test_invited_review_only_after_submission_then_revision_preserves_attachment(self):
        row = self.start("engineering-knowledge-v1")
        self.fill(row)
        submitted = self.client.post(f"/api/exams/attempts/{row['id']}/submit").json()
        rid = submitted["result"]["review_submission_id"]
        reviewer = self.other_learner()
        base = f"/api/project-submissions/{rid}"
        self.assertEqual(reviewer.get(base).status_code, 404)
        self.assertEqual(
            self.client.post(base + "/reviewers", json={"email": "other@example.com"}).status_code, 200
        )
        detail = reviewer.get(base).json()
        self.assertTrue(detail["can_review"])
        feedback = {
            "ratings": {
                c["id"]: {"score": 2, "evidence": "Reviewed actual submitted reasoning."}
                for c in detail["rubric"]["criteria"]
            },
            "summary": "The fixed reasoning meets the stated manual rubric.",
            "next_steps": "Add independent runtime and real infrastructure evidence.",
        }
        reviewed = reviewer.post(base + "/feedback", json=feedback)
        self.assertEqual(reviewed.status_code, 201, reviewed.text)
        self.assertEqual(reviewed.json()["feedback"][0]["kind"], "human")
        grant = self.client.get(base).json()["assignments"][0]["id"]
        self.client.delete(base + f"/reviewers/{grant}")
        self.assertEqual(reviewer.get(base).status_code, 404)
        draft = self.client.post("/api/projects/exam-knowledge/submissions").json()
        self.assertEqual(draft["parent_id"], rid)
        self.assertNotIn("exam_evidence", draft["artifact"])
        self.assertEqual(
            self.client.get(base).json()["artifact"]["exam_evidence"], detail["artifact"]["exam_evidence"]
        )

    def test_all_packs_exact_authenticated_and_real_brief_links(self):
        anonymous = TestClient(app)
        self.addCleanup(anonymous.close)
        for id in ["backend", "enterprise-rag", "finance"]:
            brief = self.client.get(f"/api/projects/{id}/brief")
            self.assertEqual(brief.status_code, 200)
            self.assertEqual(len(brief.json()["sections"]), 8)
            for lesson in brief.json()["learning"]:
                self.assertEqual(self.client.get(f"/api/lessons/{lesson}").status_code, 200)
            path = f"/api/portfolio-packs/{id}"
            self.assertEqual(anonymous.get(path).status_code, 401)
            with ZipFile(BytesIO(self.client.get(path).content)) as z:
                self.assertEqual(set(z.namelist()), {f"{id}/{f}" for f in PORTFOLIO_FILES})
                self.assertFalse(any("reference" in n for n in z.namelist()))
        path = "/api/exam-packs/practical-repair-v1"
        self.assertEqual(anonymous.get(path).status_code, 401)
        with ZipFile(BytesIO(self.client.get(path).content)) as z:
            self.assertEqual(set(z.namelist()), {f"practical-repair-v1/{f}" for f in REPAIR_FILES})
            cases = json.loads(z.read("practical-repair-v1/public-cases.json"))
            self.assertEqual(len(cases), 8)
            self.assertTrue(all(c["public"] for c in cases))
        self.assertEqual(self.client.get("/api/portfolio-packs/missing").status_code, 404)

    def test_frozen_manual_rubric_and_source_contract_survive_edits(self):
        row = self.start("practical-repair-v1")
        original = deepcopy(exam_by_id(row["exam_id"]))
        with self.factory() as db:
            snapshot = db.get(ExamAttempt, row["id"]).definition_snapshot
            self.assertEqual(snapshot["execution"], original["execution"])
            self.assertEqual(snapshot["rubric"], original["rubric"])
        with patch("app.assessments.exam_by_id", return_value=None):
            self.assertEqual(
                self.client.get(f"/api/exams/attempts/{row['id']}").json()["execution"]["starter"],
                original["execution"]["starter"],
            )
