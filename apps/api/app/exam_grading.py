"""Deterministic scoring against the immutable definition captured at start."""


def grade_exam(exam, answers, lesson_definitions):
    categories = {}
    explanations = []
    for question in exam["questions"]:
        if question.get("kind") == "short":
            continue
        given = answers.get(question["id"])
        correct = (
            set(given or []) == set(question["answer"])
            if question.get("kind") == "multiple"
            else given == question["answer"]
        )
        values = categories.setdefault(question["skill"], {"correct": 0, "total": 0})
        values["total"] += 1
        values["correct"] += int(correct)
        explanations.append(
            {
                "id": question["id"],
                "correct": correct,
                "answer": question["answer"],
                "explanation": question["explanation"],
            }
        )
    scores = [
        {"skill": skill, "score": round(value["correct"] / value["total"] * 100), **value}
        for skill, value in categories.items()
    ]
    correct = sum(item["correct"] for item in explanations)
    total = len(explanations)
    weak = {item["skill"] for item in scores if item["score"] < 80}
    revisit = {id for skill in weak for id in exam.get("topic_lessons", {}).get(skill, [])}
    result = {
        "score": round(correct / total * 100),
        "correct": correct,
        "total": total,
        "categories": scores,
        "explanations": explanations,
        "recommendations": [
            {"id": lesson["id"], "title": lesson["title"]}
            for lesson in lesson_definitions
            if lesson["skill"] in weak or lesson["id"] in revisit
        ],
        "study_recommendations": [
            resource for resource in exam.get("study_resources", []) if resource["skill"] in weak
        ],
        "practical_followup": exam.get("practical_followup"),
    }
    policy = exam.get("evaluation_policy")
    if policy:
        meets = correct * 100 >= policy["overall_target"] * total and all(
            item["correct"] * 100 >= policy["category_target"] * item["total"] for item in scores
        )
        result["evaluation"] = {
            **policy,
            "meets_target": meets,
            "label": "Knowledge target met" if meets else "More practice recommended",
        }
    if any(q.get("kind") == "short" for q in exam["questions"]):
        result["manual_count"] = sum(q.get("kind") == "short" for q in exam["questions"])
        result["score_note"] = "Objective questions only. Written answers require separate self/human review."
        result["recommended_exercises"] = [
            {"id": exercise["id"], "title": exercise["title"]}
            for lesson in lesson_definitions
            if lesson["id"] in revisit
            for exercise in lesson["exercises"]
        ]
    return result
