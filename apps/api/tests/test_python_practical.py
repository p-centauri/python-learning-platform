import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

from fastapi.testclient import TestClient
import test_academy
from app.config import settings
from app.content import lessons, exam_definitions
from app.main import app

MODULE = [lesson for lesson in lessons() if lesson["module_id"] == "python-practical-module"]


class PracticalContentTests(unittest.TestCase):
    def test_sequence_and_trusted_examples(self):
        self.assertEqual(len(MODULE), 5)
        exam_prompts = {q["prompt"] for exam in exam_definitions() for q in exam["questions"]}
        for i, lesson in enumerate(MODULE):
            self.assertEqual(lesson["prerequisites"], ["python-tests" if i == 0 else MODULE[i - 1]["id"]])
            self.assertEqual(len(lesson["exercises"]), 2)
            self.assertFalse({q["prompt"] for q in lesson["exercises"]} & exam_prompts)
            body = (settings.content_dir / lesson["path"]).read_text()
            for label in [
                "## Guided practice",
                "## Independent",
                "## Check your work" if i < 4 else "## Explained approach",
            ]:
                self.assertIn(label, body)
            for target in re.findall(r"\]\(/lessons/([a-z-]+)\)", body):
                self.assertIn(target, {lesson["id"] for lesson in lessons()})
            # Only fixed authored code, never learner submissions; no pdb blocks run automatically.
            code = "\n\n".join(re.findall(r"```python\n(.*?)```", body, flags=re.S))
            with self.subTest(lesson=lesson["id"]), tempfile.TemporaryDirectory() as directory:
                result = subprocess.run(
                    [sys.executable, "-I", "-c", code],
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_repair_suite_detects_starter_bugs_and_passes_reference(self):
        source = settings.content_dir / "projects" / "event-timeline"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "lab"
            shutil.copytree(source / "starter", root, ignore=shutil.ignore_patterns("__pycache__"))
            command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
            broken = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=15)
            self.assertNotEqual(broken.returncode, 0)
            for test in [
                "test_unicode_label_policy",
                "test_offsets_are_converted_and_sorted",
                "test_fractional_seconds_and_negative_offset",
                "test_invalid_encoding_json_and_top_level",
            ]:
                self.assertIn("FAIL: " + test, broken.stderr)
            shutil.copyfile(source / "reference/events.py", root / "events.py")
            shutil.rmtree(root / "__pycache__", ignore_errors=True)
            fixed = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=15)
            self.assertEqual(fixed.returncode, 0, fixed.stderr)
            self.assertIn("Ran 13 tests", fixed.stderr)


class PracticalAPITests(unittest.TestCase):
    setUp = test_academy.AcademyTests.setUp
    tearDown = test_academy.AcademyTests.tearDown
    register = test_academy.AcademyTests.register
    other_learner = test_academy.AcademyTests.other_learner

    def test_new_lessons_keep_answers_private_and_follow_foundations(self):
        data = self.client.get("/api/curriculum").json()
        self.assertEqual(
            [lesson["id"] for lesson in data["lessons"]][9:14], [lesson["id"] for lesson in MODULE]
        )
        for lesson in lessons()[:9]:
            self.client.put(f"/api/lessons/{lesson['id']}/complete")
        dashboard = self.client.get("/api/dashboard").json()
        self.assertEqual(dashboard["next_lesson"]["id"], "python-text-bytes")
        self.assertEqual(dashboard["mastery"], 0)
        for lesson in MODULE:
            response = self.client.get(f"/api/lessons/{lesson['id']}")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(
                all("answer" not in q and "solution" not in q for q in response.json()["exercises"])
            )
        practice = MODULE[0]["exercises"][0]
        base = f"/api/exercises/{practice['id']}"
        self.assertIsNone(self.client.get(base).json()["solution"])
        response = self.client.post(base + "/attempts", json={"answer": practice["answer"]})
        self.assertEqual(response.json()["score"], 100)
        self.assertTrue(response.json()["solution"])

    def test_lab_download_and_progress_are_isolated(self):
        path = "/api/projects/python-event-timeline/starter"
        with TestClient(app) as anonymous:
            self.assertEqual(anonymous.get(path).status_code, 401)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertIn("event-timeline-starter.zip", response.headers["content-disposition"])
        with ZipFile(io.BytesIO(response.content)) as archive:
            self.assertEqual(
                set(archive.namelist()),
                {
                    f"event-timeline/{name}"
                    for name in [
                        "README.md",
                        "events.py",
                        "cli.py",
                        "sample.json",
                        "expected.json",
                        "tests/test_events.py",
                    ]
                },
            )
            self.assertIn(b"Deliberately buggy", archive.read("event-timeline/events.py"))
            self.assertIsInstance(json.loads(archive.read("event-timeline/expected.json")), list)
        self.client.put("/api/projects/python-event-timeline/tasks/reproduce", json={"enabled": True})
        mine = next(p for p in self.client.get("/api/projects").json() if p["id"] == "python-event-timeline")
        theirs = next(
            p for p in self.other_learner().get("/api/projects").json() if p["id"] == "python-event-timeline"
        )
        self.assertTrue(mine["tasks"][0]["completed"])
        self.assertFalse(theirs["tasks"][0]["completed"])
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)
