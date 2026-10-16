"""Explainable study suggestions; never changes progress or mastery."""

import json
from datetime import timezone
from functools import lru_cache
from .config import settings


@lru_cache
def plan_content():
    return json.loads((settings.content_dir / "learning-plans.json").read_text())


def route_for(goal, lesson_definitions):
    by_id = {lesson["id"]: lesson for lesson in lesson_definitions}
    ordered = []
    seen = set()

    def include(lesson):
        if lesson["id"] in seen:
            return
        seen.add(lesson["id"])
        for prerequisite in lesson["prerequisites"]:
            include(by_id[prerequisite])
        ordered.append(lesson)

    for track in goal["tracks"]:
        for lesson in lesson_definitions:
            if lesson["track_id"] == track:
                include(lesson)
    return ordered


def build_plan(preferences, lesson_definitions, completed, attempts, reviews, exams, recall_topics=()):
    content = plan_content()
    goal = next(g for g in content["goals"] if g["id"] == preferences.goal)
    route = route_for(goal, lesson_definitions)
    by_id = {lesson["id"]: lesson for lesson in route}
    exercises = {e["id"]: (lesson, e) for lesson in route for e in lesson["exercises"]}
    # A correct response removes a practice task, but is not a competence certificate.
    solved = {a.exercise_id for a in attempts if a.score == 100}
    latest_practice = {a.exercise_id: a for a in attempts if not a.is_review}
    solved.difference_update(key for key, attempt in latest_practice.items() if attempt.score == 0)
    latest_exams = {}
    for exam in exams:  # newest submitted result first; active attempts never enter this function
        latest_exams.setdefault(exam.exam_id, exam)
    evidence = []
    weak = []
    uncovered = set()
    for exam in latest_exams.values():
        result = exam.result or {}
        evidence.append(
            {
                "id": exam.id,
                "title": (exam.definition_snapshot or {}).get("title", exam.exam_id),
                "score": result.get("score", 0),
                "submitted_at": exam.submitted_at,
            }
        )
        for category in result.get("categories", []):
            if category.get("total", 0) and category["correct"] * 100 < 80 * category["total"]:
                lesson_id = content["topic_lessons"].get(category["skill"])
                if not lesson_id:
                    lesson_id = next(
                        (lesson["id"] for lesson in route if lesson["skill"] == category["skill"]), None
                    )
                if lesson_id in by_id:
                    lesson = by_id[lesson_id]
                    reinforced = {
                        a.exercise_id
                        for a in attempts
                        if a.score == 100
                        and not a.is_review
                        and exam.submitted_at
                        and a.created_at.replace(tzinfo=timezone.utc)
                        >= exam.submitted_at.replace(tzinfo=timezone.utc)
                    }
                    missing = {e["id"] for e in lesson["exercises"]} - reinforced
                    if missing:
                        solved.difference_update(missing)
                        weak.append(
                            (
                                category["correct"] / category["total"],
                                lesson_id,
                                f"Your latest {evidence[-1]['title']} result shows {category['correct']}/{category['total']} in {category['skill']}. This lesson reinforces related foundations; it does not cover every exam topic.",
                            )
                        )
                elif category["skill"] not in {lesson["skill"] for lesson in lesson_definitions}:
                    uncovered.add(category["skill"])
    weak.sort(key=lambda item: (item[0], list(by_id).index(item[1])))
    start = next((lesson for lesson in route if lesson["id"] not in completed), None)
    reason = "Continue with the first unread lesson in your goal's published path."
    if not completed:
        reason = (
            "Start with Python setup because no reading progress or assessed starting point is available yet."
        )
    if preferences.starting_mode == "recommended":
        if weak:
            start, reason = by_id[weak[0][1]], weak[0][2]
        else:
            for exam_id, entry in content["knowledge_entry_points"].items():
                exam = latest_exams.get(exam_id)
                if exam and (exam.result or {}).get("evaluation", {}).get("meets_target") and entry in by_id:
                    entry_index = route.index(by_id[entry])
                    start = next(
                        (
                            lesson
                            for lesson in route[entry_index:] + route[:entry_index]
                            if lesson["id"] not in completed
                        ),
                        None,
                    )
                    reason = "Your submitted Python assessment met its knowledge target. Try this entry point; earlier lessons remain available and are not marked complete."
    else:
        reason = "You chose the beginning of the path. Read lessons stay complete; their unfinished practice remains in your queue."
    ordered = route
    if start and preferences.starting_mode == "recommended":
        index = route.index(start)
        ordered = route[index:] + route[:index]
    candidates = []
    seen = set()
    recall_lessons = {
        t["lesson_id"] for t in recall_topics if t["lesson_id"] in by_id and (t["due"] or t["active_id"])
    }

    def add(kind, item_id, title, href, minutes, why, lesson_id):
        key = (kind, item_id)
        # A due review takes the place of regular practice for the same exercise.
        if key in seen or (kind == "practice" and ("review", item_id) in seen):
            return
        seen.add(key)
        candidates.append(
            dict(
                kind=kind,
                id=item_id,
                title=title,
                href=href,
                minutes=minutes,
                reason=why,
                lesson_id=lesson_id,
            )
        )

    def add_lesson(lesson, why):
        if lesson["id"] not in completed:
            add(
                "lesson",
                lesson["id"],
                lesson["title"],
                f"/lessons/{lesson['id']}",
                lesson["minutes"],
                why,
                lesson["id"],
            )
        for exercise in lesson["exercises"]:
            if exercise["id"] not in solved and lesson["id"] not in recall_lessons:
                add(
                    "practice",
                    exercise["id"],
                    exercise["title"],
                    f"/practice/{exercise['id']}",
                    10,
                    "Practise this lesson. Reading completion alone is not evidence of mastery.",
                    lesson["id"],
                )

    for topic in recall_topics:
        if topic["lesson_id"] not in recall_lessons:
            continue
        active = topic["active_id"]
        add(
            "review",
            topic["id"],
            f"Short-answer check: {topic['title']}",
            f"/review/checks/{active}" if active else f"/review/{topic['id']}",
            10,
            "Resume your saved short-answer check. Its result will stay separate from mastery."
            if active
            else "A delayed short-answer check is due. An unseen question can provide fresh retrieval evidence."
            if topic["unseen_questions"]
            else "A delayed check is due. All current variations have been seen; this will be repeated-question practice.",
            topic["lesson_id"],
        )
    for review in reviews:
        if review.exercise_id in exercises:
            lesson, exercise = exercises[review.exercise_id]
            if lesson["id"] in recall_lessons:
                continue
            add(
                "review",
                exercise["id"],
                exercise["title"],
                f"/practice/{exercise['id']}?review=1",
                10,
                "This exercise is due for spaced review.",
                lesson["id"],
            )
    for exercise_id, attempt in latest_practice.items():
        if attempt.score == 0 and exercise_id in exercises and exercise_id not in solved:
            lesson, _ = exercises[exercise_id]
            add_lesson(
                lesson,
                "Your latest practice answer here was incorrect. Revisit the explanation and try again.",
            )
    if preferences.starting_mode == "recommended":
        for _, lesson_id, why in weak:
            add_lesson(by_id[lesson_id], why)
    for lesson in route:
        if lesson["id"] in completed:
            add_lesson(lesson, "Finish practice for a lesson you have already read.")
    for lesson in ordered:
        add_lesson(
            lesson,
            reason
            if start and lesson["id"] == start["id"]
            else "Continue your chosen path in its published order.",
        )
    budget = preferences.weekly_hours * 60
    items = []
    used = 0
    for item in candidates:
        if used + item["minutes"] > budget:
            break  # Preserve ordering; never schedule later practice ahead of its lesson to fill a gap.
        items.append(item)
        used += item["minutes"]
    return {
        "goal_title": goal["title"],
        "weekly_minutes": budget,
        "scheduled_minutes": used,
        "remaining_minutes": budget - used,
        "items": items,
        "starting_point": {
            "id": start["id"],
            "title": start["title"],
            "reason": reason,
            "prerequisites": [
                {"id": key, "title": by_id[key]["title"]}
                for key in start["prerequisites"]
                if key not in completed
            ],
        }
        if start
        else None,
        "evidence": evidence,
        "uncovered_topics": sorted(uncovered),
        "route": [
            {"id": lesson["id"], "title": lesson["title"], "completed": lesson["id"] in completed}
            for lesson in route
        ],
        "coverage_note": "This plan uses published lessons only. The full course is still growing. Times are estimates, not recorded study time or a promise of job readiness.",
    }
