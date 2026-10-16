import json
from functools import lru_cache
from .config import settings


@lru_cache
def catalog():
    return json.loads((settings.content_dir / "catalog.json").read_text())


def lessons():
    return catalog()["lessons"]


def lesson_by_id(lesson_id):
    return next((item for item in lessons() if item["id"] == lesson_id), None)


def exercise_by_id(exercise_id):
    for lesson in lessons():
        for exercise in lesson["exercises"]:
            if exercise["id"] == exercise_id:
                return lesson, exercise
    return None, None


def public_exercise(exercise):
    return {key: exercise[key] for key in ("id", "title", "kind", "difficulty", "prompt", "options")}


def public_lesson(lesson):
    return {
        **{key: value for key, value in lesson.items() if key != "exercises"},
        "exercise_count": len(lesson["exercises"]),
    }


@lru_cache
def exam_definitions():
    """Author-controlled banks; never return their private answer keys directly."""
    banks = [
        json.loads(path.read_text()) for path in sorted((settings.content_dir / "assessments").glob("*.json"))
    ]
    level_order = {"Beginner": 0, "Intermediate": 1, "Advanced": 2}
    return [catalog()["exam"]] + sorted(
        banks, key=lambda bank: (level_order.get(bank.get("level"), 3), bank["id"])
    )


def exam_by_id(exam_id):
    return next((exam for exam in exam_definitions() if exam["id"] == exam_id), None)
