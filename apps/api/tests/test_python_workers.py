"""Trusted authored content and local package checks; never learner execution."""

import io
import json
import os
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
from app.content import catalog, exam_definitions, lessons
from app.interactivity import interaction_content
from app.main import app
from app.projects import rubric_content
from app.retention import review_content

MODULE = [lesson for lesson in lessons() if lesson["module_id"] == "python-worker-module"]
PROJECT = settings.content_dir / "projects/leased-worker"
FILES = {
    "demo.py",
    "tests/test_contracts.py",
    "README.md",
    "pyproject.toml",
    "src/academy_leased_worker/py.typed",
    "src/academy_leased_worker/schema.py",
    "src/academy_leased_worker/schema.sql",
    "src/academy_leased_worker/contracts.py",
    "tests/conftest.py",
    "worker_process.py",
    "src/academy_leased_worker/evidence.py",
    "src/academy_leased_worker/core.py",
    "src/academy_leased_worker/__init__.py",
    "tests/test_postgres.py",
}


def run(args, root, *, env=None, timeout=60):
    return subprocess.run(args, cwd=root, env=env, capture_output=True, text=True, timeout=timeout)


def reference_copy(root):
    shutil.copytree(
        PROJECT / "starter",
        root,
        ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"),
    )
    for name in ["core.py"]:
        shutil.copyfile(PROJECT / "reference" / name, root / "src/academy_leased_worker" / name)
    service = settings.content_dir / "projects/ingestion-service"
    dependency = root.parent / "completed-service"
    shutil.copytree(
        service / "starter",
        dependency,
        ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"),
    )
    for name in ["auth.py", "service.py"]:
        shutil.copyfile(service / "reference" / name, dependency / "src/academy_ingestion_service" / name)
    competition = settings.content_dir / "projects/competing-ingestion"
    second = root.parent / "completed-competition"
    shutil.copytree(
        competition / "starter",
        second,
        ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"),
    )
    for name in ["retry.py", "reconcile.py"]:
        shutil.copyfile(competition / "reference" / name, second / "src/academy_competing_ingestion" / name)
    outbox = settings.content_dir / "projects/durable-outbox"
    third = root.parent / "completed-outbox"
    shutil.copytree(
        outbox / "starter",
        third,
        ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"),
    )
    shutil.copyfile(outbox / "reference/core.py", third / "src/academy_durable_outbox/core.py")


class WorkerContentTests(unittest.TestCase):
    def test_sequence_examples_and_complete_teaching_layers(self):
        self.assertEqual(len(MODULE), 6)
        self.assertEqual({lesson["skill"] for lesson in MODULE}, {"Worker lease contracts"})
        exams = {q["prompt"] for exam in exam_definitions() for q in exam["questions"]}
        previous = "python-outbox-evidence"
        for lesson in MODULE:
            self.assertEqual(lesson["prerequisites"], [previous])
            previous = lesson["id"]
            self.assertEqual(len(lesson["exercises"]), 2)
            self.assertFalse(exams & {q["prompt"] for q in lesson["exercises"]})
            self.assertIn(lesson["id"], interaction_content()["lessons"])
            self.assertEqual(
                len(next(t for t in review_content()["concepts"] if t["id"] == lesson["id"])["questions"]), 2
            )
            body = (settings.content_dir / lesson["path"]).read_text()
            self.assertFalse(body.startswith("# "), "The page already supplies its main title")
            for marker in ["## Guided practice", "## Independent", "## Check your work"]:
                self.assertIn(marker, body)
            for target in re.findall(r"\]\(/lessons/([a-z-]+)\)", body):
                self.assertIn(target, {item["id"] for item in lessons()})
            code = "\n\n".join(re.findall(r"```python\n(.*?)```", body, flags=re.S))
            with self.subTest(lesson=lesson["id"]), tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / "example.py"
                source.write_text(code)
                result = run([sys.executable, "-I", str(source)], directory)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                typed = run([sys.executable, "-m", "mypy", "--strict", str(source)], directory)
                self.assertEqual(typed.returncode, 0, typed.stdout + typed.stderr)

    def test_reference_types_lint_and_unfinished_offline_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "lab"
            reference_copy(root)
            env = {
                **os.environ,
                "PYTHONPATH": os.pathsep.join(
                    [
                        str(root / "src"),
                        str(root.parent / "completed-service/src"),
                        str(root.parent / "completed-competition/src"),
                        str(root.parent / "completed-outbox/src"),
                    ]
                ),
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            }
            env.pop("ACADEMY_WORKER_DSN", None)
            result = run([sys.executable, "-m", "pytest", "-q", "tests"], root, env=env)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("35 passed, 24 skipped", result.stdout)
            for command in [
                [sys.executable, "-m", "mypy", "--strict", "src", "demo.py", "worker_process.py"],
                [sys.executable, "-m", "ruff", "check", "src", "tests", "demo.py"],
            ]:
                result = run(command, root, env=env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            shutil.copyfile(
                PROJECT / "starter/src/academy_leased_worker/core.py",
                root / "src/academy_leased_worker/core.py",
            )
            result = run([sys.executable, "-m", "pytest", "-q", "tests/test_contracts.py"], root, env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("NotImplementedError", result.stdout)

    def test_real_artifacts_resources_and_quiet_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "lab"
            reference_copy(root)
            env = {
                **os.environ,
                "PYTHONPATH": os.pathsep.join(
                    [
                        str(root / "src"),
                        str(root.parent / "completed-service/src"),
                        str(root.parent / "completed-competition/src"),
                        str(root.parent / "completed-outbox/src"),
                    ]
                ),
            }
            quiet = run([sys.executable, "-c", "import academy_leased_worker"], root, env=env)
            self.assertEqual(quiet.returncode, 0, quiet.stderr)
            self.assertEqual(quiet.stdout + quiet.stderr, "")
            build = run([sys.executable, "-m", "build", "--no-isolation"], root)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            self.assertIn("Building wheel from sdist", build.stdout)
            with ZipFile(next((root / "dist").glob("*.whl"))) as archive:
                self.assertIn("academy_leased_worker/py.typed", archive.namelist())
                self.assertIn("academy_leased_worker/schema.sql", archive.namelist())
                metadata = archive.read("academy_leased_worker_lab-0.1.0.dist-info/METADATA").decode()
                self.assertIn("Requires-Dist: academy-durable-outbox-lab==0.1.0", metadata)
                self.assertFalse(any("reference" in f or "tests/" in f for f in archive.namelist()))


class WorkerAPITests(unittest.TestCase):
    setUp = test_academy.AcademyTests.setUp
    tearDown = test_academy.AcademyTests.tearDown
    register = test_academy.AcademyTests.register
    other_learner = test_academy.AcademyTests.other_learner

    def test_route_practice_checkpoint_recall_privacy_and_evidence(self):
        curriculum = self.client.get("/api/curriculum").json()
        self.assertEqual(
            [lesson["id"] for lesson in curriculum["lessons"]][111:117], [lesson["id"] for lesson in MODULE]
        )
        for lesson in lessons()[:111]:
            self.client.put(f"/api/lessons/{lesson['id']}/complete")
        self.assertEqual(self.client.get("/api/dashboard").json()["next_lesson"]["id"], MODULE[0]["id"])
        for lesson in MODULE:
            data = self.client.get(f"/api/lessons/{lesson['id']}").json()
            self.assertTrue(all("answer" not in q and "solution" not in q for q in data["exercises"]))
            activities = self.client.get(f"/api/lesson-activities/{lesson['id']}").json()
            self.assertNotIn('"answer"', json.dumps(activities))
            self.assertNotIn('"validation"', json.dumps(activities))
        topic = self.client.post(
            "/api/recall/topics/python-worker-fencing/sessions", json={"mode": "practice"}
        )
        self.assertEqual(topic.status_code, 201)
        self.assertNotIn('"accepted"', topic.text)
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)
        question = MODULE[0]["exercises"][0]
        url = f"/api/exercises/{question['id']}"
        self.assertIsNone(self.client.get(url).json()["solution"])
        result = self.client.post(url + "/attempts", json={"answer": question["answer"]}).json()
        self.assertEqual(result["score"], 100)
        self.assertEqual(
            self.client.get("/api/lessons/python-outbox-evidence").json()["navigation"]["next"]["id"],
            "python-worker-leases",
        )

    def test_download_fixed_files_and_account_owned_workflow(self):
        url = "/api/projects/python-leased-worker/starter"
        with TestClient(app) as anonymous:
            self.assertEqual(anonymous.get(url).status_code, 401)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        with ZipFile(io.BytesIO(response.content)) as archive:
            self.assertEqual(set(archive.namelist()), {f"leased-worker/{name}" for name in FILES})
            self.assertIn(
                b"NotImplementedError",
                archive.read("leased-worker/src/academy_leased_worker/core.py"),
            )
        self.assertEqual(self.client.get("/api/projects/leased-worker/starter").status_code, 404)
        self.client.put("/api/projects/python-leased-worker/tasks/lease", json={"enabled": True})
        project = next(
            p for p in self.client.get("/api/projects").json() if p["id"] == "python-leased-worker"
        )
        other = next(p for p in self.other_learner().get("/api/projects").json() if p["id"] == project["id"])
        self.assertTrue(project["tasks"][0]["completed"])
        self.assertFalse(other["tasks"][0]["completed"])
        draft = self.client.post(f"/api/projects/{project['id']}/submissions").json()
        self.assertEqual(draft["rubric"]["criteria"], rubric_content()["projects"][project["id"]])
        self.assertEqual(len(draft["rubric"]["criteria"]), 4)
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)
        # Earlier skills retain their original question sets and denominators.
        self.assertEqual(
            sum(
                len(lesson["exercises"])
                for lesson in catalog()["lessons"]
                if lesson["skill"] == "Python streaming"
            ),
            10,
        )
