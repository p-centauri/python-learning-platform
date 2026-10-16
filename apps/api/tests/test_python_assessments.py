import json
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_academy
from app.content import catalog, exam_by_id, exam_definitions, lessons
from app.exam_grading import grade_exam


class PythonAssessmentTests(unittest.TestCase):
    setUp = test_academy.AcademyTests.setUp
    tearDown = test_academy.AcademyTests.tearDown
    register = test_academy.AcademyTests.register
    other_learner = test_academy.AcademyTests.other_learner

    def start(self, level):
        response = self.client.post("/api/exams/start", json={"exam_id": f"python-{level}-v1"})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_catalog_has_separate_banks_and_guides_without_private_keys(self):
        response = self.client.get("/api/exams")
        all_exams = response.json()["exams"]
        self.assertEqual(len(all_exams), 7)
        exams = [e for e in all_exams if e["level"] != "Comprehensive"]
        self.assertEqual(
            {item["id"] for item in exams},
            {"knowledge-pilot-v1", "python-beginner-v1", "python-intermediate-v1", "python-advanced-v1"},
        )
        self.assertEqual(
            [item["level"] for item in exams], ["Mixed diagnostic", "Beginner", "Intermediate", "Advanced"]
        )
        for item in exams:
            self.assertNotIn("questions", item)
            if item["id"].startswith("python-"):
                self.assertTrue(item["libraries"])
                self.assertTrue(item["evaluation_policy"]["note"])
        self.assertNotIn('"explanation":', response.text)
        self.assertNotIn('"validation_output":', response.text)

    def test_each_bank_resumes_its_own_attempt_and_rejects_cross_bank_questions(self):
        beginner = self.start("beginner")
        intermediate = self.start("intermediate")
        advanced = self.start("advanced")
        self.assertEqual(len({beginner["id"], intermediate["id"], advanced["id"]}), 3)
        self.assertEqual(len(advanced["questions"]), 28)
        self.assertEqual(self.start("advanced")["id"], advanced["id"])
        self.assertNotEqual(beginner["id"], intermediate["id"])
        self.assertEqual(len(beginner["questions"]), 20)
        self.assertEqual(len(intermediate["questions"]), 24)
        self.assertEqual(self.start("beginner")["id"], beginner["id"])
        self.assertEqual(self.start("intermediate")["id"], intermediate["id"])
        path = f"/api/exams/attempts/{beginner['id']}/answer"
        self.assertEqual(self.client.put(path, json={"question_id": "pi-01", "answer": 0}).status_code, 422)
        self.assertEqual(self.client.put(path, json={"question_id": "pa-01", "answer": 0}).status_code, 422)
        self.assertEqual(self.client.post("/api/exams/start", json={"exam_id": "missing"}).status_code, 404)

    def test_code_is_public_but_answers_and_validated_outputs_are_private(self):
        attempt = self.start("advanced")
        self.assertTrue(attempt["questions"][0]["code"])
        for question in attempt["questions"]:
            for key in ("answer", "explanation", "validation_output"):
                self.assertNotIn(key, question)
        other = self.other_learner()
        base = f"/api/exams/attempts/{attempt['id']}"
        self.assertEqual(other.get(base).status_code, 404)
        self.assertEqual(
            other.put(base + "/answer", json={"question_id": "pa-01", "answer": 0}).status_code, 404
        )

    def test_all_python_banks_grade_and_keep_results_independent(self):
        for level, expected in [("beginner", 0), ("intermediate", 100), ("advanced", 100)]:
            attempt = self.start(level)
            exam = exam_by_id(attempt["exam_id"])
            for question in exam["questions"]:
                answer = question["answer"] if expected else (question["answer"] + 1) % 4
                result = self.client.put(
                    f"/api/exams/attempts/{attempt['id']}/answer",
                    json={"question_id": question["id"], "answer": answer},
                )
                self.assertEqual(result.status_code, 200)
            submitted = self.client.post(f"/api/exams/attempts/{attempt['id']}/submit").json()
            self.assertEqual(submitted["result"]["score"], expected)
            self.assertEqual(submitted["result"]["evaluation"]["meets_target"], bool(expected))
            self.assertEqual(submitted["title"], exam["title"])
            self.assertEqual(
                self.client.post(f"/api/exams/attempts/{attempt['id']}/submit").json(), submitted
            )
            self.assertEqual(
                len(submitted["result"]["categories"]),
                {"beginner": 5, "intermediate": 6, "advanced": 7}[level],
            )
            self.assertEqual(bool(submitted["result"]["study_recommendations"]), not bool(expected))
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)

    def test_saved_snapshot_survives_bank_edits_or_removal(self):
        attempt = self.start("advanced")
        original = exam_by_id(attempt["exam_id"])
        # An existing attempt must not consult live banks, even if they disappear.
        with patch("app.assessments.exam_by_id", return_value=None):
            detail = self.client.get(f"/api/exams/attempts/{attempt['id']}").json()
            self.assertEqual(detail["questions"], attempt["questions"])
            for question in original["questions"]:
                response = self.client.put(
                    f"/api/exams/attempts/{attempt['id']}/answer",
                    json={"question_id": question["id"], "answer": question["answer"]},
                )
                self.assertEqual(response.status_code, 200)
            result = self.client.post(f"/api/exams/attempts/{attempt['id']}/submit").json()
            self.assertEqual(result["result"]["score"], 100)
            self.assertEqual(result["version"], original["version"])


class PythonBankQualityTests(unittest.TestCase):
    def test_coverage_and_question_integrity(self):
        prompts = [q["prompt"] for bank in exam_definitions() for q in bank["questions"]]
        self.assertEqual(len(prompts), len(set(prompts)))
        for level, count, categories in [("beginner", 20, 5), ("intermediate", 24, 6), ("advanced", 28, 7)]:
            exam = exam_by_id(f"python-{level}-v1")
            self.assertEqual(len(exam["questions"]), count)
            self.assertEqual(len({q["id"] for q in exam["questions"]}), count)
            groups = {q["skill"] for q in exam["questions"]}
            self.assertEqual(len(groups), categories)
            self.assertEqual(groups, {r["skill"] for r in exam["study_resources"]})
            for skill in groups:
                self.assertEqual(sum(q["skill"] == skill for q in exam["questions"]), 4)
            for question in exam["questions"]:
                self.assertTrue(0 <= question["answer"] < len(question["options"]))
                self.assertEqual(len(set(question["options"])), 4)
                self.assertGreater(len(question["explanation"]), 60)
            self.assertEqual({q["answer"] for q in exam["questions"]}, {0, 1, 2, 3})

    def test_author_owned_prediction_examples_match_reference_output(self):
        # Execute only fixed repository-authored, side-effect-free examples in
        # test subprocesses. There is no learner-code execution API.
        checked = 0
        for exam in exam_definitions():
            for question in exam["questions"]:
                if "validation_output" not in question:
                    continue
                with self.subTest(question=question["id"]):
                    run = subprocess.run(
                        [sys.executable, "-I", "-c", question["code"]],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=True,
                    )
                    self.assertEqual(run.stdout.strip(), question["validation_output"])
                    checked += 1
        self.assertEqual(checked, 18)

    def test_advanced_scoring_requires_breadth_and_uses_exact_thresholds(self):
        exam = exam_by_id("python-advanced-v1")

        def result_with_wrong(indices):
            answers = {q["id"]: q["answer"] for q in exam["questions"]}
            for index in indices:
                question = exam["questions"][index]
                answers[question["id"]] = (question["answer"] + 1) % 4
            return grade_exam(exam, answers, lessons())

        weak_topic = result_with_wrong([0, 1])
        self.assertEqual(weak_topic["correct"], 26)
        self.assertFalse(weak_topic["evaluation"]["meets_target"])
        self.assertEqual(len(weak_topic["study_recommendations"]), 1)
        boundary_pass = result_with_wrong([0, 4, 8, 12, 16])
        self.assertEqual(boundary_pass["correct"], 23)
        self.assertTrue(boundary_pass["evaluation"]["meets_target"])
        boundary_fail = result_with_wrong([0, 4, 8, 12, 16, 20])
        self.assertEqual(boundary_fail["correct"], 22)
        self.assertFalse(boundary_fail["evaluation"]["meets_target"])

    def test_overall_target_cannot_hide_a_weak_topic(self):
        exam = exam_by_id("python-beginner-v1")
        answers = {q["id"]: q["answer"] for q in exam["questions"]}
        for question in exam["questions"][:2]:
            answers[question["id"]] = (question["answer"] + 1) % 4
        result = grade_exam(exam, answers, lessons())
        self.assertEqual(result["score"], 90)
        self.assertFalse(result["evaluation"]["meets_target"])
        answers = {q["id"]: q["answer"] for q in exam["questions"]}
        for index in [0, 4, 8, 12]:
            question = exam["questions"][index]
            answers[question["id"]] = (question["answer"] + 1) % 4
        result = grade_exam(exam, answers, lessons())
        self.assertEqual(result["score"], 80)
        self.assertTrue(result["evaluation"]["meets_target"])


class AssessmentMigrationTests(unittest.TestCase):
    def test_upgrade_backfills_active_and_submitted_pilot_without_losing_answers(self):
        api_dir = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "migration.db"
            env = {**os.environ, "DATABASE_URL": f"sqlite:///{path}"}

            def migrate(*args):
                subprocess.run(
                    [sys.executable, "-m", "alembic", *args],
                    cwd=api_dir,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30,
                )

            migrate("upgrade", "4a722da17582")
            with closing(sqlite3.connect(path)) as db:
                db.execute(
                    "INSERT INTO users VALUES (1, 'migration@example.com', 'Migration', 'unused', '2026-09-14')"
                )
                for index, status in enumerate(["active", "submitted"], start=1):
                    db.execute(
                        "INSERT INTO exam_attempts (id,user_id,exam_id,status,answers,result,started_at) VALUES (?,1,?,?,?,?,?)",
                        (
                            index,
                            "knowledge-pilot-v1",
                            status,
                            '{"exam-python":1}',
                            '{"score":100}' if status == "submitted" else None,
                            "2026-09-14",
                        ),
                    )
                db.commit()
            migrate("upgrade", "head")
            migrate("check")
            with closing(sqlite3.connect(path)) as db:
                rows = db.execute(
                    "SELECT status,answers,result,definition_snapshot FROM exam_attempts ORDER BY id"
                ).fetchall()
            self.assertEqual([row[0] for row in rows], ["active", "submitted"])
            self.assertEqual(json.loads(rows[1][2]), {"score": 100})
            for row in rows:
                self.assertEqual(json.loads(row[1]), {"exam-python": 1})
                self.assertEqual(json.loads(row[3])["questions"], catalog()["exam"]["questions"])
            migrate("downgrade", "4a722da17582")
            migrate("upgrade", "head")
