"""Trusted installed measurement/cache evidence, never a learner-code evaluator."""

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
LAB = ROOT / "content/projects/measured-cache"
INTEGRATION = """from typing import Literal, assert_type
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory
from academy_ingest import Record
from academy_feed_objects import FeedKey, Reading, Snapshot
from academy_typed_transforms import Row, decode_row, map_rows
from academy_resource_scopes import Resource, current_request, owned_resources, request_scope
from academy_bounded_offload import Job, Outcome, run_batch
from academy_measured_cache import CacheKey, LruCache, Measurement, legacy_get, sample

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
                cache = LruCache[Row](2)
                key = CacheKey("adapter", rows[0].id)
                def first() -> Row:
                    return cache.get_or_compute(key, lambda: rows[0])
                measured = sample(first)
                assert_type(measured, Measurement[Row])
                assert measured.last is rows[0] and len(measured.elapsed_ns) == 3
                assert cache.info().hits == 2 and cache.info().misses == 1
                with warnings.catch_warnings(record=True) as observed:
                    warnings.simplefilter("always", DeprecationWarning)
                    old = legacy_get(cache, key, lambda: rows[1])
                    assert_type(old, Row)
                assert old is rows[0] and len(observed) == 1
                assert Path(observed[0].filename).name == "integration.py"
                cache.clear()
                assert cache.info().size == 0
                records = tuple(Record(row.id, row.value) for row in rows)
                snapshot = Snapshot(Reading(FeedKey("feed", r.id), r.value) for r in records)
                assert len(snapshot) == 2 and sum(row.value for row in snapshot) == 15
                assert all(result.file_closed for result in outcomes)
    assert current_request() is None and events == ["adapter"]
    print("installed measurement/cache/offload/resource/record/transformation/snapshot adapter passed")

if __name__ == "__main__":
    main()
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-measurement-") as directory:
        temporary = Path(directory)
        wheels = []
        for name, package, files in [
            ("ingestion-package", "academy_ingest", ["parser.py", "http.py"]),
            ("feed-objects", "academy_feed_objects", ["objects.py"]),
            ("typed-transforms", "academy_typed_transforms", ["transform.py"]),
            ("resource-scopes", "academy_resource_scopes", ["scopes.py"]),
            ("bounded-offload", "academy_bounded_offload", ["offload.py"]),
            ("measured-cache", "academy_measured_cache", ["measurement.py", "cache.py"]),
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
        assert "61 passed" in tests.stdout, tests.stdout
        quiet = checked([str(python), "-I", "-c", "import academy_measured_cache"], outside, env)
        assert quiet.stdout == quiet.stderr == "", quiet
        imported = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_measured_cache; assert files('academy_measured_cache').joinpath('py.typed').is_file(); print(academy_measured_cache.__file__)",
            ],
            outside,
            env,
        )
        assert Path(imported.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        demo = checked([str(python), "-I", "demo.py"], outside, env)
        report = json.loads(demo.stdout)
        assert report["schema"] == "2026.10-measurement-v1"
        assert report["workload_items"] == report["baseline_computations"] == 32
        assert report["cached_computations"] == 4 and report["cached_hits"] == 28
        assert report["cache_state"] == "fresh per repetition"
        assert report["profile_functions"] > 0 and "function calls" in report["profile_text"]
        for samples in report["timings_ns"].values():
            assert len(samples) == 3 and all(type(n) is int and n >= 0 for n in samples)
        assert set(report["memory_traced_bytes"]) == {"before", "filled", "after_clear", "peak"}
        assert all(type(n) is int for n in report["memory_traced_bytes"].values())
        assert demo.stderr == ""
        if args.report_output:
            args.report_output.write_text(json.dumps(report, indent=2) + "\n")
            assert json.loads(args.report_output.read_text()) == report
        (outside / "integration.py").write_text(INTEGRATION)
        checked([str(python), "-I", "-m", "mypy", "--strict", "integration.py"], outside, env)
        result = checked([str(python), "-I", "integration.py"], outside, env)
        assert result.stderr == "", result.stderr
        print(
            "PASS: six source/wheel builds, fresh install, pip check, 61 measurement/cache cases, quiet import, typing marker, actual timing/profile/memory demo and strict-typed compatible prior-value composition."
        )


if __name__ == "__main__":
    main()
