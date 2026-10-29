"""An allowlisted account export, not a raw database dump or an import endpoint."""

from datetime import datetime
import json
import re
from typing import Literal
from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from sqlalchemy import select
from .auth import DB, Learner, COOKIE, token_digest
from .content import catalog
from .models import (
    User,
    LoginSession,
    LessonProgress,
    LearningPreferences,
    Bookmark,
    Note,
    ExerciseState,
    ExerciseAttempt,
    ReviewItem,
    ProjectProgress,
    ProjectSubmission,
    ExamAttempt,
    ExamRun,
    CodingDraft,
    CodingAttempt,
    RecallSession,
    LessonCheckpointAttempt,
    utcnow,
)
from .assessments import public_attempt as exam_public
from .comprehensive import public_run
from .coding import public_attempt as coding_public
from .interactivity import public_attempt as guided_public
from .retention import public_session
from .projects import public_submission

router = APIRouter(tags=["private evidence export"])


def rows(db, cls, user):
    return list(db.scalars(select(cls).where(cls.user_id == user.id)))


def fields(items, names):
    return [{name: getattr(item, name) for name in names} for item in items]


def account_export(user, db, request):
    # Serialize account-owned writes and target-project feedback while collecting evidence.
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    valid = db.scalar(
        select(LoginSession).where(
            LoginSession.token_hash == token_digest(request.cookies[COOKIE]),
            LoginSession.user_id == user.id,
            LoginSession.expires_at > utcnow(),
        )
    )
    if valid is None:
        raise HTTPException(401, "Sign in to export your evidence.")
    submissions = list(
        db.scalars(
            select(ProjectSubmission)
            .where(ProjectSubmission.user_id == user.id)
            .order_by(ProjectSubmission.id)
            .with_for_update()
        )
    )
    preferences = db.get(LearningPreferences, user.id)
    return jsonable_encoder(
        {
            "format": "academy-evidence-v1",
            "captured_at": utcnow(),
            "catalog_version": catalog()["version"],
            "scope": "Your learning evidence, drafts, notes and owned review artifacts. Active answer keys, private definitions, credentials and sessions are excluded. This file is not a database restore/import.",
            "account": {"id": user.id, "name": user.name, "email": user.email, "created_at": user.created_at},
            "preferences": fields([preferences], ["goal", "weekly_hours", "starting_mode", "updated_at"])[0]
            if preferences
            else None,
            "reading": fields(rows(db, LessonProgress, user), ["lesson_id", "completed_at"]),
            "bookmarks": fields(rows(db, Bookmark, user), ["lesson_id"]),
            "notes": fields(rows(db, Note, user), ["lesson_id", "body", "updated_at"]),
            "scenario_state": fields(
                rows(db, ExerciseState, user), ["exercise_id", "hints_used", "revealed"]
            ),
            "scenario_attempts": fields(
                rows(db, ExerciseAttempt, user),
                [
                    "id",
                    "lesson_id",
                    "exercise_id",
                    "answer",
                    "score",
                    "hints_used",
                    "revealed",
                    "is_review",
                    "created_at",
                ],
            ),
            "review_schedule": fields(
                rows(db, ReviewItem, user), ["exercise_id", "due_at", "interval_days", "repetitions"]
            ),
            "project_checklist": fields(
                rows(db, ProjectProgress, user), ["project_id", "task_id", "completed_at"]
            ),
            "project_submissions": [public_submission(s, user, db) for s in submissions],
            "exams": [exam_public(s) for s in rows(db, ExamAttempt, user)],
            "exam_runs": [public_run(s) for s in rows(db, ExamRun, user)],
            "coding_drafts": fields(rows(db, CodingDraft, user), ["exercise_id", "code", "updated_at"]),
            "coding_runs": [coding_public(s) for s in rows(db, CodingAttempt, user)],
            "recall_checks": [public_session(s) for s in rows(db, RecallSession, user)],
            "guided_checks": [guided_public(s) for s in rows(db, LessonCheckpointAttempt, user)],
        }
    )


def markdown(data):
    lines = [
        "# Forge — personal evidence",
        "",
        f"Captured: {data['captured_at']}",
        f"Catalog: {data['catalog_version']}",
        "",
        data["scope"],
        "",
        "Reading, checklist completion, objective checks and self/human judgments remain separate evidence. No expertise certification is inferred.",
        "",
    ]
    for key, value in data.items():
        if key in {"format", "captured_at", "catalog_version", "scope"}:
            continue
        title = key.replace("_", " ").title()
        lines += [f"## {title}", ""]
        if value == [] or value is None:
            lines += ["No saved records.", ""]
            continue
        text = json.dumps(value, ensure_ascii=False, indent=2)
        # Long enough fences keep learner text literal even if it contains Markdown/HTML.
        fence = "`" * (max((len(part) for part in re.findall(r"`+", text)), default=2) + 1)
        fence = "`" * max(3, len(fence))
        lines += [fence + "json", text, fence, ""]
    return "\n".join(lines) + "\n"


@router.get("/account/export")
def download(user: Learner, db: DB, request: Request, format: Literal["json", "markdown"] = "json"):
    data = account_export(user, db, request)
    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n" if format == "json" else markdown(data)
    extension = "json" if format == "json" else "md"
    return Response(
        body,
        media_type="application/json" if format == "json" else "text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="academy-evidence-{datetime.now().date()}.{extension}"',
            "Cache-Control": "no-store",
        },
    )
