"""Mistake-focused recall. Exact short answers; no learner code interpretation."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import json
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func
from .auth import DB, Learner
from .config import settings
from .content import exercise_by_id
from .models import ExerciseAttempt, RecallSession, LessonCheckpointAttempt, utcnow

router = APIRouter(tags=["recall and retention"])


@lru_cache
def review_content():
    return json.loads((settings.content_dir / "review-questions.json").read_text())


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def normalize(value, case_sensitive=False):
    cleaned = value.strip()
    return cleaned if case_sensitive else cleaned.casefold()


def require_topic(concept_id):
    topic = next((c for c in review_content()["concepts"] if c["id"] == concept_id), None)
    if topic is None:
        raise HTTPException(404, "Review topic not found.")
    return topic


def history_for(db, user_id):
    source = list(
        db.scalars(
            select(ExerciseAttempt).where(ExerciseAttempt.user_id == user_id).order_by(ExerciseAttempt.id)
        )
    )
    sessions = list(
        db.scalars(select(RecallSession).where(RecallSession.user_id == user_id).order_by(RecallSession.id))
    )
    return source, sessions


def guided_exposures_for(db, user_id):
    return dict(
        db.execute(
            select(LessonCheckpointAttempt.lesson_id, func.max(LessonCheckpointAttempt.created_at))
            .where(LessonCheckpointAttempt.user_id == user_id)
            .group_by(LessonCheckpointAttempt.lesson_id)
        ).all()
    )


def topic_state(topic, source, sessions, now, guided_exposures=None):
    source = [a for a in source if a.exercise_id in topic["sources"]]
    sessions = [s for s in sessions if s.concept_id == topic["id"]]
    submitted = [s for s in sessions if s.status == "submitted"]
    missed = [a for a in source if a.score == 0]
    failed_checks = [s for s in submitted if not s.result["correct"]]
    events = [utc(a.created_at) for a in source] + [utc(s.submitted_at or s.created_at) for s in sessions]
    guided = (guided_exposures or {}).get(topic["lesson_id"])
    if guided:
        events.append(utc(guided))
    initial = min((utc(a.created_at) + timedelta(days=3 if a.score else 1) for a in source), default=None)
    if initial is None and sessions:
        initial = min(utc(s.created_at) for s in sessions) + timedelta(days=1)
    if initial is None and guided:
        initial = utc(guided) + timedelta(days=1)
    delayed = [s for s in submitted if s.mode == "delayed"]
    latest = delayed[-1] if delayed else None
    due = datetime.fromisoformat(latest.result["next_due_at"]) if latest else initial
    interval = latest.result["interval_days"] if latest else 1
    if due:
        # A newly observed mistake brings an extended schedule forward.
        recent_misses = [
            utc(a.created_at) + timedelta(days=1)
            for a in missed
            if not latest or utc(a.created_at) > utc(latest.submitted_at)
        ]
        recent_misses += [
            utc(s.submitted_at) + timedelta(days=1) for s in failed_checks if not latest or s.id > latest.id
        ]
        if recent_misses:
            due = min(due, *recent_misses)
            interval = 1
        # A delayed check needs at least a day since the last recorded topic exposure.
        if events:
            due = max(due, max(events) + timedelta(days=1))

    def evidence(kind):
        rows = [s for s in submitted if s.result["evidence_kind"] == kind]
        return {"correct": sum(s.result["correct"] for s in rows), "total": len(rows)}

    seen = {s.question_id for s in sessions}
    active = next((s for s in sessions if s.status == "active"), None)
    misses = len(missed) + len(failed_checks)
    missed_times = [utc(a.created_at) for a in missed] + [utc(s.submitted_at) for s in failed_checks]
    return {
        "id": topic["id"],
        "title": topic["title"],
        "lesson_id": topic["lesson_id"],
        "skill": topic["skill"],
        "source_incorrect": len(missed),
        "check_incorrect": len(failed_checks),
        "incorrect": misses,
        "source_questions_missed": len({a.exercise_id for a in missed}),
        "recurring": misses >= 2,
        "last_incorrect_at": max(missed_times).isoformat() if missed_times else None,
        "source_recognition": {"correct": sum(a.score == 100 for a in source), "total": len(source)},
        "fresh_delayed": evidence("fresh-delayed"),
        "immediate": evidence("immediate"),
        "repeated_delayed": evidence("repeated-delayed"),
        "assisted": evidence("assisted"),
        "due_at": due.isoformat() if due else None,
        "due": bool(due and due <= now),
        "interval_days": interval,
        "active_id": active.id if active else None,
        "unseen_questions": sum(q["id"] not in seen for q in topic["questions"]),
        "question_count": len(topic["questions"]),
        "started": bool(source or sessions or guided),
    }


def overview_for(db, user_id):
    source, sessions = history_for(db, user_id)
    guided = guided_exposures_for(db, user_id)
    states = [topic_state(t, source, sessions, utcnow(), guided) for t in review_content()["concepts"]]
    topics = sorted(
        [t for t in states if t["started"]],
        key=lambda t: (
            not bool(t["active_id"]),
            not t["due"],
            not t["recurring"],
            -t["incorrect"],
            t["due_at"] or "",
            t["id"],
        ),
    )
    return {
        "version": review_content()["version"],
        "policy": review_content()["policy"],
        "note": review_content()["note"],
        "topics": topics,
        "catalog": [{k: t[k] for k in ("id", "title", "skill", "question_count")} for t in states],
        "summary": {
            "due": sum(t["due"] for t in states),
            "recurring": sum(t["recurring"] for t in states),
            **{
                kind: {key: sum(t[kind][key] for t in states) for key in ("correct", "total")}
                for kind in (
                    "source_recognition",
                    "fresh_delayed",
                    "immediate",
                    "repeated_delayed",
                    "assisted",
                )
            },
        },
    }


def public_session(session):
    snapshot = session.definition_snapshot
    question = snapshot["question"]
    return {
        "id": session.id,
        "concept_id": session.concept_id,
        "title": snapshot["title"],
        "version": snapshot["version"],
        "policy": snapshot["policy"],
        "status": session.status,
        "mode": session.mode,
        "fresh": snapshot["fresh"],
        "question": {
            key: question[key]
            for key in ("id", "prompt", "code", "format", "case_sensitive")
            if key in question
        },
        "answer": session.answer,
        "used_help": session.used_help,
        "result": session.result,
        "created_at": utc(session.created_at).isoformat(),
        "submitted_at": utc(session.submitted_at).isoformat() if session.submitted_at else None,
    }


def owned_session(session_id, user, db):
    row = db.scalar(
        select(RecallSession)
        .where(RecallSession.id == session_id, RecallSession.user_id == user.id)
        .with_for_update()
    )
    if row is None:
        raise HTTPException(404, "Review session not found.")
    return row


@router.get("/recall")
def overview(user: Learner, db: DB):
    return overview_for(db, user.id)


@router.get("/recall/topics/{concept_id}")
def detail(concept_id: str, user: Learner, db: DB):
    topic = require_topic(concept_id)
    source, sessions = history_for(db, user.id)
    owned = [s for s in sessions if s.concept_id == concept_id]
    return {
        "topic": topic_state(topic, source, sessions, utcnow(), guided_exposures_for(db, user.id)),
        "note": review_content()["note"],
        "sources": [
            {"id": key, "title": exercise_by_id(key)[1]["title"], "href": f"/practice/{key}"}
            for key in topic["sources"]
        ],
        "active": next((public_session(s) for s in owned if s.status == "active"), None),
        "history": [public_session(s) for s in owned[::-1] if s.status != "active"][:50],
    }


class BeginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["practice", "delayed"]


@router.post("/recall/topics/{concept_id}/sessions", status_code=201)
def begin(concept_id: str, data: BeginInput, user: Learner, db: DB):
    topic = require_topic(concept_id)
    source, sessions = history_for(db, user.id)
    active = next((s for s in sessions if s.concept_id == concept_id and s.status == "active"), None)
    if active:
        return public_session(active)
    now = utcnow()
    state = topic_state(topic, source, sessions, now, guided_exposures_for(db, user.id))
    if data.mode == "delayed" and not state["due"]:
        raise HTTPException(
            409, "A delayed check is not due yet. Practise now or return at the scheduled time."
        )
    if len(sessions) >= 2000 or sum(utc(s.created_at) >= now - timedelta(minutes=10) for s in sessions) >= 20:
        raise HTTPException(429, "Review start limit reached. Resume an existing check or return later.")
    seen = {s.question_id for s in sessions}
    question = next((q for q in topic["questions"] if q["id"] not in seen), None)
    fresh = question is not None
    if question is None:
        last_seen = {s.question_id: s.id for s in sessions}
        question = min(topic["questions"], key=lambda q: last_seen.get(q["id"], 0))
    row = RecallSession(
        user_id=user.id,
        concept_id=concept_id,
        active_key=concept_id,
        question_id=question["id"],
        mode=data.mode,
        created_at=now,
        updated_at=now,
        definition_snapshot={
            "version": review_content()["version"],
            "policy": review_content()["policy"],
            "title": topic["title"],
            "sources": list(topic["sources"]),
            "fresh": fresh,
            "interval_days": state["interval_days"],
            "question": deepcopy(question),
        },
    )
    db.add(row)
    db.flush()
    return public_session(row)


class AnswerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(max_length=120, strict=True)
    used_help: bool = Field(strict=True)


@router.get("/recall/sessions/{session_id}")
def get_session(session_id: int, user: Learner, db: DB):
    return public_session(owned_session(session_id, user, db))


@router.put("/recall/sessions/{session_id}")
def save(session_id: int, data: AnswerInput, user: Learner, db: DB):
    row = owned_session(session_id, user, db)
    if row.status != "active":
        raise HTTPException(409, "A finished review cannot be edited. Start another check.")
    row.answer, row.used_help = data.answer, data.used_help
    row.updated_at = utcnow()
    return public_session(row)


@router.post("/recall/sessions/{session_id}/submit")
def submit(session_id: int, data: AnswerInput, user: Learner, db: DB):
    row = owned_session(session_id, user, db)
    if row.status == "submitted":
        return public_session(row)
    if row.status != "active":
        raise HTTPException(409, "This review was discarded. Start another check.")
    if not data.answer.strip():
        raise HTTPException(422, "Type a short answer before submitting.")
    snapshot = row.definition_snapshot
    question = snapshot["question"]
    case_sensitive = question.get("case_sensitive", False)
    correct = normalize(data.answer, case_sensitive) in {
        normalize(a, case_sensitive) for a in question["accepted"]
    }
    topic_sources = snapshot["sources"]
    observed_study = bool(
        db.scalar(
            select(ExerciseAttempt.id)
            .where(
                ExerciseAttempt.user_id == user.id,
                ExerciseAttempt.exercise_id.in_(topic_sources),
                ExerciseAttempt.created_at > row.created_at,
            )
            .limit(1)
        )
    )
    observed_study = observed_study or bool(
        db.scalar(
            select(LessonCheckpointAttempt.id)
            .where(
                LessonCheckpointAttempt.user_id == user.id,
                LessonCheckpointAttempt.lesson_id == row.concept_id,
                LessonCheckpointAttempt.created_at > row.created_at,
            )
            .limit(1)
        )
    )
    assisted = data.used_help or observed_study
    kind = (
        "assisted"
        if assisted
        else "immediate"
        if row.mode == "practice"
        else "fresh-delayed"
        if snapshot["fresh"]
        else "repeated-delayed"
    )
    interval = 1
    if row.mode == "delayed" and correct and not assisted:
        interval = (
            min(max(3, snapshot["interval_days"] * 2), 30) if snapshot["fresh"] else snapshot["interval_days"]
        )
    now = utcnow()
    row.answer, row.used_help = data.answer, data.used_help
    row.status, row.active_key, row.submitted_at, row.updated_at = "submitted", None, now, now
    row.result = {
        "correct": correct,
        "observed_study": observed_study,
        "evidence_kind": kind,
        "expected": question["accepted"][0],
        "explanation": question["explanation"],
        "interval_days": interval,
        "next_due_at": (now + timedelta(days=interval)).isoformat(),
        "note": "Independence is self-reported. This exact short-answer check does not change mastery or certify expertise.",
    }
    db.flush()
    return public_session(row)


@router.post("/recall/sessions/{session_id}/discard")
def discard(session_id: int, user: Learner, db: DB):
    row = owned_session(session_id, user, db)
    if row.status == "submitted":
        raise HTTPException(409, "Recorded feedback cannot be discarded.")
    row.status, row.active_key, row.updated_at = "abandoned", None, utcnow()
    return public_session(row)
