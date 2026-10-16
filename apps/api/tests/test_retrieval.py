"""Content, privacy and learner workflow; executable reference checks have a separate verifier."""

import io
import json
from pathlib import Path
import re
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

MODULE = [lesson for lesson in lessons() if lesson["module_id"] == "retrieval-practice-module"]
FILES = {
    "RETRIEVAL_CONTRACT.md",
    "src/academy_retrieval/fixture.json",
    "README.md",
    "src/academy_retrieval/contracts.py",
    "src/academy_retrieval/py.typed",
    "tests/test_metrics.py",
    "src/academy_retrieval/support.py",
    "src/academy_retrieval/__init__.py",
    "tests/test_fixture.py",
    "demo.py",
    "pyproject.toml",
    "tests/test_chunks.py",
    "src/academy_retrieval/operations.py",
    "tests/test_ranking.py",
    "src/academy_retrieval/dataset.py",
}


class RetrievalContentTests(unittest.TestCase):
    def test_complete_ordered_layers_runnable_examples_and_existing_denominators(self):
        self.assertEqual(len(MODULE), 6)
        self.assertEqual({lesson["skill"] for lesson in MODULE}, {"Scoped retrieval contracts"})
        exams = {q["prompt"] for exam in exam_definitions() for q in exam["questions"]}
        previous = "embedding-retrieval"
        with tempfile.TemporaryDirectory() as directory:
            for lesson in MODULE:
                self.assertEqual(
                    lesson["prerequisites"],
                    [previous, "model-contract-evidence"] if lesson == MODULE[0] else [previous],
                )
                previous = lesson["id"]
                self.assertEqual(len(lesson["exercises"]), 2)
                self.assertFalse(exams & {q["prompt"] for q in lesson["exercises"]})
                interaction = interaction_content()["lessons"][lesson["id"]]
                self.assertEqual(len(interaction["checkpoints"]), 2)
                self.assertEqual(len(interaction["diagram"]["steps"]), 3)
                self.assertEqual(len(interaction["glossary_ids"]), 2)
                concept = next(c for c in review_content()["concepts"] if c["id"] == lesson["id"])
                self.assertEqual(len(concept["questions"]), 2)
                body = (settings.content_dir / lesson["path"]).read_text()
                for marker in ("## Guided practice", "## Independent practice", "## Check your work"):
                    self.assertIn(marker, body)
                self.assertFalse(body.startswith("# "))
                code = "\n\n".join(re.findall(r"```python\n(.*?)```", body, re.S))
                source = Path(directory) / (lesson["id"] + ".py")
                source.write_text(code)
                result = subprocess.run(
                    [sys.executable, "-I", str(source)], capture_output=True, text=True, timeout=10
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            typed = subprocess.run(
                [sys.executable, "-m", "mypy", "--strict", directory],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(typed.returncode, 0, typed.stdout + typed.stderr)
        self.assertEqual(
            sum(
                len(lesson["exercises"])
                for lesson in lessons()
                if lesson["skill"] == "Delivery migration contracts"
            ),
            12,
        )
        self.assertEqual(
            sum(len(lesson["exercises"]) for lesson in lessons() if lesson["skill"] == "Python streaming"), 10
        )
        self.assertEqual([len(e["questions"]) for e in exam_definitions() if e.get("level") != "Comprehensive"], [10, 20, 24, 28])
        self.assertEqual(len(catalog()["lessons"]), 195)


class RetrievalAPITests(unittest.TestCase):
    setUp = test_academy.AcademyTests.setUp
    tearDown = test_academy.AcademyTests.tearDown
    register = test_academy.AcademyTests.register
    other_learner = test_academy.AcademyTests.other_learner

    def test_navigation_practice_guidance_and_recall_keys_are_private(self):
        navigation = self.client.get("/api/lessons/embedding-retrieval").json()["navigation"]
        self.assertEqual(navigation["next"]["id"], MODULE[0]["id"])
        for lesson in MODULE:
            data = self.client.get(f"/api/lessons/{lesson['id']}").json()
            self.assertEqual(data["id"], lesson["id"])
            self.assertTrue(all("answer" not in q and "solution" not in q for q in data["exercises"]))
            guided = self.client.get(f"/api/lesson-activities/{lesson['id']}").json()
            self.assertNotIn('"answer"', json.dumps(guided))
            self.assertNotIn('"validation"', json.dumps(guided))
        question = MODULE[0]["exercises"][0]
        path = f"/api/exercises/{question['id']}"
        self.assertIsNone(self.client.get(path).json()["solution"])
        result = self.client.post(path + "/attempts", json={"answer": question["answer"]})
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.json()["score"], 100)
        recall = self.client.post(
            "/api/recall/topics/retrieval-metric-denominators/sessions", json={"mode": "practice"}
        )
        self.assertEqual(recall.status_code, 201)
        self.assertNotIn('"accepted"', recall.text)
        self.assertNotIn('"explanation"', recall.text)

    def test_exact_download_real_links_and_account_owned_manual_evidence(self):
        project_id = "retrieval"
        url = f"/api/projects/{project_id}/starter"
        with TestClient(app) as anonymous:
            self.assertEqual(anonymous.get(url).status_code, 401)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        with ZipFile(io.BytesIO(response.content)) as archive:
            self.assertEqual(set(archive.namelist()), {f"retrieval/{name}" for name in FILES})
            self.assertIn(
                b"raise NotImplementedError",
                archive.read("retrieval/src/academy_retrieval/operations.py"),
            )
            self.assertFalse(any("reference" in name for name in archive.namelist()))
        self.assertEqual(self.client.get("/api/projects/offline-retrieval/starter").status_code, 404)
        project = next(p for p in self.client.get("/api/projects").json() if p["id"] == project_id)
        self.assertEqual(project["lesson_id"], "retrieval-evidence")
        self.assertEqual(project["starter_url"], url)
        self.assertEqual(
            self.client.put(f"/api/projects/{project_id}/tasks/chunks", json={"enabled": True}).status_code,
            200,
        )
        other_client = self.other_learner()
        other = next(p for p in other_client.get("/api/projects").json() if p["id"] == project_id)
        self.assertFalse(other["tasks"][0]["completed"])
        draft = self.client.post(f"/api/projects/{project_id}/submissions").json()
        self.assertEqual(draft["rubric"]["criteria"], rubric_content()["projects"][project_id])
        self.assertEqual(len(draft["rubric"]["criteria"]), 4)
        path = f"/api/project-submissions/{draft['id']}"
        artifact = {
            "repository_url": "https://github.com/fixture/retrieval",
            "revision_ref": "review-fixture-1",
            "design_notes": "Fixture: predict an old-public fallback and requested-k denominator edge; keep model quality unverified.",
            "evidence": "Fixture artifact: retrieval.json and an independently explained regression. Hand-supplied development vectors do not certify embedding-model quality.",
            "test_status": "passed",
            "test_command": "python -I -m pytest -q tests",
            "test_output": "Reported fixture output",
            "change_summary": "",
        }
        self.assertEqual(self.client.put(path, json=artifact).status_code, 200)
        submitted = self.client.post(path + "/submit").json()
        self.assertEqual(submitted["artifact"], artifact)
        self.assertEqual(submitted["rubric"]["criteria"], draft["rubric"]["criteria"])
        self.assertEqual(other_client.get(path).status_code, 404)
        revised = self.client.post(f"/api/projects/{project_id}/submissions").json()
        self.assertEqual(revised["revision"], 2)
        self.assertEqual(self.client.get(path).json()["artifact"], artifact)
        self.assertEqual(self.client.get("/api/dashboard").json()["mastery"], 0)
