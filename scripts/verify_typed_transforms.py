"""Trusted installed runtime/checker evidence, never a learner-code evaluator."""

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
LAB = ROOT / "content/projects/typed-transforms"
INTEGRATION = """from typing import assert_type
from academy_ingest import Record
from academy_feed_objects import FeedKey, Reading, Snapshot
from academy_typed_transforms import Consumer, Row, Valued, decode_row, first, map_rows, watch_call

records = [Record("api", 5), Record("worker", 10)]
def value_of(row: Valued[int]) -> int:
    return row.value
values = map_rows(records, value_of)
assert_type(values, tuple[int, ...])
assert values == (5, 10)
events: list[str] = []
def observe_any(value: object, /) -> None:
    assert isinstance(value, str)
    events.append(value)
observer: Consumer[str] = observe_any
observed = watch_call(decode_row, observer=observer)
rows = map_rows([{"id":"api","value":5},{"id":"worker","value":10}], observed)
assert_type(rows, tuple[Row, ...])
assert_type(first(rows), Row | None)
snapshot = Snapshot(Reading(FeedKey("feed", row.id), row.value) for row in rows)
assert len(snapshot) == 2 and sum(row.value for row in snapshot) == 15
assert events == ["started", "returned", "started", "returned"]
records.clear()
assert len(snapshot) == 2 and values == (5, 10)
print("installed typed record/snapshot adapter passed")
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-typing-") as directory:
        temporary = Path(directory)
        wheels = []
        for name, package, files in [
            ("ingestion-package", "academy_ingest", ["parser.py", "http.py"]),
            ("feed-objects", "academy_feed_objects", ["objects.py"]),
            ("typed-transforms", "academy_typed_transforms", ["transform.py"]),
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
        env = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "PYTHONHOME", "MYPYPATH"}}
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        install = [str(python), "-m", "pip", "install"]
        if args.wheelhouse:
            install += ["--no-index", "--find-links", str(args.wheelhouse.resolve())]
        checked(install + wheels + ["pytest==9.0.3", "mypy==2.3.1"], outside, env)
        checked([str(python), "-m", "pip", "check"], outside, env)
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        shutil.copytree(LAB / "starter/typing", outside / "typing")
        shutil.copyfile(LAB / "starter/check_types.py", outside / "check_types.py")
        tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
        assert "47 passed" in tests.stdout, tests.stdout
        fixtures = checked([str(python), "-I", "check_types.py"], outside, env)
        assert "positive typed API and 10 rejected-call fixtures" in fixtures.stdout, fixtures.stdout
        quiet = checked([str(python), "-I", "-c", "import academy_typed_transforms"], outside, env)
        assert quiet.stdout == quiet.stderr == "", quiet
        imported = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_typed_transforms; assert files('academy_typed_transforms').joinpath('py.typed').is_file(); print(academy_typed_transforms.__file__)",
            ],
            outside,
            env,
        )
        assert Path(imported.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        demo = checked([str(python), "-I", "demo.py"], outside, env)
        assert (
            json.loads(demo.stdout)
            == {
                "count": 2,
                "total": 15,
                "first": "api",
                "events": ["started", "returned", "started", "returned"],
            }
            and demo.stderr == ""
        )
        (outside / "integration.py").write_text(INTEGRATION)
        checked([str(python), "-I", "-m", "mypy", "--strict", "integration.py"], outside, env)
        result = checked([str(python), "-I", "integration.py"], outside, env)
        assert result.stderr == "", result.stderr
        print(
            "PASS: three source/wheel builds, fresh install, pip check, 47 runtime cases, positive/10 negative checker fixtures, quiet import, typing marker, installed demo and strict-typed record/snapshot composition."
        )


if __name__ == "__main__":
    main()
