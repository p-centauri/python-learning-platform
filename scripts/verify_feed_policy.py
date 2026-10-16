"""Install trusted reference wheels and exercise their offline composition.

Maintainer check only: never execute learner uploads. Index access is needed
unless --wheelhouse contains all dependencies.
"""

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
LAB = ROOT / "content/projects/feed-policy"
INTEGRATION = """from collections.abc import Iterable, Iterator
import logging
import httpx
from academy_ingest import Record, open_feed, summarize
from academy_feed_policy import Reading, Report, apply_policy, logged_report, make_selector

closed: list[bool] = []
class Chunks(httpx.SyncByteStream):
    def __iter__(self) -> Iterator[bytes]:
        yield b'{"id":"api-fast","value":5}\\n{"id":"api-slow","value":20}\\n'
        yield b'{"id":"worker","value":30}\\n'
    def close(self) -> None:
        closed.append(True)

def transport(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, headers={"Content-Type": "application/x-ndjson"}, stream=Chunks())

def report(records: Iterable[Reading], /) -> Report:
    # The immutable prior Record satisfies the read-only protocol. This adapter
    # narrows the older dict annotation to the exact new Report return shape.
    result = summarize(Record(record.id, record.value) for record in records)
    return {"count": result["count"], "total": result["total"]}

with httpx.Client(transport=httpx.MockTransport(transport)) as client:
    with open_feed("https://example.test/feed", client=client) as rows:
        wrapped = logged_report(report, logger=logging.getLogger("integration"), source_id="feed")
        result = apply_policy(rows, selector=make_selector(prefix="api", minimum=10), reporter=wrapped)
        assert result == {"count": 1, "total": 20}
    assert closed == [True] and not client.is_closed
print("installed offline composition passed")
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-policy-") as directory:
        temporary = Path(directory)
        wheels = []
        for name, package, replacements in [
            ("ingestion-package", "academy_ingest", ["parser.py", "http.py"]),
            ("feed-policy", "academy_feed_policy", ["policy.py"]),
        ]:
            lab = ROOT / "content/projects" / name
            source = temporary / name
            shutil.copytree(
                lab / "starter", source, ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache")
            )
            for filename in replacements:
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
        assert "49 passed" in tests.stdout, tests.stdout
        probe = checked([str(python), "-I", "-c", "import academy_feed_policy"], outside, env)
        assert probe.stdout == probe.stderr == "", probe
        probe = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_feed_policy; assert files('academy_feed_policy').joinpath('py.typed').is_file(); print(academy_feed_policy.__file__)",
            ],
            outside,
            env,
        )
        assert Path(probe.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        demo = checked([str(python), "-I", "demo.py"], outside, env)
        assert json.loads(demo.stdout) == {"count": 1, "total": 20} and demo.stderr == ""
        (outside / "integration.py").write_text(INTEGRATION)
        checked(
            [sys.executable, "-m", "mypy", "--strict", "integration.py"],
            outside,
            {
                **env,
                "MYPYPATH": os.pathsep.join(
                    str(temporary / name / "src") for name in ["ingestion-package", "feed-policy"]
                ),
            },
        )
        checked([str(python), "-I", "integration.py"], outside, env)
        print(
            "PASS: source/wheel builds, fresh install, pip check, 49 pytest cases, quiet import, typing marker, demo and offline installed ingestion composition."
        )


if __name__ == "__main__":
    main()
