"""Owned disposable database for trusted maintainer checks; never learner execution."""

from contextlib import contextmanager
import json
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
import uuid

IMAGE = "postgres@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24"


def docker(*args):
    result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=60)
    if result.returncode:
        # No configured DSN/password appears in these commands or diagnostics.
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


@contextmanager
def disposable_postgres():
    name = "academy-persistence-" + uuid.uuid4().hex
    network = name + "-net"
    docker("image", "inspect", IMAGE)
    with tempfile.TemporaryDirectory(prefix="academy-pg-env-") as directory:
        environment = Path(directory) / "postgres.env"
        password = secrets.token_hex(24)
        environment.write_text(f"POSTGRES_PASSWORD={password}\nPOSTGRES_USER=lab\nPOSTGRES_DB=disposable\n")
        environment.chmod(0o600)
        created = False
        docker("network", "create", network)
        try:
            docker(
                "create",
                "--name",
                name,
                "--network",
                network,
                "--publish",
                "127.0.0.1::5432",
                "--env-file",
                str(environment),
                "--memory",
                "256m",
                "--cpus",
                "1",
                "--pids-limit",
                "128",
                "--tmpfs",
                "/var/lib/postgresql/data:rw,size=128m",
                IMAGE,
            )
            created = True
            docker("start", name)
            for _ in range(100):
                ready = subprocess.run(
                    [
                        "docker",
                        "exec",
                        name,
                        "pg_isready",
                        "-h",
                        "127.0.0.1",
                        "-U",
                        "lab",
                        "-d",
                        "disposable",
                    ],
                    capture_output=True,
                    timeout=10,
                )
                if ready.returncode == 0:
                    break
                time.sleep(0.2)
            else:
                raise RuntimeError("disposable PostgreSQL did not become ready")
            bindings = json.loads(docker("inspect", "--format", "{{json .NetworkSettings.Ports}}", name))
            port = bindings["5432/tcp"][0]["HostPort"]
            yield f"host=127.0.0.1 port={port} dbname=disposable user=lab password={password}"
        finally:
            if created:
                docker("rm", "--force", "--volumes", name)
            docker("network", "rm", network)
