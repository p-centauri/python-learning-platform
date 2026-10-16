from datetime import timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from .auth import DB, Learner
from .config import settings
from .content import catalog, exercise_by_id, lesson_by_id, lessons, public_exercise, public_lesson
from .mastery import mastery_scores
from .retention import overview_for
from .interactivity import sections_for, navigation_for, glossary_entries
from .models import Bookmark, ExerciseAttempt, ExerciseState, LessonProgress, Note, ReviewItem, utcnow

router = APIRouter(tags=["learning"])


def require_lesson(lesson_id):
    lesson = lesson_by_id(lesson_id)
    if lesson is None:
        raise HTTPException(404, "Lesson not found.")
    return lesson


def require_exercise(exercise_id):
    lesson, exercise = exercise_by_id(exercise_id)
    if exercise is None:
        raise HTTPException(404, "Exercise not found.")
    return lesson, exercise


def state_for(db, user_id, exercise_id):
    state = db.scalar(
        select(ExerciseState).where(
            ExerciseState.user_id == user_id, ExerciseState.exercise_id == exercise_id
        )
    )
    if state is None:
        state = ExerciseState(user_id=user_id, exercise_id=exercise_id, hints_used=0, revealed=False)
        db.add(state)
        db.flush()
    return state


@router.get("/curriculum")
def curriculum(user: Learner, db: DB):
    completed = set(db.scalars(select(LessonProgress.lesson_id).where(LessonProgress.user_id == user.id)))
    data = catalog()
    return {
        "version": data["version"],
        "tracks": data["tracks"],
        "modules": data["modules"],
        "lessons": [
            {**public_lesson(lesson), "completed": lesson["id"] in completed} for lesson in lessons()
        ],
    }


@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: str, user: Learner, db: DB):
    lesson = require_lesson(lesson_id)
    body = (settings.content_dir / lesson["path"]).read_text()
    note = db.scalar(select(Note).where(Note.user_id == user.id, Note.lesson_id == lesson_id))
    bookmarked = db.scalar(
        select(Bookmark.id).where(Bookmark.user_id == user.id, Bookmark.lesson_id == lesson_id)
    )
    completed = db.scalar(
        select(LessonProgress.id).where(
            LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id
        )
    )
    return {
        **public_lesson(lesson),
        "body": body,
        "sections": sections_for(body),
        "navigation": navigation_for(lesson),
        "exercises": [public_exercise(e) for e in lesson["exercises"]],
        "note": note.body if note else "",
        "bookmarked": bool(bookmarked),
        "completed": bool(completed),
    }


@router.put("/lessons/{lesson_id}/complete")
def complete(lesson_id: str, user: Learner, db: DB):
    require_lesson(lesson_id)
    if not db.scalar(
        select(LessonProgress.id).where(
            LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id
        )
    ):
        db.add(LessonProgress(user_id=user.id, lesson_id=lesson_id))
    return {"completed": True}


class NoteInput(BaseModel):
    body: str = Field(max_length=20000)


@router.put("/lessons/{lesson_id}/note")
def save_note(lesson_id: str, data: NoteInput, user: Learner, db: DB):
    require_lesson(lesson_id)
    note = db.scalar(select(Note).where(Note.user_id == user.id, Note.lesson_id == lesson_id))
    if note:
        note.body = data.body
    else:
        db.add(Note(user_id=user.id, lesson_id=lesson_id, body=data.body))
    return {"saved": True}


class Toggle(BaseModel):
    enabled: bool


@router.put("/lessons/{lesson_id}/bookmark")
def bookmark(lesson_id: str, data: Toggle, user: Learner, db: DB):
    require_lesson(lesson_id)
    query = select(Bookmark).where(Bookmark.user_id == user.id, Bookmark.lesson_id == lesson_id)
    existing = db.scalar(query)
    if data.enabled and not existing:
        db.add(Bookmark(user_id=user.id, lesson_id=lesson_id))
    elif existing and not data.enabled:
        db.delete(existing)
    return {"bookmarked": data.enabled}


@router.get("/bookmarks")
def bookmarks(user: Learner, db: DB):
    ids = set(db.scalars(select(Bookmark.lesson_id).where(Bookmark.user_id == user.id)))
    return [public_lesson(lesson) for lesson in lessons() if lesson["id"] in ids]


@router.get("/exercises/{exercise_id}")
def exercise_detail(exercise_id: str, user: Learner, db: DB):
    lesson, exercise = require_exercise(exercise_id)
    state = db.scalar(
        select(ExerciseState).where(
            ExerciseState.user_id == user.id, ExerciseState.exercise_id == exercise_id
        )
    )
    attempts = list(
        db.scalars(
            select(ExerciseAttempt)
            .where(ExerciseAttempt.user_id == user.id, ExerciseAttempt.exercise_id == exercise_id)
            .order_by(ExerciseAttempt.id.desc())
            .limit(50)
        )
    )
    solution_visible = (state and state.revealed) or any(a.score == 100 for a in attempts)
    return {
        **public_exercise(exercise),
        "lesson_id": lesson["id"],
        "skill": lesson["skill"],
        "hints": exercise["hints"][: state.hints_used if state else 0],
        "revealed": state.revealed if state else False,
        "solution": exercise["solution"] if solution_visible else None,
        "attempts": [
            {
                "id": a.id,
                "answer": a.answer,
                "score": a.score,
                "hints_used": a.hints_used,
                "is_review": a.is_review,
                "created_at": a.created_at,
            }
            for a in attempts
        ],
    }


@router.post("/exercises/{exercise_id}/hint")
def hint(exercise_id: str, user: Learner, db: DB):
    _, exercise = require_exercise(exercise_id)
    state = state_for(db, user.id, exercise_id)
    state.hints_used = min(state.hints_used + 1, len(exercise["hints"]))
    return {"hints": exercise["hints"][: state.hints_used]}


@router.post("/exercises/{exercise_id}/reveal")
def reveal(exercise_id: str, user: Learner, db: DB):
    _, exercise = require_exercise(exercise_id)
    state_for(db, user.id, exercise_id).revealed = True
    return {"solution": exercise["solution"]}


class AnswerInput(BaseModel):
    answer: int = Field(strict=True, ge=0, le=20)
    review: bool = False


@router.post("/exercises/{exercise_id}/attempts", status_code=201)
def submit(exercise_id: str, data: AnswerInput, user: Learner, db: DB):
    lesson, exercise = require_exercise(exercise_id)
    if data.answer >= len(exercise["options"]):
        raise HTTPException(422, "Choose one of the available answers.")
    state = state_for(db, user.id, exercise_id)
    review = db.scalar(
        select(ReviewItem).where(ReviewItem.user_id == user.id, ReviewItem.exercise_id == exercise_id)
    )
    if data.review and (not review or review.due_at.replace(tzinfo=utcnow().tzinfo) > utcnow()):
        raise HTTPException(409, "This exercise is not due for review.")
    score = 100 if data.answer == exercise["answer"] else 0
    attempt = ExerciseAttempt(
        user_id=user.id,
        lesson_id=lesson["id"],
        exercise_id=exercise_id,
        answer=data.answer,
        score=score,
        hints_used=state.hints_used,
        revealed=state.revealed,
        is_review=data.review,
    )
    db.add(attempt)
    if review is None:
        days = 3 if score else 1
        db.add(
            ReviewItem(
                user_id=user.id,
                exercise_id=exercise_id,
                interval_days=days,
                due_at=utcnow() + timedelta(days=days),
            )
        )
    elif data.review:
        review.interval_days = min(review.interval_days * 2, 30) if score else 1
        review.repetitions += 1
        review.due_at = utcnow() + timedelta(days=review.interval_days)
    db.flush()
    return {
        "id": attempt.id,
        "review_topic_id": lesson["id"],
        "score": score,
        "feedback": "Correct. Compare your reasoning with the explanation."
        if score
        else "Not quite. Trace the failure boundary and try again.",
        "solution": exercise["solution"] if score or state.revealed else None,
    }


@router.get("/dashboard")
def dashboard(user: Learner, db: DB):
    attempts = list(
        db.scalars(
            select(ExerciseAttempt).where(ExerciseAttempt.user_id == user.id).order_by(ExerciseAttempt.id)
        )
    )
    completed = set(db.scalars(select(LessonProgress.lesson_id).where(LessonProgress.user_id == user.id)))
    skills = mastery_scores(lessons(), attempts)
    reviews = list(
        db.scalars(
            select(ReviewItem)
            .where(ReviewItem.user_id == user.id, ReviewItem.due_at <= utcnow())
            .order_by(ReviewItem.due_at)
        )
    )
    next_lesson = next((lesson for lesson in lessons() if lesson["id"] not in completed), lessons()[0])
    weak = sorted([s for s in skills if s["assessed"] and s["score"] < 70], key=lambda s: s["score"])
    activity_dates = {a.created_at.date() for a in attempts} | {
        p.completed_at.date()
        for p in db.scalars(select(LessonProgress).where(LessonProgress.user_id == user.id))
    }
    day = utcnow().date()
    if day not in activity_dates:
        day -= timedelta(days=1)
    streak = 0
    while day in activity_dates:
        streak += 1
        day -= timedelta(days=1)
    return {
        "completed_lessons": len(completed),
        "total_lessons": len(lessons()),
        "attempts": len(attempts),
        "solved_exercises": len({a.exercise_id for a in attempts if a.score == 100 and not a.revealed}),
        "mastery": round(sum(s["score"] for s in skills) / len(skills)),
        "skills": skills,
        "weak_skills": weak,
        "streak": streak,
        "review_due": len(reviews),
        "retention_due": overview_for(db, user.id)["summary"]["due"],
        "next_lesson": public_lesson(next_lesson),
        "recent_attempts": [
            {
                "id": a.id,
                "exercise_id": a.exercise_id,
                "title": exercise_by_id(a.exercise_id)[1]["title"],
                "score": a.score,
                "created_at": a.created_at,
            }
            for a in attempts[-5:][::-1]
        ],
    }


@router.get("/reviews")
def review_list(user: Learner, db: DB):
    reviews = db.scalars(select(ReviewItem).where(ReviewItem.user_id == user.id).order_by(ReviewItem.due_at))
    return [
        {
            "exercise_id": r.exercise_id,
            "title": exercise_by_id(r.exercise_id)[1]["title"],
            "skill": exercise_by_id(r.exercise_id)[0]["skill"],
            "due_at": r.due_at,
            "due": r.due_at.replace(tzinfo=utcnow().tzinfo) <= utcnow(),
            "interval_days": r.interval_days,
            "repetitions": r.repetitions,
        }
        for r in reviews
    ]


@router.get("/search")
def search(user: Learner, db: DB, q: str = Query(min_length=2, max_length=100)):
    term = q.casefold()
    results = []
    for lesson in lessons():
        body = (settings.content_dir / lesson["path"]).read_text()
        if term in f"{lesson['title']} {lesson['skill']} {body}".casefold():
            results.append({"type": "Lesson", "title": lesson["title"], "href": f"/lessons/{lesson['id']}"})
        for exercise in lesson["exercises"]:
            if term in f"{exercise['title']} {exercise['prompt']}".casefold():
                results.append(
                    {"type": "Exercise", "title": exercise["title"], "href": f"/practice/{exercise['id']}"}
                )
    for note in db.scalars(select(Note).where(Note.user_id == user.id)):
        if term in note.body.casefold():
            results.append(
                {
                    "type": "Note",
                    "title": require_lesson(note.lesson_id)["title"],
                    "href": f"/lessons/{note.lesson_id}",
                }
            )
    for project in catalog()["projects"]:
        if term in f"{project['title']} {project['description']}".casefold():
            results.append({"type": "Project", "title": project["title"], "href": "/projects"})
    for entry in glossary_entries():
        if term in f"{entry['term']} {entry['definition']}".casefold():
            results.append({"type": "Glossary", "title": entry["term"], "href": f"/glossary#{entry['id']}"})
    return results[:30]
