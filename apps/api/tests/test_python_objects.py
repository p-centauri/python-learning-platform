import io
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
from app.content import exam_definitions, lessons
from app.main import app

MODULE = [lesson for lesson in lessons() if lesson["module_id"] == "python-objects-module"]
PROJECT = settings.content_dir / "projects" / "task-inbox"


class ObjectContentTests(unittest.TestCase):
    def test_order_examples_and_distinct_practice(self):
        self.assertEqual(len(MODULE), 5)
        exams = {q["prompt"] for exam in exam_definitions() for q in exam["questions"]}
        for index, lesson in enumerate(MODULE):
            self.assertEqual(
                lesson["prerequisites"], ["python-ownership" if index == 0 else MODULE[index - 1]["id"]]
            )
            self.assertEqual(len(lesson["exercises"]), 2)
            self.assertFalse(exams & {q["prompt"] for q in lesson["exercises"]})
            body = (settings.content_dir / lesson["path"]).read_text()
            for marker in ["## Guided practice", "## Independent", "## Check your work"]:
                self.assertIn(marker, body)
            for target in re.findall(r"\]\(/lessons/([a-z-]+)\)", body):
                self.assertIn(target, {item["id"] for item in lessons()})
            code = "\n\n".join(re.findall(r"```python\n(.*?)```", body, flags=re.S))
            with self.subTest(lesson=lesson["id"]), tempfile.TemporaryDirectory() as directory:
                # Only trusted authored examples, never submitted learner code.
                source = Path(directory) / "example.py"
                source.write_text(code)
                run = subprocess.run(
                    [sys.executable, "-I", str(source)],
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self.assertEqual(run.returncode, 0, run.stderr)
                typed = subprocess.run(
                    [sys.executable, "-m", "mypy", "--strict", str(source)],
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(typed.returncode, 0, typed.stdout + typed.stderr)

    def test_reference_runtime_and_types(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "lab"
            shutil.copytree(
                PROJECT / "starter", root, ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache")
            )
            command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
            broken = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=15)
            self.assertNotEqual(broken.returncode, 0)
            self.assertIn("NotImplementedError", broken.stderr)
            shutil.copyfile(PROJECT / "reference/inbox.py", root / "inbox.py")
            shutil.rmtree(root / "__pycache__", ignore_errors=True)
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Ran 14 tests", result.stderr)
            typed = subprocess.run(
                [sys.executable, "-m", "mypy", "--strict", "inbox.py", "demo.py", "typecheck_examples.py"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(typed.returncode, 0, typed.stdout + typed.stderr)
            fixture = root / "typecheck_examples.py"
            fixture.write_text(fixture.read_text().replace(
                "def all(self) -> tuple[Task, ...]:\n        return tuple(self.tasks)",
                'def all(self) -> tuple[str, ...]:\n        return ("wrong",)',
            ))
            invalid = subprocess.run(
                [sys.executable, "-m", "mypy", "--strict", "typecheck_examples.py"],
                cwd=root, capture_output=True, text=True, timeout=30,
            )
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("incompatible", invalid.stdout.lower())


class ObjectAPITests(unittest.TestCase):
    setUp = test_academy.AcademyTests.setUp
    tearDown = test_academy.AcademyTests.tearDown
    register = test_academy.AcademyTests.register
    other_learner = test_academy.AcademyTests.other_learner

    def test_continuation_privacy_and_scoring(self):
        curriculum = self.client.get("/api/curriculum").json()
        self.assertEqual(
            [item["id"] for item in curriculum["lessons"]][15:20], [lesson["id"] for lesson in MODULE]
        )
        for lesson in lessons()[:15]:
            self.client.put(f"/api/lessons/{lesson['id']}/complete")
        dashboard = self.client.get("/api/dashboard").json()
        self.assertEqual(dashboard["next_lesson"]["id"], "python-classes")
        self.assertEqual(dashboard["mastery"], 0)
        for lesson in MODULE:
            data = self.client.get(f"/api/lessons/{lesson['id']}").json()
            self.assertTrue(all("answer" not in q and "solution" not in q for q in data["exercises"]))
        exercise = MODULE[0]["exercises"][0]
        url = f"/api/exercises/{exercise['id']}"
        self.assertIsNone(self.client.get(url).json()["solution"])
        data = self.client.post(url + "/attempts", json={"answer": exercise["answer"]}).json()
        self.assertEqual(data["score"], 100)
        self.assertTrue(data["solution"])

    def test_download_auth_allowlist_and_project_isolation(self):
        url = "/api/projects/python-task-inbox/starter"
        with TestClient(app) as anonymous:
            self.assertEqual(anonymous.get(url).status_code, 401)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("task-inbox-starter.zip", response.headers["content-disposition"])
        with ZipFile(io.BytesIO(response.content)) as archive:
            self.assertEqual(
                set(archive.namelist()),
                {
                    f"task-inbox/{name}"
                    for name in [
                        "README.md",
                        "inbox.py",
                        "demo.py",
                        "typecheck_examples.py",
                        "pyproject.toml",
                        "tests/test_inbox.py",
                    ]
                },
            )
            self.assertIn(b"NotImplementedError", archive.read("task-inbox/inbox.py"))
        self.client.put("/api/projects/python-task-inbox/tasks/values", json={"enabled": True})
        mine = next(p for p in self.client.get("/api/projects").json() if p["id"] == "python-task-inbox")
        theirs = next(
            p for p in self.other_learner().get("/api/projects").json() if p["id"] == "python-task-inbox"
        )
        self.assertTrue(mine["tasks"][0]["completed"])
        self.assertFalse(theirs["tasks"][0]["completed"])
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)
