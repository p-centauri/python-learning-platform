"""Guided lesson activities. Exact choices, no learner-code execution or mastery writes."""

from copy import deepcopy
from datetime import timedelta, timezone
from functools import lru_cache
import json
import re
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from .auth import DB, Learner
from .config import settings
from .content import lesson_by_id, lessons
from .models import LessonCheckpointAttempt, utcnow

router = APIRouter(tags=["interactive lessons"])


@lru_cache
def interaction_content():
    return json.loads((settings.content_dir / "lesson-interactions.json").read_text())


def public_question(question):
    return {key: question[key] for key in ("id", "kind", "title", "prompt", "code", "options")}


def public_attempt(row):
    return {
        "id": row.id,
        "lesson_id": row.lesson_id,
        "checkpoint_id": row.checkpoint_id,
        "version": row.definition_snapshot["version"],
        "policy": row.definition_snapshot["policy"],
        "question": public_question(row.definition_snapshot["question"]),
        "answer": row.answer,
        "result": row.result,
        "created_at": row.created_at.replace(tzinfo=timezone.utc).isoformat(),
    }


def lesson_bundle(lesson_id):
    if lesson_by_id(lesson_id) is None or lesson_id not in interaction_content()["lessons"]:
        raise HTTPException(404, "Interactive lesson not found.")
    return interaction_content()["lessons"][lesson_id]


def glossary_entries():
    titles = {lesson["id"]: lesson["title"] for lesson in lessons()}
    return [
        {
            **{key: term[key] for key in ("id", "term", "definition")},
            "lessons": [{"id": key, "title": titles[key]} for key in term["lesson_ids"]],
        }
        for term in interaction_content()["glossary"]
    ]


@router.get("/glossary")
def glossary(user: Learner):
    return {"version": interaction_content()["version"], "terms": glossary_entries()}


@router.get("/lesson-activities/{lesson_id}")
def activities(lesson_id: str, user: Learner, db: DB):
    bundle = lesson_bundle(lesson_id)
    history = list(
        db.scalars(
            select(LessonCheckpointAttempt)
            .where(LessonCheckpointAttempt.user_id == user.id, LessonCheckpointAttempt.lesson_id == lesson_id)
            .order_by(LessonCheckpointAttempt.id.desc())
            .limit(50)
        )
    )
    return {
        "version": interaction_content()["version"],
        "note": interaction_content()["note"],
        "diagram": bundle["diagram"],
        "glossary": [t for t in glossary_entries() if t["id"] in bundle["glossary_ids"]],
        "checkpoints": [public_question(q) for q in bundle["checkpoints"]],
        "history": [public_attempt(row) for row in history],
        "history_limit": 50,
    }


class CheckInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: int = Field(strict=True, ge=0, le=5)
    version: str = Field(min_length=1, max_length=60, strict=True)
    request_key: UUID


@router.post("/lesson-activities/{lesson_id}/checkpoints/{checkpoint_id}/attempts", status_code=201)
def check(lesson_id: str, checkpoint_id: str, data: CheckInput, user: Learner, db: DB):
    existing = db.scalar(
        select(LessonCheckpointAttempt).where(
            LessonCheckpointAttempt.user_id == user.id,
            LessonCheckpointAttempt.request_key == str(data.request_key),
        )
    )
    if existing:
        if (
            existing.lesson_id != lesson_id
            or existing.checkpoint_id != checkpoint_id
            or existing.answer != data.answer
            or existing.definition_snapshot["version"] != data.version
        ):
            raise HTTPException(409, "This request key already belongs to a different answer.")
        return public_attempt(existing)
    bundle = lesson_bundle(lesson_id)
    question = next((q for q in bundle["checkpoints"] if q["id"] == checkpoint_id), None)
    if question is None:
        raise HTTPException(404, "Checkpoint not found in this lesson.")
    if data.version != interaction_content()["version"]:
        raise HTTPException(409, "This checkpoint changed. Reload the lesson before trying again.")
    if data.answer >= len(question["options"]):
        raise HTTPException(422, "Choose one of the available answers.")
    count = db.scalar(
        select(func.count())
        .select_from(LessonCheckpointAttempt)
        .where(LessonCheckpointAttempt.user_id == user.id)
    )
    recent = db.scalar(
        select(func.count())
        .select_from(LessonCheckpointAttempt)
        .where(
            LessonCheckpointAttempt.user_id == user.id,
            LessonCheckpointAttempt.created_at >= utcnow() - timedelta(minutes=10),
        )
    )
    if count >= 4000 or recent >= 40:
        raise HTTPException(429, "Checkpoint limit reached. Read saved feedback or return later.")
    row = LessonCheckpointAttempt(
        user_id=user.id,
        lesson_id=lesson_id,
        checkpoint_id=checkpoint_id,
        request_key=str(data.request_key),
        answer=data.answer,
        definition_snapshot={
            "version": interaction_content()["version"],
            "policy": interaction_content()["policy"],
            "question": deepcopy(question),
        },
        result={
            "correct": data.answer == question["answer"],
            "expected": question["options"][question["answer"]],
            "explanation": question["explanation"],
        },
    )
    db.add(row)
    db.flush()
    return public_attempt(row)


def sections_for(body):
    sections = []
    fence = None
    for line in body.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            if fence is None:
                fence = marker.group(1)[0]
            elif fence == marker.group(1)[0]:
                fence = None
            continue
        if fence is None and line.startswith("## "):
            title = re.sub(r"[`*_]", "", line[3:].strip())
            sections.append({"id": f"lesson-section-{len(sections) + 1}", "title": title})
    return sections


def navigation_for(lesson):
    route = [item for item in lessons() if item["track_id"] == lesson["track_id"]]
    index = next(i for i, item in enumerate(route) if item["id"] == lesson["id"])

    def link(item):
        return {"id": item["id"], "title": item["title"]}

    return {
        "previous": link(route[index - 1]) if index else None,
        "next": link(route[index + 1]) if index + 1 < len(route) else None,
        "prerequisites": [link(lesson_by_id(key)) for key in lesson["prerequisites"]],
    }
