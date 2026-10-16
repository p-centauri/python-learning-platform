"""Trusted installed HTTP rehearsal only; never evaluate learner uploads."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import venv
from persistence_db import disposable_postgres
from verify_delivery_recovery import completed_sources as prior_sources
from verify_ingestion_package import checked

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "content/projects/api-depth"


def completed_sources(area):
    roots = prior_sources(area)
    for name, package in [
        ("delivery-release", "academy_delivery_release"),
        ("api-depth", "academy_api_depth"),
    ]:
        source = area / name
        lab = ROOT / "content/projects" / name
        shutil.copytree(
            lab / "starter",
            source,
            ignore=shutil.ignore_patterns(
                "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "*.egg-info"
            ),
        )
        shutil.copyfile(lab / "reference/operations.py", source / "src" / package / "operations.py")
        roots.append(source)
    return roots


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-api-artifacts-") as directory:
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
            install
            + wheels
            + ["httpx==0.28.1", "pytest==9.0.3", "mypy==2.3.1", "types-psycopg2==2.9.21.20260911"],
            outside,
            env,
        )
        checked([str(python), "-m", "pip", "check"], outside, env)
        quiet = checked([str(python), "-I", "-c", "import academy_api_depth"], outside, env)
        assert quiet.stdout == quiet.stderr == ""
        probe = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_api_depth; assert files('academy_api_depth').joinpath('py.typed').is_file(); print(academy_api_depth.__file__)",
            ],
            outside,
            env,
        )
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        checked([str(python), "-I", "-m", "mypy", "--strict", "-p", "academy_api_depth"], outside, env)
        checked([str(python), "-I", "-m", "mypy", "--strict", "demo.py"], outside, env)
        with disposable_postgres() as dsn:
            env["ACADEMY_API_TEST_DSN"] = dsn
            tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
            assert "51 passed" in tests.stdout and "skipped" not in tests.stdout, tests.stdout
            print(tests.stdout, end="")
            demo = checked([str(python), "-I", "demo.py", "--output", "api.json"], outside, env)
            report = json.loads(demo.stdout)
            assert report == json.loads((outside / "api.json").read_text()) and not demo.stderr
            assert report["head"] == ["delivery_004"] and report["server_version"] // 10000 == 17
            assert report["cache"] == dict(
                first=200,
                conditional=304,
                empty_304=True,
                changed=200,
                changed_tag=True,
                policy="private, no-cache",
                vary="Authorization",
            )
            assert report["permission"] == dict(unauthenticated=401, forbidden=403, no_error_tag=True)
            assert report["webhooks"] == dict(
                competing=[[200, False], [200, True]],
                tamper=401,
                conflict=409,
                stale=401,
                invalid=422,
                blocked=503,
                recovered=200,
                receipts=2,
                facts=1,
                outbox=0,
            )
            assert report["compatibility"] == dict(ready=200, old_read=200, old_policy="no-store")
            assert report["checked_out"] == 0 and report["transport"] == "actual loopback TCP"
            if args.report_output:
                args.report_output.parent.mkdir(parents=True, exist_ok=True)
                args.report_output.write_text(json.dumps(report, indent=2) + "\n")
                assert json.loads(args.report_output.read_text()) == report
    print(
        "PASS: nine source/wheel artifacts, clean installed types/imports, 51 public cases, actual loopback cache/permission/signature/duplicate/rollback evidence. Owned resources removed."
    )


if __name__ == "__main__":
    main()
