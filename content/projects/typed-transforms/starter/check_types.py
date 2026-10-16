"""Finite public checker fixtures; inspects source, never executes fixture code."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-path", type=Path, help="Source package directory for local development")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    env = {k: v for k, v in os.environ.items() if k not in {"MYPYPATH", "PYTHONPATH", "PYTHONHOME"}}
    if args.package_path:
        env["MYPYPATH"] = str(args.package_path.resolve())
    command = [
        sys.executable,
        "-m",
        "mypy",
        "--strict",
        "--no-incremental",
        "--show-error-codes",
        "--no-pretty",
        "--no-color-output",
    ]
    with tempfile.TemporaryDirectory(prefix="academy-type-cases-") as directory:
        temporary = Path(directory)
        positive = subprocess.run(
            command + [str(root / "typing/positive.py")],
            cwd=temporary,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if positive.returncode:
            raise AssertionError(positive.stdout + positive.stderr)
        cases = json.loads((root / "typing/negative.json").read_text())
        for case in cases:
            source = temporary / (case["id"] + ".py")
            source.write_text(case["code"])
            result = subprocess.run(
                command + [str(source)], cwd=temporary, env=env, capture_output=True, text=True, timeout=30
            )
            errors = [line for line in result.stdout.splitlines() if ": error:" in line]
            codes = [re.search(r"\[([a-z-]+)\]$", line) for line in errors]
            if (
                result.returncode != 1
                or len(codes) != 1
                or codes[0] is None
                or codes[0].group(1) != case["error_code"]
            ):
                raise AssertionError(case["id"] + ":\n" + result.stdout + result.stderr)
        print(f"PASS: positive typed API and {len(cases)} rejected-call fixtures")


if __name__ == "__main__":
    main()
