"""Trusted local release installation evidence; never run learner uploads."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import venv
from persistence_db import disposable_postgres
from stream_broker import disposable_broker
from verify_delivery_recovery import completed_sources
from verify_ingestion_package import checked

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "content/projects/delivery-release"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-release-artifacts-") as directory:
        area = Path(directory)
        sources = completed_sources(area)
        source = area / "delivery-release"
        shutil.copytree(LAB / "starter", source, ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"))
        shutil.copyfile(LAB / "reference/operations.py", source / "src/academy_delivery_release/operations.py")
        sources.append(source)
        wheels = []
        for package in sources:
            built = checked([sys.executable, "-m", "build", "--no-isolation"], package)
            assert "Building wheel from sdist" in built.stdout
            wheels.append(str(next((package / "dist").glob("*.whl"))))
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
        checked(install + wheels + ["pytest==9.0.3", "mypy==2.3.1", "types-psycopg2==2.9.21.20260911", "httpx==0.28.1"], outside, env)
        checked([str(python), "-m", "pip", "check"], outside, env)
        quiet = checked([str(python), "-I", "-c", "import academy_delivery_release; import academy_delivery_release.operate"], outside, env)
        assert quiet.stdout == quiet.stderr == ""
        probe = checked([str(python), "-I", "-c", "from importlib.resources import files; import academy_delivery_release; assert files('academy_delivery_release').joinpath('py.typed').is_file(); print(academy_delivery_release.__file__)"], outside, env)
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copytree(LAB / "starter/tests", outside / "tests")
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        checked([str(python), "-I", "-m", "mypy", "--strict", "-p", "academy_delivery_release"], outside, env)
        checked([str(python), "-I", "-m", "mypy", "--strict", "demo.py"], outside, env)
        with disposable_postgres() as dsn, disposable_broker() as (url, _):
            env["ACADEMY_RELEASE_TEST_DSN"], env["ACADEMY_BROKER_URL"] = dsn, url
            tests = checked([str(python), "-I", "-m", "pytest", "-q", "tests"], outside, env)
            assert "33 passed" in tests.stdout and "skipped" not in tests.stdout, tests.stdout
            print(tests.stdout, end="")
            demo = checked([str(python), "-I", "demo.py", "--output", "release.json"], outside, env)
            report = json.loads(demo.stdout)
            assert report == json.loads((outside / "release.json").read_text()) and not demo.stderr
            assert report["head"] == ["delivery_004"] and report["server_version"] // 10000 == 17
            assert report["readiness"] == dict(old=503, compatible=200, changed=503, alive=200, restored=200, draining=503, admission=503, restarted=200)
            assert report["permissions"] == dict(unauthorized=401, permitted=200)
            assert report["rollback"] == dict(refused=True, facts_unchanged=True, jobs_after=0, inbox_before=1, inbox_after=1)
            assert report["recovery"] == dict(generation=2, payload_removed=True) and report["checked_out_connections"] == 0
            if args.report_output:
                args.report_output.parent.mkdir(parents=True, exist_ok=True)
                args.report_output.write_text(json.dumps(report, indent=2) + "\n")
                assert json.loads(args.report_output.read_text()) == report
    print("PASS: eight source archives/wheels, clean install, public cases, actual compatible release/rollback/broker composition and loopback SIGTERM. Owned resources removed.")


if __name__ == "__main__":
    main()
