"""Persist learner source and call the separate authenticated runner over HTTP."""

from copy import deepcopy
from datetime import timedelta
from functools import lru_cache
import json
from uuid import UUID
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from .auth import DB, Learner
from .config import settings
from .models import CodingAttempt, CodingDraft, utcnow
from .projects import utc_timestamp

router = APIRouter(tags=["coding practice"])


@lru_cache
def coding_content():
    return json.loads((settings.content_dir / "coding-exercises.json").read_text())


def require_exercise(exercise_id):
    exercise = next((e for e in coding_content()["exercises"] if e["id"] == exercise_id), None)
    if exercise is None:
        raise HTTPException(404, "Coding exercise not found.")
    return exercise


def public_definition(exercise):
    return {
        **{key: exercise[key] for key in ("id", "title", "language", "prompt", "starter", "lesson_id")},
        "schema": exercise.get("schema"),
        "examples": [
            {key: value for key, value in test.items() if key != "public"}
            for test in exercise["tests"]
            if test["public"]
        ],
        "check_count": len(exercise["tests"]),
    }


def runner_request(path, payload=None):
    if not settings.runner_url or len(settings.runner_token) < 32:
        raise HTTPException(503, "The isolated runner is not configured. Your draft can still be saved.")
    try:
        response = httpx.request(
            "GET" if payload is None else "POST",
            settings.runner_url.rstrip("/") + path,
            json=payload,
            headers={"X-Runner-Token": settings.runner_token},
            timeout=60,
            trust_env=False,
        )
    except httpx.HTTPError as error:
        raise HTTPException(
            503, "The isolated runner is unavailable. Your draft is safe; retry when it is ready."
        ) from error
    try:
        body = response.json()
        if not isinstance(body, dict):
            raise ValueError()
    except ValueError as error:
        raise HTTPException(503, "The runner returned an invalid response. No grade was recorded.") from error
    if response.status_code != 200:
        detail = str(body.get("detail", "The isolated runner is unavailable."))[:600]
        raise HTTPException(response.status_code if response.status_code in {409, 429} else 503, detail)
    return body


def safe_result(result, definition):
    """Validate evidence and redact private feedback again at the API boundary."""
    tests = definition["tests"]
    checks = result.get("checks") if isinstance(result, dict) else None
    if not isinstance(checks, list) or not 1 <= len(checks) <= len(tests):
        raise HTTPException(503, "The runner returned an invalid result. No grade was recorded.")
    cleaned = []
    for index, check in enumerate(checks):
        if not isinstance(check, dict) or check.get("status") not in {
            "passed",
            "failed",
            "error",
            "timeout",
            "output-limit",
        }:
            raise HTTPException(503, "The runner returned an invalid result. No grade was recorded.")
        public = tests[index]["public"]
        cleaned.append(
            {
                "name": tests[index]["name"] if public else f"Additional check {index + 1}",
                "public": public,
                "status": check["status"],
                "actual": check.get("actual") if public else None,
                "message": str(check.get("message", ""))[:600] if public else "",
            }
        )
    passed = sum(c["status"] == "passed" for c in cleaned)
    status = "passed" if passed == len(tests) else "failed"
    if (
        result.get("status") != status
        or type(result.get("passed")) is not int
        or type(result.get("total")) is not int
        or result.get("passed") != passed
        or result.get("total") != len(tests)
        or type(result.get("duration_ms")) is not int
        or not 0 <= result["duration_ms"] <= 60000
        or not isinstance(result.get("profile"), str)
        or len(result["profile"]) > 60
    ):
        raise HTTPException(503, "The runner returned an invalid result. No grade was recorded.")
    return {
        "status": status,
        "passed": passed,
        "total": len(tests),
        "checks": cleaned,
        "duration_ms": result.get("duration_ms", 0),
        "profile": result.get("profile", "unknown"),
        "note": coding_content()["note"],
    }


def runner_status():
    try:
        health = runner_request("/health")
        verification = health.get("verification") or {}
        if not isinstance(verification, dict):
            raise HTTPException(503, "The runner returned an invalid health response.")
        ready = health.get("ready") is True and health.get("version") == coding_content()["version"]
        return {
            "ready": bool(ready),
            "message": "Isolation verified. Ready to run."
            if ready
            else "The runner is verifying isolation or needs a content restart. Draft saving remains available.",
            "profile": verification.get("profile"),
        }
    except HTTPException as error:
        return {"ready": False, "message": error.detail, "profile": None}


def public_attempt(attempt):
    return {
        "id": attempt.id,
        "exercise_id": attempt.exercise_id,
        "code": attempt.code,
        "version": attempt.definition_snapshot["version"],
        "result": attempt.result,
        "created_at": utc_timestamp(attempt.created_at),
    }


@router.get("/coding")
def index(user: Learner, db: DB):
    attempts = list(db.scalars(select(CodingAttempt).where(CodingAttempt.user_id == user.id)))
    return {
        "version": coding_content()["version"],
        "note": coding_content()["note"],
        "runner": runner_status(),
        "exercises": [
            {
                **public_definition(e),
                "attempt_count": sum(a.exercise_id == e["id"] for a in attempts),
                "passed": any(a.exercise_id == e["id"] and a.result["status"] == "passed" for a in attempts),
            }
            for e in coding_content()["exercises"]
        ],
    }


@router.get("/coding/{exercise_id}")
def detail(exercise_id: str, user: Learner, db: DB):
    definition = require_exercise(exercise_id)
    draft = db.scalar(
        select(CodingDraft).where(CodingDraft.user_id == user.id, CodingDraft.exercise_id == exercise_id)
    )
    attempts = db.scalars(
        select(CodingAttempt)
        .where(CodingAttempt.user_id == user.id, CodingAttempt.exercise_id == exercise_id)
        .order_by(CodingAttempt.id.desc())
        .limit(50)
    )
    return {
        **public_definition(definition),
        "version": coding_content()["version"],
        "note": coding_content()["note"],
        "code": draft.code if draft else definition["starter"],
        "draft_saved": draft is not None,
        "runner": runner_status(),
        "attempts": [public_attempt(a) for a in attempts],
        "limits": {"runs": 8, "window_minutes": 10, "code_bytes": 16384, "job_seconds": 45},
    }


class SourceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(max_length=12000)

    @field_validator("code")
    @classmethod
    def code_size(cls, value):
        if len(value.encode()) > 16384:
            raise ValueError("Code exceeds the 16 KiB UTF-8 limit.")
        return value


def save_source(user, db, exercise_id, code):
    draft = db.scalar(
        select(CodingDraft).where(CodingDraft.user_id == user.id, CodingDraft.exercise_id == exercise_id)
    )
    if draft is None:
        db.add(CodingDraft(user_id=user.id, exercise_id=exercise_id, code=code))
    else:
        draft.code = code


@router.put("/coding/{exercise_id}/draft")
def draft(exercise_id: str, data: SourceInput, user: Learner, db: DB):
    require_exercise(exercise_id)
    save_source(user, db, exercise_id, data.code)
    return {"saved": True}


class RunInput(SourceInput):
    request_key: UUID
    version: str = Field(max_length=60)


@router.post("/coding/{exercise_id}/attempts", status_code=201)
def run(exercise_id: str, data: RunInput, user: Learner, db: DB):
    existing = db.scalar(
        select(CodingAttempt).where(
            CodingAttempt.user_id == user.id, CodingAttempt.request_key == str(data.request_key)
        )
    )
    if existing:
        if existing.exercise_id != exercise_id or existing.code != data.code:
            raise HTTPException(409, "This run request was already used for different code.")
        return public_attempt(existing)
    definition = require_exercise(exercise_id)
    if data.version != coding_content()["version"]:
        raise HTTPException(409, "Exercise content changed. Save your draft, then reload before running.")
    if not data.code.strip():
        raise HTTPException(422, "Write some code before running the checks.")
    recent = list(
        db.scalars(
            select(CodingAttempt.id).where(
                CodingAttempt.user_id == user.id, CodingAttempt.created_at >= utcnow() - timedelta(minutes=10)
            )
        )
    )
    if len(recent) >= 8:
        raise HTTPException(
            429, "You have used 8 runs in 10 minutes. Save your code and retry after the window clears."
        )
    # Only the runner gets source for execution. The API never invokes an interpreter.
    result = runner_request("/run", {"exercise_id": exercise_id, "version": data.version, "code": data.code})
    result = safe_result(result, definition)
    save_source(user, db, exercise_id, data.code)
    attempt = CodingAttempt(
        user_id=user.id,
        exercise_id=exercise_id,
        request_key=str(data.request_key),
        code=data.code,
        definition_snapshot={"version": data.version, "exercise": deepcopy(definition)},
        result=result,
    )
    db.add(attempt)
    db.flush()
    return public_attempt(attempt)
