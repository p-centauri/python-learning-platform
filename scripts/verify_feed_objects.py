"""Trusted reference wheel/composition checks, never learner upload execution."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import venv

from verify_ingestion_package import checked

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "content/projects/feed-objects"
INTEGRATION = '''from academy_ingest import Record
from academy_feed_objects import Budget, FeedKey, Reading, Snapshot

records = [Record("api", 5), Record("worker", 10)]
budget = Budget(len(records))
snapshot = Snapshot(Reading(FeedKey("feed", row.id), row.value) for row in records)
assert budget.limit == len(snapshot) == 2
assert sum(row.value for row in snapshot) == 15
assert {snapshot[0].key: 5}[FeedKey("feed", "api")] == 5
records.clear()
assert len(snapshot) == 2
print("installed ingestion object adapter passed")
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-objects-") as directory:
        temporary = Path(directory)
        wheels = []
        for name, package, files in [
            ("ingestion-package", "academy_ingest", ["parser.py", "http.py"]),
            ("feed-objects", "academy_feed_objects", ["objects.py"]),
        ]:
            lab = ROOT / "content/projects" / name
            source = temporary / name
            shutil.copytree(
                lab / "starter", source, ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache")
            )
            for filename in files:
                shutil.copyfile(lab / "reference" / filename, source / "src" / package / filename)
            checked([sys.executable, "-m", "build", "--no-isolation"], source)
            wheels.append(str(next((source / "dist").glob("*.whl"))))
        environment = temporary / "installed"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        outside = temporary / "outside"
        outside.mkdir()
        env = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "PYTHONHOME"}}
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        install = [str(python), "-m", "pip", "install"]
        if args.wheelhouse:
            install += ["--no-index", "--find-links", str(args.wheelhouse.resolve())]
        checked(install + wheels + ["pytest==9.0.3"], outside, env)
        checked([str(python), "-m", "pip", "check"], outside, env)
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
        assert "50 passed" in tests.stdout, tests.stdout
        quiet = checked([str(python), "-I", "-c", "import academy_feed_objects"], outside, env)
        assert quiet.stdout == quiet.stderr == "", quiet
        imported = checked(
            [str(python), "-I", "-c",
             "from importlib.resources import files; import academy_feed_objects; assert files('academy_feed_objects').joinpath('py.typed').is_file(); print(academy_feed_objects.__file__)"],
            outside, env,
        )
        assert Path(imported.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        demo = checked([str(python), "-I", "demo.py"], outside, env)
        assert json.loads(demo.stdout) == {"limit": 2, "count": 2, "total": 15} and demo.stderr == ""
        (outside / "integration.py").write_text(INTEGRATION)
        checked(
            [sys.executable, "-m", "mypy", "--strict", "integration.py"], outside,
            {**env, "MYPYPATH": os.pathsep.join(str(temporary / name / "src") for name in ["ingestion-package", "feed-objects"])},
        )
        result = checked([str(python), "-I", "integration.py"], outside, env)
        assert result.stderr == "", result.stderr
        print("PASS: sdist/wheel builds, fresh install, pip check, 50 pytest cases, quiet import, typing marker, installed demo and strict-typed offline ingestion adapter.")


if __name__ == "__main__":
    main()
