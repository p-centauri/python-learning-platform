from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from .auth import DB, Learner
from .content import catalog, lessons
from .models import LearningPreferences, LessonProgress, ExerciseAttempt, ReviewItem, ExamAttempt, utcnow
from .study_plan import build_plan, plan_content
from .retention import overview_for

router = APIRouter(tags=["learning plan"])


class PreferencesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goal: Literal["python", "backend", "applied-ai", "backend-ai"]
    weekly_hours: int = Field(strict=True, ge=1, le=20)
    starting_mode: Literal["recommended", "from-start"] = "recommended"


def response_for(user, db):
    preferences = db.get(LearningPreferences, user.id)
    response = {
        "goals": plan_content()["goals"],
        "preferences": None,
        "plan": None,
        "policy_version": plan_content()["version"],
        "catalog_version": catalog()["version"],
    }
    if preferences is None:
        return response
    response["preferences"] = {
        "goal": preferences.goal,
        "weekly_hours": preferences.weekly_hours,
        "starting_mode": preferences.starting_mode,
    }
    completed = set(db.scalars(select(LessonProgress.lesson_id).where(LessonProgress.user_id == user.id)))
    attempts = list(
        db.scalars(
            select(ExerciseAttempt).where(ExerciseAttempt.user_id == user.id).order_by(ExerciseAttempt.id)
        )
    )
    reviews = list(
        db.scalars(
            select(ReviewItem)
            .where(ReviewItem.user_id == user.id, ReviewItem.due_at <= utcnow())
            .order_by(ReviewItem.due_at, ReviewItem.id)
        )
    )
    exams = list(
        db.scalars(
            select(ExamAttempt)
            .where(ExamAttempt.user_id == user.id, ExamAttempt.status == "submitted")
            .order_by(ExamAttempt.submitted_at.desc(), ExamAttempt.id.desc())
        )
    )
    response["plan"] = build_plan(
        preferences, lessons(), completed, attempts, reviews, exams, overview_for(db, user.id)["topics"]
    )
    return response


@router.get("/learning-plan")
def get_plan(user: Learner, db: DB):
    return response_for(user, db)


@router.put("/learning-plan")
def save_plan(data: PreferencesInput, user: Learner, db: DB):
    preferences = db.get(LearningPreferences, user.id)
    if preferences is None:
        preferences = LearningPreferences(user_id=user.id)
        db.add(preferences)
    preferences.goal = data.goal
    preferences.weekly_hours = data.weekly_hours
    preferences.starting_mode = data.starting_mode
    db.flush()
    return response_for(user, db)
