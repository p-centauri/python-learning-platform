"""Trusted installed resource ownership evidence, never a learner-code evaluator."""

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
LAB = ROOT / "content/projects/resource-scopes"
INTEGRATION = """from typing import assert_type
from academy_ingest import Record
from academy_feed_objects import FeedKey, Reading, Snapshot
from academy_typed_transforms import Row, decode_row, map_rows
from academy_resource_scopes import Resource, WeakRegistry, current_request, owned_resources, request_scope

events: list[str | None] = []
def first_record() -> Resource[Record]:
    return Resource(Record("api", 5), lambda: events.append(current_request()))
def second_record() -> Resource[Record]:
    return Resource(Record("worker", 10), lambda: events.append(current_request()))
with request_scope("adapter"):
    with owned_resources([first_record, second_record]) as records:
        assert_type(records, tuple[Record, ...])
        def to_row(record: Record) -> Row:
            return decode_row({"id": record.id, "value": record.value})
        rows = map_rows(records, to_row)
        assert_type(rows, tuple[Row, ...])
        snapshot = Snapshot(Reading(FeedKey("feed", row.id), row.value) for row in rows)
        registry = WeakRegistry[Row]()
        registry.store("first", rows[0])
        assert registry.get("first") is rows[0]
assert current_request() is None and events == ["adapter", "adapter"]
assert len(snapshot) == 2 and sum(row.value for row in snapshot) == 15
print("installed resource/record/transformation/snapshot adapter passed")
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-resources-") as directory:
        temporary = Path(directory)
        wheels = []
        for name, package, files in [
            ("ingestion-package", "academy_ingest", ["parser.py", "http.py"]),
            ("feed-objects", "academy_feed_objects", ["objects.py"]),
            ("typed-transforms", "academy_typed_transforms", ["transform.py"]),
            ("resource-scopes", "academy_resource_scopes", ["scopes.py"]),
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
        tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
        assert "54 passed" in tests.stdout, tests.stdout
        quiet = checked([str(python), "-I", "-c", "import academy_resource_scopes"], outside, env)
        assert quiet.stdout == quiet.stderr == "", quiet
        imported = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_resource_scopes; assert files('academy_resource_scopes').joinpath('py.typed').is_file(); print(academy_resource_scopes.__file__)",
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
                "label": "demo",
                "restored": None,
                "events": ["open:a", "open:b", "close:b", "close:a", "open:async", "close:async"],
            }
            and demo.stderr == ""
        )
        (outside / "integration.py").write_text(INTEGRATION)
        checked([str(python), "-I", "-m", "mypy", "--strict", "integration.py"], outside, env)
        result = checked([str(python), "-I", "integration.py"], outside, env)
        assert result.stderr == "", result.stderr
        print(
            "PASS: four source/wheel builds, fresh install, pip check, 54 resource cases, quiet import, typing marker, installed demo and strict-typed prior-value composition."
        )


if __name__ == "__main__":
    main()
