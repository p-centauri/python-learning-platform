"""Account-scoped artifact versions and attributable manual review. No execution."""

from copy import deepcopy
from datetime import timezone
from functools import lru_cache
import json
from typing import Literal
from urllib.parse import urlsplit
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import select
from .auth import DB, Learner
from .config import settings
from .content import catalog
from .models import ProjectSubmission, ProjectFeedback, ProjectReviewAssignment, User, utcnow

router = APIRouter(tags=["project submissions"])


@lru_cache
def rubric_content():
    return json.loads((settings.content_dir / "project-rubrics.json").read_text())


def project_definition(project_id):
    project = next((p for p in catalog()["projects"] if p["id"] == project_id), None)
    if project is None:
        raise HTTPException(404, "Project not found.")
    return project


def rubric_for(project_id):
    content = rubric_content()
    return deepcopy(
        {
            "version": content["version"],
            "project_title": project_definition(project_id)["title"],
            "criteria": content["projects"][project_id],
            "scale": content["scale"],
            "note": content["note"],
        }
    )


def find_submission(submission_id, db, lock=False):
    query = select(ProjectSubmission).where(ProjectSubmission.id == submission_id)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(404, "Submission not found.")
    return row


def owned(submission_id, user, db, lock=False):
    row = find_submission(submission_id, db, lock)
    if row.user_id != user.id:
        raise HTTPException(404, "Submission not found.")
    return row


def can_review(row, user, db):
    return (
        row.status == "submitted"
        and db.scalar(
            select(ProjectReviewAssignment.id).where(
                ProjectReviewAssignment.submission_id == row.id,
                ProjectReviewAssignment.email == user.email,
                ProjectReviewAssignment.active.is_(True),
            )
        )
        is not None
    )


def public_submission(row, user, db):
    feedback = list(
        db.scalars(
            select(ProjectFeedback)
            .where(ProjectFeedback.submission_id == row.id)
            .order_by(ProjectFeedback.id)
        )
    )
    owner = db.get(User, row.user_id)
    return {
        "id": row.id,
        "project_id": row.project_id,
        "revision": row.revision,
        "parent_id": row.parent_id,
        "status": row.status,
        "artifact": row.artifact,
        "rubric": row.rubric_snapshot,
        "created_at": utc_timestamp(row.created_at),
        "updated_at": utc_timestamp(row.updated_at),
        "submitted_at": utc_timestamp(row.submitted_at),
        "owner_name": owner.name,
        "is_owner": row.user_id == user.id,
        "can_review": row.status == "submitted" and not any(f.reviewer_id == user.id for f in feedback),
        "feedback": [
            {
                "id": f.id,
                "kind": f.kind,
                "reviewer_name": db.get(User, f.reviewer_id).name,
                "ratings": f.ratings,
                "summary": f.summary,
                "next_steps": f.next_steps,
                "outcome": "meets-rubric"
                if all(r["score"] >= 2 for r in f.ratings.values())
                else "changes-requested",
                "created_at": utc_timestamp(f.created_at),
            }
            for f in feedback
        ],
        "assignments": [
            {"id": a.id, "email": a.email, "active": a.active}
            for a in db.scalars(
                select(ProjectReviewAssignment)
                .where(ProjectReviewAssignment.submission_id == row.id)
                .order_by(ProjectReviewAssignment.id)
            )
        ]
        if row.user_id == user.id
        else [],
    }


def utc_timestamp(value):
    # SQLite reads timezone columns as naive values. Keep API timestamps stable.
    if value is None:
        return None
    return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ArtifactInput(StrictInput):
    repository_url: str = Field(default="", max_length=2000)
    revision_ref: str = Field(default="", max_length=120)
    design_notes: str = Field(default="", max_length=12000)
    evidence: str = Field(default="", max_length=12000)
    test_status: Literal["not-run", "passed", "failed"] = "not-run"
    test_command: str = Field(default="", max_length=500)
    test_output: str = Field(default="", max_length=20000)
    change_summary: str = Field(default="", max_length=6000)

    @field_validator("repository_url")
    @classmethod
    def safe_link(cls, value):
        if value:
            try:
                parts = urlsplit(value)
                valid = (
                    parts.scheme == "https" and parts.hostname and not parts.username and not parts.password
                )
                parts.port  # Also reject malformed ports.
            except ValueError:
                valid = False
            if not valid or any(c.isspace() or ord(c) < 32 for c in value):
                raise ValueError("Use a full HTTPS repository URL without credentials.")
        return value


@router.get("/projects/{project_id}/submissions")
def history(project_id: str, user: Learner, db: DB):
    project = project_definition(project_id)
    rows = db.scalars(
        select(ProjectSubmission)
        .where(ProjectSubmission.user_id == user.id, ProjectSubmission.project_id == project_id)
        .order_by(ProjectSubmission.revision.desc())
    )
    return {
        "project": project,
        "rubric": rubric_for(project_id),
        "submissions": [public_submission(row, user, db) for row in rows],
    }


@router.post("/projects/{project_id}/submissions", status_code=201)
def start_draft(project_id: str, user: Learner, db: DB):
    project_definition(project_id)
    latest = db.scalar(
        select(ProjectSubmission)
        .where(ProjectSubmission.user_id == user.id, ProjectSubmission.project_id == project_id)
        .order_by(ProjectSubmission.revision.desc())
    )
    if latest and latest.status == "draft":
        return public_submission(latest, user, db)
    if latest and latest.revision >= 50:
        raise HTTPException(409, "This project has reached the 50-version local history limit.")
    row = ProjectSubmission(
        user_id=user.id,
        project_id=project_id,
        revision=latest.revision + 1 if latest else 1,
        parent_id=latest.id if latest else None,
        rubric_snapshot=rubric_for(project_id),
        artifact={
            **{k: v for k, v in latest.artifact.items() if k in ArtifactInput.model_fields},
            "change_summary": "",
        }
        if latest
        else ArtifactInput().model_dump(),
    )
    db.add(row)
    db.flush()
    return public_submission(row, user, db)


@router.get("/project-submissions/{submission_id}")
def detail(submission_id: int, user: Learner, db: DB):
    row = find_submission(submission_id, db)
    if row.user_id != user.id and not can_review(row, user, db):
        raise HTTPException(404, "Submission not found.")
    return public_submission(row, user, db)


@router.put("/project-submissions/{submission_id}")
def save_draft(submission_id: int, data: ArtifactInput, user: Learner, db: DB):
    row = owned(submission_id, user, db, lock=True)
    if row.status != "draft":
        raise HTTPException(409, "Submitted versions are fixed. Start a new revision to make changes.")
    row.artifact = data.model_dump()
    db.flush()
    return public_submission(row, user, db)


@router.delete("/project-submissions/{submission_id}", status_code=204)
def discard_draft(submission_id: int, user: Learner, db: DB):
    row = owned(submission_id, user, db, lock=True)
    if row.status != "draft":
        raise HTTPException(409, "Submitted versions cannot be discarded.")
    db.delete(row)


@router.post("/project-submissions/{submission_id}/submit")
def submit(submission_id: int, user: Learner, db: DB):
    row = owned(submission_id, user, db, lock=True)
    if row.status == "submitted":
        return public_submission(row, user, db)
    artifact = ArtifactInput.model_validate(row.artifact)
    if (
        not artifact.repository_url
        or not artifact.revision_ref
        or len(artifact.design_notes) < 30
        or len(artifact.evidence) < 30
    ):
        raise HTTPException(
            422,
            "Add a repository URL, revision reference, and at least 30 characters each of design notes and implementation evidence.",
        )
    if artifact.test_status != "not-run" and (
        len(artifact.test_command) < 3 or len(artifact.test_output) < 10
    ):
        raise HTTPException(422, "Reported test results need the command and its output.")
    if row.parent_id and len(artifact.change_summary) < 20:
        raise HTTPException(422, "Explain the revision and feedback addressed in at least 20 characters.")
    row.status, row.submitted_at = "submitted", utcnow()
    db.flush()
    return public_submission(row, user, db)


class AssignmentInput(StrictInput):
    email: EmailStr


@router.post("/project-submissions/{submission_id}/reviewers")
def invite(submission_id: int, data: AssignmentInput, user: Learner, db: DB):
    row = owned(submission_id, user, db, lock=True)
    if row.status != "submitted":
        raise HTTPException(409, "Submit this version before inviting a reviewer.")
    email = str(data.email).lower()
    if email == user.email:
        raise HTTPException(
            422, "Use self-review for your own work. Invite a different account for human review."
        )
    if db.scalar(select(User.id).where(User.email == email)) is None:
        raise HTTPException(
            422, "Ask the reviewer to create an academy account first, then confirm their account email."
        )
    assignments = list(
        db.scalars(select(ProjectReviewAssignment).where(ProjectReviewAssignment.submission_id == row.id))
    )
    assignment = next((a for a in assignments if a.email == email), None)
    if assignment:
        assignment.active = True
    elif len(assignments) < 10:
        db.add(ProjectReviewAssignment(submission_id=row.id, email=email))
    else:
        raise HTTPException(409, "A submitted version supports up to 10 reviewer accounts.")
    db.flush()
    return public_submission(row, user, db)


@router.delete("/project-submissions/{submission_id}/reviewers/{assignment_id}")
def revoke(submission_id: int, assignment_id: int, user: Learner, db: DB):
    row = owned(submission_id, user, db, lock=True)
    assignment = db.scalar(
        select(ProjectReviewAssignment).where(
            ProjectReviewAssignment.id == assignment_id, ProjectReviewAssignment.submission_id == row.id
        )
    )
    if assignment is None:
        raise HTTPException(404, "Reviewer invitation not found.")
    assignment.active = False
    db.flush()
    return public_submission(row, user, db)


@router.get("/project-reviews")
def inbox(user: Learner, db: DB):
    rows = db.scalars(
        select(ProjectSubmission)
        .join(ProjectReviewAssignment)
        .where(
            ProjectReviewAssignment.email == user.email,
            ProjectReviewAssignment.active.is_(True),
            ProjectSubmission.status == "submitted",
        )
        .order_by(ProjectSubmission.submitted_at.desc())
    )
    return [
        {
            "id": row.id,
            "revision": row.revision,
            "title": row.rubric_snapshot["project_title"],
            "owner_name": db.get(User, row.user_id).name,
            "submitted_at": utc_timestamp(row.submitted_at),
            "reviewed": db.scalar(
                select(ProjectFeedback.id).where(
                    ProjectFeedback.submission_id == row.id, ProjectFeedback.reviewer_id == user.id
                )
            )
            is not None,
        }
        for row in rows
    ]


class Rating(StrictInput):
    score: int = Field(strict=True, ge=0, le=3)
    evidence: str = Field(min_length=10, max_length=2000)


class FeedbackInput(StrictInput):
    ratings: dict[str, Rating] = Field(min_length=1, max_length=20)
    summary: str = Field(min_length=20, max_length=6000)
    next_steps: str = Field(min_length=20, max_length=6000)


@router.post("/project-submissions/{submission_id}/feedback", status_code=201)
def review(submission_id: int, data: FeedbackInput, user: Learner, db: DB):
    row = find_submission(submission_id, db, lock=True)
    if row.user_id != user.id and not can_review(row, user, db):
        raise HTTPException(404, "Submission not found.")
    if row.status != "submitted":
        raise HTTPException(409, "Submit this version before reviewing it.")
    if set(data.ratings) != {c["id"] for c in row.rubric_snapshot["criteria"]}:
        raise HTTPException(422, "Rate every criterion in this version's rubric, without extra criteria.")
    existing = db.scalar(
        select(ProjectFeedback).where(
            ProjectFeedback.submission_id == row.id, ProjectFeedback.reviewer_id == user.id
        )
    )
    payload = data.model_dump()
    if existing:
        if all(getattr(existing, key) == value for key, value in payload.items()):
            return public_submission(row, user, db)
        raise HTTPException(
            409,
            "Feedback is already recorded for this version. Review a new revision to record updated judgment.",
        )
    db.add(
        ProjectFeedback(
            submission_id=row.id,
            reviewer_id=user.id,
            kind="self" if row.user_id == user.id else "human",
            **payload,
        )
    )
    db.flush()
    return public_submission(row, user, db)
