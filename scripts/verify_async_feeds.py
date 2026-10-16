"""Trusted reference installation/composition, never a learner-code evaluator.

Needs index access unless --wheelhouse supplies every dependency.
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
LAB = ROOT / "content/projects/async-feeds"
INTEGRATION = """import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import aclosing, asynccontextmanager
import httpx
from academy_async_feeds import BatchReport, Record, Source, ingest, open_feed
from academy_feed_policy import make_selector

closed: list[bool] = []
class Stream(httpx.AsyncByteStream):
    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield b'{"id":"api-fast","value":5}\\n{"id":"api-slow","value":20}\\n'
        yield b'{"id":"worker","value":30}\\n'
    async def aclose(self) -> None:
        closed.append(True)

async def main() -> BatchReport:
    selector = make_selector(prefix="api", minimum=10)
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Content-Type":"application/x-ndjson"}, stream=Stream())
    async def selected(rows: AsyncIterator[Record]) -> AsyncGenerator[Record, None]:
        async for row in rows:
            if selector(row):
                yield row
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        @asynccontextmanager
        async def configured(source: Source, /) -> AsyncIterator[AsyncIterator[Record]]:
            async with open_feed(source, client=client) as rows, aclosing(selected(rows)) as filtered:
                yield filtered
        result = await ingest([
            Source("a", "https://example.test/a"), Source("b", "https://example.test/b"),
        ], opener=configured, workers=2, queue_size=1)
        assert result == {"sources":2,"count":2,"total":40}
        assert closed == [True, True] and not client.is_closed
        return result

assert asyncio.run(main()) == {"sources":2,"count":2,"total":40}
print("installed async policy composition passed")
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="academy-async-") as directory:
        temporary = Path(directory)
        wheels = []
        for name, package, files in [
            ("feed-policy", "academy_feed_policy", ["policy.py"]),
            ("async-feeds", "academy_async_feeds", ["parser.py", "http.py", "worker.py"]),
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
        assert "75 passed" in tests.stdout, tests.stdout
        quiet = checked([str(python), "-I", "-c", "import academy_async_feeds"], outside, env)
        assert quiet.stdout == quiet.stderr == "", quiet
        imported = checked(
            [
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; import academy_async_feeds; assert files('academy_async_feeds').joinpath('py.typed').is_file(); print(academy_async_feeds.__file__)",
            ],
            outside,
            env,
        )
        assert Path(imported.stdout.strip()).resolve().is_relative_to(environment.resolve())
        shutil.copyfile(LAB / "starter/demo.py", outside / "demo.py")
        demo = checked([str(python), "-I", "demo.py"], outside, env)
        assert json.loads(demo.stdout) == {"sources": 2, "count": 4, "total": 30} and demo.stderr == ""
        (outside / "integration.py").write_text(INTEGRATION)
        checked(
            [sys.executable, "-m", "mypy", "--strict", "integration.py"],
            outside,
            {
                **env,
                "MYPYPATH": os.pathsep.join(
                    str(temporary / name / "src") for name in ["async-feeds", "feed-policy"]
                ),
            },
        )
        result = checked([str(python), "-I", "integration.py"], outside, env)
        assert result.stderr == "", result.stderr
        print(
            "PASS: source/wheel builds, fresh install, pip check, 75 pytest cases, quiet import, typing marker, installed demo and strict-typed offline async policy composition."
        )


if __name__ == "__main__":
    main()
