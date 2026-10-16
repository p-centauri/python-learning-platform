"""Trusted composed practical evidence only; never evaluate learner uploads."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import venv
from persistence_db import disposable_postgres
from verify_ingestion_package import checked

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "content/projects/practical-review"
PACKAGES = [
    ("ingestion-package", "academy_ingest", ["parser.py", "http.py"]),
    ("feed-objects", "academy_feed_objects", ["objects.py"]),
    ("typed-transforms", "academy_typed_transforms", ["transform.py"]),
    ("resource-scopes", "academy_resource_scopes", ["scopes.py"]),
    ("bounded-offload", "academy_bounded_offload", ["offload.py"]),
    ("measured-cache", "academy_measured_cache", ["measurement.py", "cache.py"]),
    ("ingestion-service", "academy_ingestion_service", ["auth.py", "service.py"]),
    ("practical-review", "academy_practical_review", ["operations.py"]),
]


def completed_sources(area):
    roots = []
    for name, package, references in PACKAGES:
        source = area / name
        lab = ROOT / "content/projects" / name
        shutil.copytree(
            lab / "starter",
            source,
            ignore=shutil.ignore_patterns(
                "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "*.egg-info"
            ),
        )
        for filename in references:
            shutil.copyfile(lab / "reference" / filename, source / "src" / package / filename)
        roots.append(source)
    return roots


def maintainer_case():
    old = [dict(id="case-" + str(i).zfill(2), revision=1, value=100 + i) for i in range(10)]
    latest = [
        dict(id="case-" + str(i).zfill(2), revision=8, value=0 if i % 3 == 0 else i * 7) for i in range(10)
    ]
    return dict(
        case_id="assessor-eviction-zero-gap",
        namespace="review-case",
        purpose="Maintainer rehearsal: ten distinct latest revisions exceed the eight-entry cache; zero, gaps and one equal duplicate preserve outputs. This is not a learner-authored originality claim.",
        rows=[*old, *reversed(latest), old[0]],
        requests=[*range(10), 0, 1],
        expected_latest=latest,
        expected_computations=dict(baseline=12, cached=12),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-practical-artifacts-") as directory:
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
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"PYTHONPATH", "PYTHONHOME", "MYPYPATH"} and not key.startswith("ACADEMY_")
        }
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        install = [str(python), "-m", "pip", "install"]
        if args.wheelhouse:
            install += ["--no-index", "--find-links", str(args.wheelhouse.resolve())]
        checked(
            install + wheels + ["pytest==9.0.3", "mypy==2.3.1", "types-psycopg2==2.9.21.20260911"],
            outside,
            env,
        )
        checked([str(python), "-m", "pip", "check"], outside, env)
        quiet = checked([str(python), "-I", "-c", "import academy_practical_review"], outside, env)
        assert quiet.stdout == quiet.stderr == ""
        probe = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_practical_review; assert files('academy_practical_review').joinpath('py.typed').is_file(); print(academy_practical_review.__file__)",
            ],
            outside,
            env,
        )
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        checked([str(python), "-I", "-m", "mypy", "--strict", "-p", "academy_practical_review"], outside, env)
        checked([str(python), "-I", "-m", "mypy", "--strict", "demo.py"], outside, env)
        case = maintainer_case()
        (outside / "review-case.json").write_text(json.dumps(case, indent=2) + "\n")
        with disposable_postgres() as dsn:
            env["ACADEMY_PRACTICAL_DSN"] = dsn
            tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
            assert "50 passed" in tests.stdout and "skipped" not in tests.stdout, tests.stdout
            print(tests.stdout, end="")
            demo = checked(
                [str(python), "-I", "demo.py", "--output", "practical.json", "--case", "review-case.json"],
                outside,
                env,
            )
            report = json.loads(demo.stdout)
            assert report == json.loads((outside / "practical.json").read_text()) and not demo.stderr
            assert (
                report["head"] == "service_002"
                and report["server_version"] // 10000 == 17
                and report["checked_out"] == 0
            )
            assert report["workload"] == dict(
                source_rows=128,
                ids=32,
                revisions=4,
                selected_latest=32,
                requests=152,
                hot_ids=8,
                hot_repeats=16,
                cold_requests=24,
            )
            assert report["service"] == dict(
                inserted=[dict(observed=64, inserted=64, duplicates=0)] * 2,
                duplicate=dict(observed=1, inserted=0, duplicates=1),
                conflict=409,
                missing=401,
                forbidden=403,
                ready=200,
                read_pages=4,
                responses_closed=True,
                facts_unchanged=True,
            )
            for key, baseline, cached, hits in [("measured", 152, 32, 120), ("cyclic", 64, 64, 0)]:
                measured = report[key]
                assert (
                    measured["equivalent"]
                    and measured["baseline_computations"] == baseline
                    and measured["cached_computations"] == cached
                    and measured["cached_hits"] == hits
                )
                assert (
                    measured["profiles"]["baseline"]["fingerprint_calls"] == baseline
                    and measured["profiles"]["cached"]["fingerprint_calls"] == cached
                )
                assert all(
                    len(samples) == 3 and all(type(n) is int and n >= 0 for n in samples)
                    for samples in measured["timings_ns"].values()
                )
                assert all(
                    observed["peak"] >= observed["retained"] >= 0
                    for observed in measured["traced_python_bytes"].values()
                )
            worker = report["workers"]
            assert (
                worker["jobs"] == 8
                and worker["equivalent"]
                and worker["files_closed"]
                and worker["context_restored"]
                and worker["directories_removed"] == [True]
            )
            assert (
                worker["cleanup_labels"] == ["review-jobs"]
                and worker["spawn_pids"]
                and not set(worker["spawn_pids"]) & set(worker["thread_pids"])
            )
            assert report["compatibility"] == dict(
                legacy_same_object=True, legacy_warnings=1, cache_cleared=True
            )
            assert (
                report["reviewer_case"]["equivalent"]
                and report["reviewer_case"]["originality"] == "requires manual review"
            )
            if args.report_output:
                args.report_output.parent.mkdir(parents=True, exist_ok=True)
                args.report_output.write_text(json.dumps(report, indent=2) + "\n")
                args.report_output.with_name("maintainer-review-case.json").write_text(
                    json.dumps(case, indent=2) + "\n"
                )
                assert json.loads(args.report_output.read_text()) == report
    print(
        "PASS: eight source/wheel artifacts, clean installed types/imports, 50 public cases, actual PostgreSQL/loopback async reads/thread/spawn/compatible profiles and manual-review case. Owned resources removed."
    )


if __name__ == "__main__":
    main()
