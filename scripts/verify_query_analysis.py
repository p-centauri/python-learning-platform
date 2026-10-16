"""Trusted installed query observations only; never evaluate learner uploads."""
import argparse
import json
import os
import re
from pathlib import Path
import shutil
import sys
import tempfile
import venv
from persistence_db import disposable_postgres
from verify_delivery_recovery import completed_sources as prior_sources
from verify_ingestion_package import checked

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "content/projects/query-analysis"


def completed_sources(area):
    roots = prior_sources(area)
    for name, package, references in [("delivery-release", "academy_delivery_release", ["operations.py"]), ("query-analysis", "academy_query_analysis", ["summary.sql", "history.sql", "search.sql"])]:
        source = area / name
        lab = ROOT / "content/projects" / name
        shutil.copytree(lab / "starter", source, ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "*.egg-info"))
        for filename in references:
            shutil.copyfile(lab / "reference" / filename, source / "src" / package / filename)
        roots.append(source)
    return roots


def verify_lesson_examples(python, outside, env):
    expected = {
        "python-query-joins": [("a", 0, 2), ("b", 7, 0)],
        "python-query-windows": [(1, 0, None, 0), (3, 7, 0, 7), (8, 2, 7, 9)],
        "python-query-jsonb": [(True, False, "")],
        "python-query-evidence": [("a", 8, 2)],
    }
    examples = []
    for lesson in [*expected, "python-query-indexes"]:
        body = (ROOT / "content/lessons" / (lesson + ".md")).read_text()
        blocks = re.findall(r"```sql\n(.*?)```", body, re.S)
        assert len(blocks) == 1, lesson
        examples.append((lesson, blocks[0]))
    program = "EXAMPLES = " + repr(examples) + "\nEXPECTED = " + repr(expected) + "\n" + """
import os
from academy_ingestion_service import make_engine
from academy_ingestion_service.database import url_from_dsn
from academy_query_analysis.support import read
from academy_query_analysis.plans import summarize_plan
engine = make_engine(url_from_dsn(os.environ['ACADEMY_QUERY_DSN']))
try:
    with read(engine) as connection:
        for lesson, sql in EXAMPLES:
            rows = connection.exec_driver_sql(sql).all()
            if lesson == 'python-query-indexes':
                assert summarize_plan(rows[0][0]).actual_rows == 1
            else:
                assert [tuple(row) for row in rows] == EXPECTED[lesson], lesson
finally:
    engine.dispose()
print('PASS: five literal lesson SQL examples evaluated on actual PostgreSQL.')
"""
    (outside / "lesson_examples.py").write_text(program)
    result = checked([str(python), "-I", "lesson_examples.py"], outside, env)
    assert not result.stderr
    print(result.stdout, end="")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-query-artifacts-") as directory:
        area = Path(directory)
        wheels = []
        for source in completed_sources(area):
            built = checked([sys.executable, "-m", "build", "--no-isolation"], source)
            assert "Building wheel from sdist" in built.stdout
            wheels.append(str(next((source / "dist").glob("*.whl"))))
        environment = area / "installed"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / "bin/python"
        outside = area / "outside"
        outside.mkdir()
        env = {key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "PYTHONHOME", "MYPYPATH"} and not key.startswith("ACADEMY_")}
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        install = [str(python), "-m", "pip", "install"]
        if args.wheelhouse:
            install += ["--no-index", "--find-links", str(args.wheelhouse.resolve())]
        checked(install + wheels + ["pytest==9.0.3", "mypy==2.3.1", "types-psycopg2==2.9.21.20260911"], outside, env)
        checked([str(python), "-m", "pip", "check"], outside, env)
        quiet = checked([str(python), "-I", "-c", "import academy_query_analysis"], outside, env)
        assert quiet.stdout == quiet.stderr == ""
        probe = checked([str(python), "-I", "-c", "from importlib.resources import files; import academy_query_analysis; package=files('academy_query_analysis'); assert package.joinpath('py.typed').is_file(); assert all(package.joinpath(n).is_file() for n in ('summary.sql','history.sql','search.sql','range.sql','notes.sql','annotation.sql')); print(academy_query_analysis.__file__)"], outside, env)
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        checked([str(python), "-I", "-m", "mypy", "--strict", "-p", "academy_query_analysis"], outside, env)
        checked([str(python), "-I", "-m", "mypy", "--strict", "demo.py"], outside, env)
        with disposable_postgres() as dsn:
            env["ACADEMY_QUERY_DSN"] = dsn
            tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
            assert "36 passed" in tests.stdout and "skipped" not in tests.stdout, tests.stdout
            print(tests.stdout, end="")
            verify_lesson_examples(python, outside, env)
            demo = checked([str(python), "-I", "demo.py", "--output", "queries.json"], outside, env)
            report = json.loads(demo.stdout)
            assert report == json.loads((outside / "queries.json").read_text()) and not demo.stderr
            assert report["head"] == ["delivery_004"] and report["server_version"] // 10000 == 17
            assert report["functional"]["summary"] == dict(records=4, total=11, noted_records=3)
            assert report["functional"]["history"] == [dict(revision=1,value=0,previous=None,delta=None,running_total=0,latest=False),dict(revision=3,value=7,previous=0,delta=7,running_total=7,latest=False),dict(revision=8,value=2,previous=7,delta=-5,running_total=9,latest=True)]
            assert report["functional"]["facts_unchanged"] and report["functional"]["source_ready"]
            assert report["workload"] == dict(records=40000, notes=40000, rare_notes=10, selective_returned=32, limit=32, analyzed=True)
            assert report["equivalent"] == dict(range=True,notes=True) and report["checked_out"] == dict(source=0,query=0)
            for group in ("baseline", "indexed"):
                for plan in report[group].values():
                    assert plan["actual_rows"] in (10,32) and plan["execution_ms"] >= 0 and plan["nodes"]
            if args.report_output:
                args.report_output.parent.mkdir(parents=True, exist_ok=True)
                args.report_output.write_text(json.dumps(report, indent=2) + "\n")
                assert json.loads(args.report_output.read_text()) == report
    print("PASS: nine source/wheel artifacts, clean install, 36 public cases, actual joins/windows/JSONB and result-equivalent baseline/indexed PostgreSQL plans. Owned resources removed.")


if __name__ == "__main__":
    main()
