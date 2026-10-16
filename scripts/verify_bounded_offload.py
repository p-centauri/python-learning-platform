"""Trusted installed bounded offload evidence, never a learner-code evaluator."""

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
LAB = ROOT / "content/projects/bounded-offload"
INTEGRATION = """from typing import Literal, assert_type
from pathlib import Path
from tempfile import TemporaryDirectory
from academy_ingest import Record
from academy_feed_objects import FeedKey, Reading, Snapshot
from academy_typed_transforms import Row, decode_row, map_rows
from academy_resource_scopes import Resource, current_request, owned_resources, request_scope
from academy_bounded_offload import Job, Outcome, run_batch

def main() -> None:
    events: list[str | None] = []
    def create_jobs() -> Resource[tuple[Job, ...]]:
        directory = TemporaryDirectory()
        try:
            jobs: list[Job] = []
            for name, value in [("api", 5), ("worker", 10)]:
                path = Path(directory.name) / name
                path.write_bytes(str(value).encode("ascii") + b"\\n")
                jobs.append(Job(name, str(path)))
            def close() -> None:
                events.append(current_request())
                directory.cleanup()
            return Resource(tuple(jobs), close)
        except BaseException:
            directory.cleanup()
            raise
    with request_scope("adapter"):
        with owned_resources([create_jobs]) as batches:
            assert_type(batches, tuple[tuple[Job, ...], ...])
            modes: tuple[Literal["thread", "process"], ...] = ("thread", "process")
            for mode in modes:
                outcomes = run_batch(batches[0], mode=mode)
                assert_type(outcomes, tuple[Outcome, ...])
                def to_row(outcome: Outcome) -> Row:
                    return decode_row({"id": outcome.id, "value": outcome.value})
                rows = map_rows(outcomes, to_row)
                assert_type(rows, tuple[Row, ...])
                records = tuple(Record(row.id, row.value) for row in rows)
                snapshot = Snapshot(Reading(FeedKey("feed", r.id), r.value) for r in records)
                assert len(snapshot) == 2 and sum(row.value for row in snapshot) == 15
                assert all(result.file_closed for result in outcomes)
    assert current_request() is None and events == ["adapter"]
    print("installed offload/resource/record/transformation/snapshot adapter passed")

if __name__ == "__main__":
    main()
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-offload-") as directory:
        temporary = Path(directory)
        wheels = []
        for name, package, files in [
            ("ingestion-package", "academy_ingest", ["parser.py", "http.py"]),
            ("feed-objects", "academy_feed_objects", ["objects.py"]),
            ("typed-transforms", "academy_typed_transforms", ["transform.py"]),
            ("resource-scopes", "academy_resource_scopes", ["scopes.py"]),
            ("bounded-offload", "academy_bounded_offload", ["offload.py"]),
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
        assert "66 passed" in tests.stdout, tests.stdout
        quiet = checked([str(python), "-I", "-c", "import academy_bounded_offload"], outside, env)
        assert quiet.stdout == quiet.stderr == "", quiet
        imported = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_bounded_offload; assert files('academy_bounded_offload').joinpath('py.typed').is_file(); print(academy_bounded_offload.__file__)",
            ],
            outside,
            env,
        )
        assert Path(imported.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        demo = checked([str(python), "-I", "demo.py"], outside, env)
        report = json.loads(demo.stdout)
        assert report["thread_total"] == report["process_total"] == 15
        assert report["worker_files_closed"] is True and report["process_boundary"] is True
        assert type(report["free_threaded_build"]) is bool
        assert type(report["gil_enabled"]) is bool or report["gil_enabled"] == "unavailable"
        assert demo.stderr == ""
        (outside / "integration.py").write_text(INTEGRATION)
        checked([str(python), "-I", "-m", "mypy", "--strict", "integration.py"], outside, env)
        result = checked([str(python), "-I", "integration.py"], outside, env)
        assert result.stderr == "", result.stderr
        print(
            "PASS: five source/wheel builds, fresh install, pip check, 66 offload cases, quiet import, typing marker, guarded spawned-process demo and strict-typed prior-value composition."
        )


if __name__ == "__main__":
    main()
