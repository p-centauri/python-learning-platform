"""Frozen exam workspaces; executable evidence comes only from the private runner."""

from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from .auth import DB, Learner
from .coding import runner_request, safe_result
from .models import ExamAttempt, ExamRun, ProjectSubmission, utcnow
from .projects import utc_timestamp, rubric_content

router = APIRouter(tags=["comprehensive exams"])


def owned(id, user, db):
    row = db.scalar(select(ExamAttempt).where(ExamAttempt.id == id, ExamAttempt.user_id == user.id))
    if row is None:
        raise HTTPException(404, "Assessment attempt not found.")
    if not row.definition_snapshot:
        raise HTTPException(409, "Missing frozen assessment definition.")
    return row


def visible_questions(row):
    exam = row.definition_snapshot
    if exam.get("mode") != "design":
        return exam["questions"]
    stage = row.workspace.get("stage", 0)
    return [q for s in exam["stages"][: stage + 1] for q in s["questions"]]


def require_active(row):
    if row.status != "active":
        raise HTTPException(409, "Submitted exam evidence is fixed.")


def validate_answer(q, value, final=False):
    kind = q.get("kind", "single")
    if kind == "short":
        valid = isinstance(value, str) and len(value) <= q.get("max_length", 1000)
        if final:
            valid = valid and len(value.strip()) >= q.get("min_length", 30)
    elif kind == "multiple":
        valid = (
            isinstance(value, list)
            and (1 if final else 0) <= len(value) <= len(q["options"])
            and all(type(v) is int and 0 <= v < len(q["options"]) for v in value)
            and len(set(value)) == len(value)
        )
    else:
        valid = type(value) is int and 0 <= value < len(q["options"])
    if not valid:
        raise HTTPException(
            422, "Invalid answer for this question. Written submissions must meet the stated minimum."
        )


def complete(questions, answers):
    for q in questions:
        if q["id"] not in answers:
            raise HTTPException(422, "Complete every required response before continuing.")
        validate_answer(q, answers[q["id"]], final=True)


class WorkspaceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    flags: list[str] = Field(default_factory=list, max_length=100)
    position: int = Field(default=0, strict=True, ge=0, le=100)
    code: str | None = Field(default=None, max_length=12000)

    @field_validator("code")
    @classmethod
    def bytes_limit(cls, value):
        if value is not None and len(value.encode()) > 16384:
            raise ValueError("Code exceeds 16 KiB UTF-8.")
        return value


@router.put("/exams/attempts/{attempt_id}/workspace")
def workspace(attempt_id: int, data: WorkspaceInput, user: Learner, db: DB):
    row = owned(attempt_id, user, db)
    require_active(row)
    ids = {q["id"] for q in visible_questions(row)}
    if len(set(data.flags)) != len(data.flags) or not set(data.flags) <= ids:
        raise HTTPException(422, "Flags must identify visible questions without duplicates.")
    if data.position >= max(1, len(ids)):
        raise HTTPException(422, "Question position is out of range.")
    if data.code is not None and row.definition_snapshot.get("mode") != "repair":
        raise HTTPException(422, "Only the practical exam accepts source code.")
    row.workspace = {
        **row.workspace,
        "flags": data.flags,
        "position": data.position,
        "saved_at": utcnow().isoformat(),
    }
    if data.code is not None:
        row.workspace = {**row.workspace, "code": data.code}
    return {"saved": True}


@router.post("/exams/attempts/{attempt_id}/advance")
def advance(attempt_id: int, user: Learner, db: DB):
    row = owned(attempt_id, user, db)
    require_active(row)
    exam = row.definition_snapshot
    if exam.get("mode") != "design":
        raise HTTPException(409, "This exam has no incident stages.")
    stage = row.workspace.get("stage", 0)
    if stage >= len(exam["stages"]) - 1:
        raise HTTPException(409, "All incident stages are already available.")
    complete(exam["stages"][stage]["questions"], row.answers)
    row.workspace = {
        **row.workspace,
        "stage": stage + 1,
        "position": len(visible_questions(row)),
        "commits": [*row.workspace.get("commits", []), {"stage": stage, "at": utcnow().isoformat()}],
    }
    # New position is the first question of the newly revealed stage.
    row.workspace = {
        **row.workspace,
        "position": sum(len(s["questions"]) for s in exam["stages"][: stage + 1]),
    }
    return {"advanced": True}


class RunInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_key: UUID


def public_run(row):
    return {
        "id": row.id,
        "code": row.code,
        "source_digest": sha256(row.code.encode()).hexdigest(),
        "result": row.result,
        "created_at": utc_timestamp(row.created_at),
    }


@router.get("/exams/attempts/{attempt_id}/runs")
def runs(attempt_id: int, user: Learner, db: DB):
    row = owned(attempt_id, user, db)
    if row.definition_snapshot.get("mode") != "repair":
        return []
    return [
        public_run(r)
        for r in db.scalars(select(ExamRun).where(ExamRun.attempt_id == row.id).order_by(ExamRun.id.desc()))
    ]


@router.post("/exams/attempts/{attempt_id}/runs", status_code=201)
def run(attempt_id: int, data: RunInput, user: Learner, db: DB):
    row = owned(attempt_id, user, db)
    # Idempotent replay remains readable after submission; never starts another job.
    existing = db.scalar(
        select(ExamRun).where(ExamRun.user_id == user.id, ExamRun.request_key == str(data.request_key))
    )
    code = row.workspace.get("code", "")
    if existing:
        if existing.attempt_id != row.id or existing.code != code:
            raise HTTPException(409, "Run key already belongs to different source or an attempt.")
        return public_run(existing)
    require_active(row)
    exam = row.definition_snapshot
    if exam.get("mode") != "repair" or not code.strip():
        raise HTTPException(422, "Save practical source before running checks.")
    count = len(
        list(
            db.scalars(
                select(ExamRun.id).where(
                    ExamRun.user_id == user.id, ExamRun.created_at >= utcnow() - timedelta(minutes=10)
                )
            )
        )
    )
    total = len(list(db.scalars(select(ExamRun.id).where(ExamRun.attempt_id == row.id))))
    if count >= 8 or total >= 64:
        raise HTTPException(429, "Limit: 8 runs per 10 minutes and 64 saved runs per practical attempt.")
    digest = sha256(json.dumps(exam["execution"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    result = runner_request(
        "/exam-run",
        {"exam_id": exam["id"], "version": exam["version"], "execution_digest": digest, "code": code},
    )
    result = safe_result(result, exam["execution"])
    run = ExamRun(
        user_id=user.id,
        attempt_id=row.id,
        request_key=str(data.request_key),
        code=code,
        definition_snapshot=deepcopy(exam["execution"]),
        result=result,
    )
    db.add(run)
    db.flush()
    return public_run(run)


def review_artifact(row, result, db):
    exam = row.definition_snapshot
    if not exam.get("review_project"):
        return result
    questions = visible_questions(row)

    def readable_answer(q):
        answer = row.answers.get(q["id"])
        if q.get("kind") == "short":
            return answer
        indices = answer if isinstance(answer, list) else [answer]
        return "; ".join(q["options"][i] for i in indices)

    evidence = {
        "attempt_id": row.id,
        "exam_id": exam["id"],
        "version": exam["version"],
        "responses": [
            {"id": q["id"], "prompt": q["prompt"], "answer": readable_answer(q)} for q in questions
        ],
        "source": row.workspace.get("code"),
        "objective": result.get("objective"),
    }
    # This generated attachment is immutable. It is never accepted as user input.
    latest = db.scalar(
        select(ProjectSubmission)
        .where(
            ProjectSubmission.user_id == row.user_id, ProjectSubmission.project_id == exam["review_project"]
        )
        .order_by(ProjectSubmission.revision.desc())
    )
    artifact = {
        "repository_url": "",
        "revision_ref": f"exam-attempt-{row.id}",
        "design_notes": "Fixed submitted exam responses are attached below. Review engineering reasoning using the frozen rubric.",
        "evidence": "The academy attached the actual submitted responses and any fixed isolated checks. No human judgment has been invented.",
        "test_status": "not-run",
        "test_command": "",
        "test_output": "",
        "change_summary": "",
        "exam_evidence": evidence,
    }
    review = ProjectSubmission(
        user_id=row.user_id,
        project_id=exam["review_project"],
        revision=latest.revision + 1 if latest else 1,
        parent_id=latest.id if latest else None,
        status="submitted",
        submitted_at=utcnow(),
        artifact=artifact,
        rubric_snapshot={
            "version": exam["version"],
            "project_title": exam["title"],
            "criteria": deepcopy(exam["rubric"]),
            "scale": deepcopy(rubric_content()["scale"]),
            "note": "Manual judgment only. Self-review is distinct from invited human review; neither certifies expertise.",
        },
    )
    db.add(review)
    db.flush()
    return {
        **result,
        "review_submission_id": review.id,
        "review_project": exam["review_project"],
        "review_note": "Awaiting self/human review. Open the fixed evidence workspace to invite a reviewer. No manual score is assumed.",
    }


def finish_nonknowledge(row, db):
    exam = row.definition_snapshot
    if exam["mode"] == "design":
        if row.workspace.get("stage", 0) != len(exam["stages"]) - 1:
            raise HTTPException(422, "Commit the baseline and address all incidents first.")
        complete(visible_questions(row), row.answers)
        result = {
            "mode": "design",
            "manual_count": len(visible_questions(row)),
            "score": None,
            "note": "Design and incident responses are saved. Senior engineering judgment requires rubric review.",
        }
    else:
        complete(exam["questions"], row.answers)
        code = row.workspace.get("code", "")
        last = db.scalar(
            select(ExamRun)
            .where(ExamRun.attempt_id == row.id, ExamRun.code == code)
            .order_by(ExamRun.id.desc())
        )
        if last is None:
            raise HTTPException(
                422,
                "Run isolated checks on the exact saved source before submitting. Failures may be submitted honestly.",
            )
        result = {
            "mode": "repair",
            "score": None,
            "manual_count": len(exam["questions"]),
            "run_id": last.id,
            "source_digest": sha256(code.encode()).hexdigest(),
            "objective": last.result,
            "note": "Finite executable contracts only. Architecture, Docker, performance and production behavior require separate review.",
        }
    return review_artifact(row, result, db)
