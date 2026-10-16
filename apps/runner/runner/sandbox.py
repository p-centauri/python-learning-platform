"""No learner code executes here. Docker commands are fixed argument vectors."""

import csv
from contextvars import ContextVar
import io
import json
import os
import selectors
import subprocess
import time
from uuid import uuid4

PYTHON_IMAGE = "python@sha256:2325bb286ec344af3e5898cc224b5844e2707ac6e26b1632516fd3edc84a5e26"
SQL_IMAGE = "postgres@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24"
PROFILE = "2026.09-runner-v1"
OUTPUT_LIMIT = 16384
JOB_SECONDS = 45
JOB_DEADLINE = ContextVar("runner_job_deadline", default=None)

# Expected answers never enter this interpreter. The outer service compares outputs.
PYTHON_DRIVER = """
import contextlib, json, sys
payload = json.loads(sys.stdin.read())
namespace = {"__name__": "learner"}
try:
    with contextlib.redirect_stdout(sys.stderr):
        exec(compile(payload["code"], "learner.py", "exec"), namespace)
        value = namespace[payload["function"]](*payload["args"])
    result = {"value": value, "input_after": payload["args"]}
except BaseException as error:
    result = {"error": type(error).__name__, "message": str(error)[:200]}
result["input_after"] = payload["args"]
sys.stdout.write(json.dumps(result, allow_nan=False))
"""


class SandboxFailure(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def command(args, *, data=b"", timeout=5, limit=OUTPUT_LIMIT, ignore_job_deadline=False):
    """Bound both pipes while running Docker; communicate() would buffer a flood."""
    deadline = time.monotonic() + timeout
    if not ignore_job_deadline and JOB_DEADLINE.get() is not None:
        deadline = min(deadline, JOB_DEADLINE.get())
    if deadline <= time.monotonic():
        raise SandboxFailure("timeout", "The submission exceeded its total time limit.")
    process = subprocess.Popen(
        ["docker", *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    output, errors = bytearray(), bytearray()
    with selectors.DefaultSelector() as selector:
        for stream, tag in [(process.stdout, "out"), (process.stderr, "err")]:
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, tag)
        if data:
            os.set_blocking(process.stdin.fileno(), False)
            selector.register(process.stdin, selectors.EVENT_WRITE, "in")
        else:
            process.stdin.close()
        offset = 0
        try:
            while selector.get_map():
                if time.monotonic() >= deadline:
                    raise SandboxFailure("timeout", "The execution exceeded its time limit.")
                for key, _ in selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                    if key.data == "in":
                        try:
                            offset += os.write(key.fd, data[offset : offset + 4096])
                        except BrokenPipeError:
                            offset = len(data)
                        if offset == len(data):
                            selector.unregister(key.fileobj)
                            key.fileobj.close()
                    else:
                        chunk = os.read(key.fd, 4096)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            key.fileobj.close()
                        else:
                            (output if key.data == "out" else errors).extend(chunk)
                            if len(output) + len(errors) > limit:
                                raise SandboxFailure(
                                    "output-limit",
                                    "Output exceeded the 16 KiB limit. Remove repeated debug printing.",
                                )
            try:
                returncode = process.wait(timeout=max(0.01, deadline - time.monotonic()))
            except subprocess.TimeoutExpired as error:
                raise SandboxFailure("timeout", "The execution exceeded its time limit.") from error
            return (
                returncode,
                output.decode("utf-8", errors="replace"),
                errors.decode("utf-8", errors="replace"),
            )
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()
            for stream in (process.stdin, process.stdout, process.stderr):
                if not stream.closed:
                    stream.close()


def checked(args, **kwargs):
    code, output, _ = command(args, **kwargs)
    if code:
        raise SandboxFailure("unavailable", "The isolated runner could not prepare its container.")
    return output


def flags(name, language):
    sql = language == "sql"
    memory = "256m" if sql else "128m"
    user = "70:70" if sql else "65532:65532"
    result = [
        "create",
        "--name",
        name,
        "--label",
        f"academy.runner={PROFILE}",
        "--label",
        f"academy.expires={int(time.time()) + JOB_SECONDS + 30}",
        "--pull=never",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--user",
        user,
        "--memory",
        memory,
        "--memory-swap",
        memory,
        "--cpus=0.5",
        "--pids-limit=32",
        "--ulimit",
        "nofile=256:256",
        "--ulimit",
        "core=0:0",
        "--log-driver=none",
        "--tmpfs",
        f"/tmp:rw,noexec,nosuid,nodev,size=8388608,uid={user.split(':')[0]},gid={user.split(':')[1]}",
    ]
    if sql:
        result += [
            "--tmpfs",
            "/var/lib/postgresql/data:rw,noexec,nosuid,nodev,size=201326592,uid=70,gid=70,mode=0700",
            "--tmpfs",
            "/var/run/postgresql:rw,noexec,nosuid,nodev,size=1048576,uid=70,gid=70",
            "-e",
            "POSTGRES_HOST_AUTH_METHOD=trust",
            "-e",
            "POSTGRES_DB=academy",
        ]
    else:
        result += ["--interactive", "--workdir=/tmp"]
    return result


def assert_profile(name, language):
    config = json.loads(checked(["inspect", name]))[0]
    host = config["HostConfig"]
    sql = language == "sql"
    memory = (256 if sql else 128) * 1024 * 1024
    allowed = {"/tmp", "/var/lib/postgresql/data", "/var/run/postgresql"} if sql else {"/tmp"}
    if not (
        host["NetworkMode"] == "none"
        and host["ReadonlyRootfs"]
        and host["CapDrop"] == ["ALL"]
        and "no-new-privileges" in host["SecurityOpt"]
        and host["Memory"] == memory
        and host["MemorySwap"] == memory
        and host["NanoCpus"] == 500000000
        and host["PidsLimit"] == 32
        and config["Config"]["User"] == ("70:70" if sql else "65532:65532")
        and not host["Privileged"]
        and not host.get("Binds")
        and not host.get("Devices")
        and not host.get("PortBindings")
        and set(host["Tmpfs"]) == allowed
        and host["LogConfig"]["Type"] == "none"
        and not config.get("Mounts")
    ):
        raise SandboxFailure("unavailable", "Container isolation configuration did not pass verification.")


class Container:
    def __init__(self, language, argv=None):
        self.language = language
        self.name = "academy-exec-" + uuid4().hex
        self.argv = argv

    def __enter__(self):
        try:
            image = SQL_IMAGE if self.language == "sql" else PYTHON_IMAGE
            argv = self.argv or (
                [
                    "postgres",
                    "-c",
                    "shared_buffers=8MB",
                    "-c",
                    "max_connections=8",
                    "-c",
                    "listen_addresses=",
                    "-c",
                    "unix_socket_directories=/var/run/postgresql",
                ]
                if self.language == "sql"
                else ["python", "-I", "-B", "-c", PYTHON_DRIVER]
            )
            checked([*flags(self.name, self.language), image, *argv])
            assert_profile(self.name, self.language)
            return self
        except BaseException:
            self.cleanup()
            raise

    def cleanup(self):
        try:
            checked(["rm", "--force", self.name], timeout=5, ignore_job_deadline=True)
        except SandboxFailure:
            # Fail closed: a worker whose cleanup failed must be restarted/verified.
            raise SandboxFailure(
                "cleanup-failed", "Container cleanup failed; the runner is disabled until it is restarted."
            )

    def __exit__(self, *args):
        self.cleanup()


def python_case(code, definition, test):
    payload = json.dumps({"code": code, "function": definition["function"], "args": test["args"]}).encode()
    with Container("python") as box:
        exit_code, output, errors = command(
            ["start", "--attach", "--interactive", box.name], data=payload, timeout=4
        )
    if exit_code:
        return {
            "status": "error",
            "message": errors[-600:]
            or "The interpreter exited unexpectedly. Check syntax, memory use and return values.",
        }
    try:
        actual = json.loads(output)
        if not isinstance(actual, dict):
            raise ValueError()
        input_unchanged = json.dumps(
            actual.get("input_after"), sort_keys=True, allow_nan=False
        ) == json.dumps(test["args"], sort_keys=True, allow_nan=False)
        if "error" in test:
            passed = actual.get("error") == test["error"] and input_unchanged
        else:
            passed = (
                "value" in actual
                and json.dumps(actual["value"], sort_keys=True, allow_nan=False)
                == json.dumps(test["expected"], sort_keys=True, allow_nan=False)
                and input_unchanged
            )
        return {
            "status": "passed" if passed else "failed",
            "actual": actual.get("value", actual.get("error", "Invalid result")),
            "message": actual.get("message", ""),
        }
    except (ValueError, TypeError):
        return {
            "status": "error",
            "message": "Return a JSON-compatible value. Direct stdout writes can corrupt the result protocol.",
        }


def sql_case(code, test):
    with Container("sql") as box:
        checked(["start", box.name])
        deadline = time.monotonic() + 12
        while True:
            _, process_name, _ = command(["exec", box.name, "cat", "/proc/1/comm"], timeout=2)
            returncode, _, _ = command(
                ["exec", box.name, "pg_isready", "-h", "/var/run/postgresql", "-U", "postgres"], timeout=2
            )
            if returncode == 0 and process_name.strip() == "postgres":
                break
            if time.monotonic() >= deadline:
                raise SandboxFailure("unavailable", "The isolated PostgreSQL database did not start.")
            time.sleep(0.1)
        setup = (
            """
CREATE ROLE learner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
REVOKE ALL ON DATABASE academy FROM PUBLIC;
GRANT CONNECT ON DATABASE academy TO learner;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
"""
            + test["setup_sql"]
            + """
GRANT USAGE ON SCHEMA public TO learner;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO learner;
ALTER ROLE learner SET default_transaction_read_only=on;
ALTER ROLE learner SET statement_timeout='1500ms';
ALTER ROLE learner SET lock_timeout='500ms';
ALTER ROLE learner SET idle_in_transaction_session_timeout='1000ms';
"""
        )
        checked(
            [
                "exec",
                "-i",
                box.name,
                "psql",
                "-X",
                "-q",
                "-v",
                "ON_ERROR_STOP=1",
                "-h",
                "/var/run/postgresql",
                "-U",
                "postgres",
                "-d",
                "academy",
            ],
            data=setup.encode(),
            timeout=5,
        )
        query = "COPY (\n" + code.strip().rstrip(";") + "\n) TO STDOUT WITH (FORMAT csv, HEADER true);"
        exit_code, output, errors = command(
            [
                "exec",
                box.name,
                "psql",
                "-X",
                "-q",
                "-v",
                "ON_ERROR_STOP=1",
                "-h",
                "/var/run/postgresql",
                "-U",
                "learner",
                "-d",
                "academy",
                "-c",
                query,
            ],
            timeout=4,
        )
    if exit_code:
        return {"status": "error", "message": errors[-600:] or "The SQL process exited unexpectedly."}
    rows = list(csv.reader(io.StringIO(output)))
    passed = rows == [test["columns"], *test["expected"]]
    return {"status": "passed" if passed else "failed", "actual": rows, "message": ""}


def execute(code, definition):
    token = JOB_DEADLINE.set(time.monotonic() + JOB_SECONDS)
    try:
        return execute_checks(code, definition)
    finally:
        JOB_DEADLINE.reset(token)


def execute_checks(code, definition):
    started = time.monotonic()
    results = []
    for index, test in enumerate(definition["tests"]):
        try:
            if time.monotonic() - started >= JOB_SECONDS:
                raise SandboxFailure("timeout", "The submission exceeded its total time limit.")
            result = (
                python_case(code, definition, test)
                if definition["language"] == "python"
                else sql_case(code, test)
            )
        except SandboxFailure as error:
            if error.status in {"unavailable", "cleanup-failed"}:
                raise
            result = {"status": error.status, "message": str(error)}
        # Private cases disclose only pass/fail/status, never input, expected or actual.
        results.append(
            {
                "name": test["name"] if test["public"] else f"Additional check {index + 1}",
                "public": test["public"],
                "status": result["status"],
                "actual": result.get("actual") if test["public"] else None,
                "message": result.get("message", "") if test["public"] else "",
            }
        )
        if result["status"] in {"timeout", "output-limit"}:
            break
    passed = sum(r["status"] == "passed" for r in results)
    return {
        "status": "passed" if passed == len(definition["tests"]) else "failed",
        "passed": passed,
        "total": len(definition["tests"]),
        "checks": results,
        "duration_ms": round((time.monotonic() - started) * 1000),
        "profile": PROFILE,
        "note": "Objective results for this fixed test suite. Passing is not a complete code review or certification.",
    }
