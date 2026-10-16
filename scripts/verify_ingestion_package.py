"""Maintainer-only wheel installation check in a fresh environment.

Runs trusted authored reference code. Never use this to evaluate user uploads.
Dependency installation needs a configured package index unless --wheelhouse is set.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "content/projects/ingestion-package"


def checked(command, directory, env=None):
    result = subprocess.run(command, cwd=directory, env=env, capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path, help="Install dependencies offline from this directory")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-wheel-") as directory:
        temporary = Path(directory)
        source = temporary / "source"
        shutil.copytree(LAB / "starter", source, ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache"))
        for name in ["parser.py", "http.py"]:
            shutil.copyfile(LAB / "reference" / name, source / "src/academy_ingest" / name)
        checked([sys.executable, "-m", "build", "--no-isolation"], source)
        wheel = next((source / "dist").glob("*.whl"))
        environment = temporary / "installed"
        venv.EnvBuilder(with_pip=True).create(environment)
        executable_dir = environment / ("Scripts" if os.name == "nt" else "bin")
        python = executable_dir / ("python.exe" if os.name == "nt" else "python")
        install = [str(python), "-m", "pip", "install"]
        if args.wheelhouse:
            install += ["--no-index", "--find-links", str(args.wheelhouse.resolve())]
        install += [str(wheel)]
        outside = temporary / "outside"
        outside.mkdir()
        clean_env = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "PYTHONHOME"}}
        checked(install, outside, clean_env)
        checked([str(python), "-m", "pip", "check"], outside, clean_env)
        shutil.copytree(source / "tests", outside / "tests")
        tests = checked(
            [str(python), "-I", "-m", "unittest", "discover", "-s", "tests", "-v"], outside, clean_env
        )
        assert "Ran 28 tests" in tests.stderr, tests.stderr
        probe = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_ingest; print(academy_ingest.__file__); assert files('academy_ingest').joinpath('defaults.json').is_file(); assert files('academy_ingest').joinpath('py.typed').is_file()",
            ],
            outside,
            clean_env,
        )
        imported = Path(probe.stdout.strip()).resolve()
        assert imported.is_relative_to(environment.resolve()), imported
        for command in [
            [str(python), "-I", "-m", "academy_ingest", "--demo"],
            [str(executable_dir / ("academy-ingest.exe" if os.name == "nt" else "academy-ingest")), "--demo"],
        ]:
            result = checked(command, outside, clean_env)
            assert json.loads(result.stdout) == {"count": 2, "total": 15}
            assert result.stderr == "", result.stderr
        print(
            "PASS: sdist/wheel build, clean dependency installation, pip check, 28 offline tests, resources and both commands outside source."
        )


if __name__ == "__main__":
    main()
