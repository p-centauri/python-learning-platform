"""Audit published learning layers, dependency paths and authenticated starter manifests without execution."""

import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / "content" / name).read_text())


def audit(baseline=None):
    c = read("catalog.json")
    inter = read("lesson-interactions.json")
    recall = read("review-questions.json")
    rub = read("project-rubrics.json")
    lessons = {row["id"]: row for row in c["lessons"]}
    modules = {m["id"]: m for m in c["modules"]}
    tracks = {t["id"] for t in c["tracks"]}
    projects = {p["id"]: p for p in c["projects"]}
    assert (
        len(lessons) == len(c["lessons"])
        and len(modules) == len(c["modules"])
        and len(projects) == len(c["projects"])
    )
    concepts = {x["lesson_id"]: x for x in recall["concepts"]}
    terms = {x["id"]: x for x in inter["glossary"]}
    assert set(lessons) == set(inter["lessons"]) == set(concepts)
    assert set(projects) == set(rub["projects"])
    visited = set()
    active = set()
    snippets = 0

    def visit(id):
        assert id in lessons, id
        assert id not in active, ("cycle", id)
        if id in visited:
            return
        active.add(id)
        for dependency in lessons[id]["prerequisites"]:
            visit(dependency)
        active.remove(id)
        visited.add(id)

    for id, row in lessons.items():
        visit(id)
        assert (
            row["track_id"] in tracks
            and row["module_id"] in modules
            and modules[row["module_id"]]["track_id"] == row["track_id"]
        )
        p = (ROOT / "content" / row["path"]).resolve()
        assert p.is_relative_to(ROOT / "content") and p.is_file(), id
        body = p.read_text()
        assert len(body.strip()) > 100 and "TODO: write lesson" not in body, id
        interaction = inter["lessons"][id]
        assert (
            len(row["exercises"]) == len(interaction["checkpoints"]) == len(concepts[id]["questions"]) == 2
        ), id
        assert len(interaction["diagram"]["steps"]) >= 2 and interaction["glossary_ids"], id
        assert all(t in terms and id in terms[t]["lesson_ids"] for t in interaction["glossary_ids"]), id
        assert set(concepts[id]["sources"]) <= set(x["id"] for x in row["exercises"]), id
        for q in row["exercises"]:
            assert type(q["answer"]) is int and 0 <= q["answer"] < len(q["options"]) and q["solution"], q[
                "id"
            ]
        for code in re.findall(r"```python\n(.*?)```", body, re.S):
            ast.parse(code, filename=str(p))
            snippets += 1
        for target in re.findall(r"\]\((/lessons/[^)#]+)(?:#[^)]*)?\)", body):
            assert target.split("/")[-1] in lessons, (id, target)
    for id, m in modules.items():
        assert m["track_id"] in tracks and any(row["module_id"] == id for row in lessons.values()), id
        if m.get("project_id"):
            assert m["project_id"] in projects, id
    node = ast.parse((ROOT / "apps/api/app/assessments.py").read_text())
    fn = next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == "project_starter")
    assignment = next(
        n
        for n in fn.body
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "bundles" for t in n.targets)
    )
    bundles = ast.literal_eval(assignment.value)
    starters = 0
    for id, p in projects.items():
        assert p["tasks"] and rub["projects"][id], id
        if "starter_url" not in p:
            # The three portfolio briefs have stated tasks and manual rubrics, rather than local starters.
            assert id in {"backend", "enterprise-rag", "finance"} or p.get("assessment_id"), id
            if p.get("assessment_id"):
                exam = read(f"assessments/{p['assessment_id']}.json")
                assert exam["review_project"] == id and exam["rubric"] == rub["projects"][id], id
            continue
        assert p.get("lesson_id") in lessons, id
        starters += 1
        assert p["starter_url"] == f"/api/projects/{id}/starter" and id in bundles, id
        name, files = bundles[id]
        base = (ROOT / "content/projects" / name / "starter").resolve()
        assert len(set(files)) == len(files) and all("reference" not in f for f in files), id
        for name in files:
            path = (base / name).resolve()
            assert path.is_relative_to(base) and path.is_file(), (id, name)
    assert starters == len(bundles)
    portfolios = read("portfolio-projects.json")
    assert set(portfolios["projects"]) == {"backend", "enterprise-rag", "finance"}
    for id, brief in portfolios["projects"].items():
        assert len(brief["sections"]) == 8 and all(lesson in lessons for lesson in brief["learning"]), id
        base = ROOT / "content/portfolio-packs" / id
        for file in [
            "README.md",
            "BRIEF.md",
            "app.py",
            "EVIDENCE.md",
            "fixtures.json",
            "pytest.ini",
            "tests/test_acceptance.py",
        ]:
            assert (base / file).is_file(), (id, file)
    if baseline:
        old = json.loads(Path(baseline).read_text())
        for collection, key in [("lessons", "id"), ("modules", "id"), ("projects", "id"), ("tracks", "id")]:
            now = {x[key]: x for x in c[collection]}
            assert all(now[x[key]] == x for x in old["catalog.json"][collection]), collection
        assert all(
            inter["lessons"][key] == value
            for key, value in old["lesson-interactions.json"]["lessons"].items()
        )
        oldterms = {x["id"]: x for x in old["lesson-interactions.json"]["glossary"]}
        assert all(terms[k] == v for k, v in oldterms.items())
        oldrec = {x["lesson_id"]: x for x in old["review-questions.json"]["concepts"]}
        assert all(concepts[k] == v for k, v in oldrec.items())
        assert all(rub["projects"][k] == v for k, v in old["project-rubrics.json"]["projects"].items())
        for name in ["coding-exercises.json", "learning-plans.json"]:
            assert read(name) == old[name], name
    return dict(
        catalog=c["version"],
        tracks=len(tracks),
        modules=len(modules),
        lessons=len(lessons),
        scenarios=sum(len(row["exercises"]) for row in lessons.values()),
        projects=len(projects),
        starters=starters,
        python_snippets_syntax=snippets,
        dependencies_acyclic=True,
        all_layers_and_links=True,
        baseline_definitions_preserved=bool(baseline),
        scope="Published content/layers/paths and static authenticated allowlists; syntax checks do not execute all snippets or certify learner mastery.",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    report = audit(args.baseline)
    if args.report_output:
        args.report_output.parent.mkdir(parents=True, exist_ok=True)
        args.report_output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
