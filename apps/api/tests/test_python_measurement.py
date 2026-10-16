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

MODULE = [lesson for lesson in lessons() if lesson["module_id"] == "python-measurement-module"]
PROJECT = settings.content_dir / "projects/measured-cache"
FILES = {
    "README.md",
    "pyproject.toml",
    "demo.py",
    "src/academy_measured_cache/__init__.py",
    "src/academy_measured_cache/contracts.py",
    "src/academy_measured_cache/measurement.py",
    "src/academy_measured_cache/cache.py",
    "src/academy_measured_cache/py.typed",
    "tests/test_measurement.py",
    "tests/test_cache.py",
}


def run(args, root, *, env=None, timeout=60):
    return subprocess.run(args, cwd=root, env=env, capture_output=True, text=True, timeout=timeout)


def reference_copy(root):
    shutil.copytree(PROJECT / "starter", root, ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache"))
    for name in ["measurement.py", "cache.py"]:
        shutil.copyfile(PROJECT / "reference" / name, root / "src/academy_measured_cache" / name)


class MeasurementContentTests(unittest.TestCase):
    def test_sequence_examples_and_complete_teaching_layers(self):
        self.assertEqual(len(MODULE), 8)
        self.assertEqual({lesson["skill"] for lesson in MODULE}, {"Python measurement contracts"})
        exams = {q["prompt"] for exam in exam_definitions() for q in exam["questions"]}
        previous = "python-offload-contracts"
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

    def test_reference_behavior_types_lint_and_starter_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "lab"
            reference_copy(root)
            env = {**os.environ, "PYTHONPATH": str(root / "src"), "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
            command = [sys.executable, "-m", "pytest", "-q"]
            result = run(command, root, env=env)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("61 passed", result.stdout)
            typed = run([sys.executable, "-m", "mypy", "src/academy_measured_cache", "demo.py"], root)
            self.assertEqual(typed.returncode, 0, typed.stdout + typed.stderr)
            lint = run(
                [
                    sys.executable,
                    "-m",
                    "ruff",
                    "check",
                    "src",
                    "tests",
                    "demo.py",
                ],
                root,
            )
            self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)
            for name in ["measurement.py", "cache.py"]:
                shutil.copyfile(
                    PROJECT / "starter/src/academy_measured_cache" / name,
                    root / "src/academy_measured_cache" / name,
                )
            shutil.rmtree(root / "src/academy_measured_cache/__pycache__", ignore_errors=True)
            broken = run(command, root, env=env)
            self.assertNotEqual(broken.returncode, 0)
            self.assertIn("NotImplementedError", broken.stdout)

    def test_demo_real_observations_and_quiet_instrumentation_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "lab"
            reference_copy(root)
            env = {**os.environ, "PYTHONPATH": str(root / "src")}
            quiet = run(
                [
                    sys.executable,
                    "-c",
                    "import tracemalloc; before=tracemalloc.is_tracing(); import academy_measured_cache; assert tracemalloc.is_tracing()==before",
                ],
                root,
                env=env,
            )
            self.assertEqual(quiet.returncode, 0, quiet.stderr)
            self.assertEqual(quiet.stdout + quiet.stderr, "")
            result = run([sys.executable, "demo.py", "--output", "measurement.json"], root, env=env)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data, json.loads((root / "measurement.json").read_text()))
            self.assertEqual(data["schema"], "2026.10-measurement-v1")
            self.assertEqual(data["workload_items"], 32)
            self.assertEqual(data["baseline_computations"], 32)
            self.assertEqual(data["cached_computations"], 4)
            self.assertEqual(data["cached_hits"], 28)
            self.assertEqual(data["cache_state"], "fresh per repetition")
            self.assertEqual(len(data["variant_order"]), 4)
            for values in data["timings_ns"].values():
                self.assertEqual(len(values), 3)
                self.assertTrue(all(type(value) is int and value >= 0 for value in values))
            self.assertEqual(set(data["memory_traced_bytes"]), {"before", "filled", "after_clear", "peak"})
            self.assertTrue(all(type(value) is int for value in data["memory_traced_bytes"].values()))
            self.assertGreater(data["profile_functions"], 0)
            self.assertIn("function calls", data["profile_text"])
            self.assertEqual(result.stderr, "")

    def test_real_wheel_contents_and_build_from_source_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "lab"
            reference_copy(root)
            build = run([sys.executable, "-m", "build", "--no-isolation"], root)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            wheel = next((root / "dist").glob("*.whl"))
            with ZipFile(wheel) as archive:
                self.assertIn("academy_measured_cache/py.typed", archive.namelist())
                self.assertIn("academy_measured_cache/measurement.py", archive.namelist())
                metadata = archive.read("academy_measured_cache_lab-0.1.0.dist-info/METADATA").decode()
                self.assertNotIn("Requires-Dist: httpx", metadata)
                self.assertFalse(
                    any("reference" in f or "tests/" in f or "typing/" in f for f in archive.namelist())
                )
            # build's default mode builds the wheel from its freshly extracted sdist.
            self.assertIn("Building wheel from sdist", build.stdout)


class MeasurementAPITests(unittest.TestCase):
    setUp = test_academy.AcademyTests.setUp
    tearDown = test_academy.AcademyTests.tearDown
    register = test_academy.AcademyTests.register
    other_learner = test_academy.AcademyTests.other_learner

    def test_route_practice_checkpoint_recall_privacy_and_evidence(self):
        curriculum = self.client.get("/api/curriculum").json()
        self.assertEqual(
            [lesson["id"] for lesson in curriculum["lessons"]][74:82], [lesson["id"] for lesson in MODULE]
        )
        for lesson in lessons()[:74]:
            self.client.put(f"/api/lessons/{lesson['id']}/complete")
        self.assertEqual(self.client.get("/api/dashboard").json()["next_lesson"]["id"], MODULE[0]["id"])
        for lesson in MODULE:
            data = self.client.get(f"/api/lessons/{lesson['id']}").json()
            self.assertTrue(all("answer" not in q and "solution" not in q for q in data["exercises"]))
            activities = self.client.get(f"/api/lesson-activities/{lesson['id']}").json()
            self.assertNotIn('"answer"', json.dumps(activities))
            self.assertNotIn('"validation"', json.dumps(activities))
        topic = self.client.post(
            "/api/recall/topics/python-cache-lifetime/sessions", json={"mode": "practice"}
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
            self.client.get("/api/lessons/python-offload-contracts").json()["navigation"]["next"]["id"],
            "python-measurement-baselines",
        )

    def test_download_fixed_files_and_account_owned_workflow(self):
        url = "/api/projects/python-measured-cache/starter"
        with TestClient(app) as anonymous:
            self.assertEqual(anonymous.get(url).status_code, 401)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        with ZipFile(io.BytesIO(response.content)) as archive:
            self.assertEqual(set(archive.namelist()), {f"measured-cache/{name}" for name in FILES})
            self.assertIn(
                b"NotImplementedError",
                archive.read("measured-cache/src/academy_measured_cache/measurement.py"),
            )
        self.assertEqual(self.client.get("/api/projects/measured-cache/starter").status_code, 404)
        self.client.put("/api/projects/python-measured-cache/tasks/measurement", json={"enabled": True})
        project = next(
            p for p in self.client.get("/api/projects").json() if p["id"] == "python-measured-cache"
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
