"""Whole published-path navigation/privacy/download checks; no learner execution."""

import ast
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
import test_academy
from app.content import catalog, lessons

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_learning_paths import audit  # noqa: E402 - repository helper loaded after its explicit path


class LearningPathAuditTests(unittest.TestCase):
    setUp = test_academy.AcademyTests.setUp
    tearDown = test_academy.AcademyTests.tearDown
    register = test_academy.AcademyTests.register

    def test_every_published_lesson_navigation_and_active_keys(self):
        all_lessons = lessons()
        self.assertEqual(len(all_lessons), 195)
        for lesson in all_lessons:
            with self.subTest(lesson=lesson["id"]):
                response = self.client.get(f"/api/lessons/{lesson['id']}")
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(data["id"], lesson["id"])
                for q in data["exercises"]:
                    self.assertNotIn("answer", q)
                    self.assertNotIn("solution", q)
                track = [row for row in all_lessons if row["track_id"] == lesson["track_id"]]
                index = next(n for n, row in enumerate(track) if row["id"] == lesson["id"])
                nav = data["navigation"]
                self.assertEqual(
                    nav["previous"]["id"] if nav["previous"] else None,
                    track[index - 1]["id"] if index else None,
                )
                self.assertEqual(
                    nav["next"]["id"] if nav["next"] else None,
                    track[index + 1]["id"] if index + 1 < len(track) else None,
                )
                activities = self.client.get(f"/api/lesson-activities/{lesson['id']}").json()
                self.assertNotIn('"answer"', json.dumps(activities))
                self.assertNotIn('"validation"', json.dumps(activities))
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)

    def test_every_registered_starter_is_exact_and_authenticated(self):
        node = ast.parse((ROOT / "apps/api/app/assessments.py").read_text())
        fn = next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == "project_starter")
        assignment = next(
            n
            for n in fn.body
            if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "bundles" for t in n.targets)
        )
        bundles = ast.literal_eval(assignment.value)
        self.assertEqual(len(bundles), 29)
        for project in catalog()["projects"]:
            if "starter_url" not in project:
                continue
            with self.subTest(project=project["id"]):
                name, files = bundles[project["id"]]
                response = self.client.get(project["starter_url"])
                self.assertEqual(response.status_code, 200)
                with ZipFile(io.BytesIO(response.content)) as archive:
                    self.assertEqual(set(archive.namelist()), {f"{name}/{f}" for f in files})
                    self.assertFalse(any("reference" in p for p in archive.namelist()))

    def test_structural_audit_and_changed_previous_definition_rejection(self):
        report = audit()
        self.assertEqual(report["lessons"], 195)
        self.assertTrue(report["dependencies_acyclic"])
        old = {p.name: json.loads(p.read_text()) for p in (ROOT / "content").glob("*.json")}
        old["catalog.json"]["lessons"][0]["skill"] = "invented denominator"
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "baseline.json"
            file.write_text(json.dumps(old))
            with self.assertRaises(AssertionError):
                audit(file)
