"""Author-controlled portfolio briefs and exact authenticated build packs."""

from functools import lru_cache
from io import BytesIO
import json
from zipfile import ZipFile, ZIP_DEFLATED
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from .auth import Learner
from .config import settings
from .projects import project_definition, rubric_for
from .content import lesson_by_id

router = APIRouter(tags=["portfolio build packs"])
PORTFOLIO_FILES = (
    "README.md",
    "BRIEF.md",
    "app.py",
    "EVIDENCE.md",
    "fixtures.json",
    "pytest.ini",
    "tests/test_acceptance.py",
)
REPAIR_FILES = (
    "README.md",
    "CONTRACT.md",
    "core.py",
    "server.py",
    "Dockerfile",
    "public-cases.json",
    "tests/test_public.py",
)


@lru_cache
def briefs():
    return json.loads((settings.content_dir / "portfolio-projects.json").read_text())


@router.get("/projects/{project_id}/brief")
def brief(project_id: str, user: Learner):
    data = briefs()
    if project_id not in data["projects"]:
        raise HTTPException(404, "Portfolio brief not found.")
    return {
        **data["projects"][project_id],
        "version": data["version"],
        "milestones": project_definition(project_id)["tasks"],
        "rubric": rubric_for(project_id),
        "learning_titles": {id: lesson_by_id(id)["title"] for id in data["projects"][project_id]["learning"]},
    }


def archive(base, files, name):
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as bundle:
        for file in files:
            bundle.writestr(f"{name}/{file}", (base / file).read_bytes())
    return Response(
        output.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{name}.zip"'},
    )


@router.get("/portfolio-packs/{project_id}")
def portfolio_pack(project_id: str, user: Learner):
    if project_id not in {"backend", "enterprise-rag", "finance"}:
        raise HTTPException(404, "Portfolio pack not found.")
    return archive(settings.content_dir / "portfolio-packs" / project_id, PORTFOLIO_FILES, project_id)


@router.get("/exam-packs/{exam_id}")
def exam_pack(exam_id: str, user: Learner):
    if exam_id != "practical-repair-v1":
        raise HTTPException(404, "Exam pack not found.")
    return archive(settings.content_dir / "exam-packs" / exam_id / "starter", REPAIR_FILES, exam_id)
