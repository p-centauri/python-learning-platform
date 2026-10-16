from collections import defaultdict


def mastery_scores(lesson_definitions, attempts):
    """A repeated success contributes evidence once, never unlimited points."""
    grouped = defaultdict(list)
    for attempt in sorted(attempts, key=lambda a: a.id):
        if not attempt.is_review:
            grouped[attempt.exercise_id].append(attempt)
    skill_values = defaultdict(list)
    counts = defaultdict(int)
    for lesson in lesson_definitions:
        for exercise in lesson["exercises"]:
            history = grouped[exercise["id"]]
            eligible = [a for a in history if not a.revealed]
            value = 0
            if eligible:
                first = eligible[0]
                success = next((a for a in eligible if a.score == 100), None)
                hint_count = success.hints_used if success else eligible[-1].hints_used
                value = (0.7 * first.score + 0.3 * max(a.score for a in eligible)) * max(
                    0.4, 1 - 0.2 * hint_count
                )
                counts[lesson["skill"]] += 1
            skill_values[lesson["skill"]].append(value)
    return [
        {
            "skill": skill,
            "score": round(sum(values) / len(values)),
            "assessed": counts[skill],
            "total": len(values),
        }
        for skill, values in skill_values.items()
    ]
