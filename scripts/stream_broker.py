"""Owned AOF Redis broker for trusted maintainer checks; no learner execution."""

from contextlib import contextmanager
import json
from pathlib import Path
import secrets
import socket
import tempfile
import time
import uuid
from redis import Redis
from persistence_db import docker

IMAGE = "redis@sha256:02419de7eddf55aa5bcf49efb74e88fa8d931b4d77c07eff8a6b2144472b6952"


@contextmanager
def disposable_broker():
    name = "academy-stream-" + uuid.uuid4().hex
    network = name + "-net"
    volume = name + "-data"
    docker("image", "inspect", IMAGE)
    with tempfile.TemporaryDirectory(prefix="academy-broker-env-") as directory:
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            selected_port = reservation.getsockname()[1]
        password = secrets.token_hex(24)
        environment = Path(directory) / "broker.env"
        environment.write_text("REDIS_PASSWORD=" + password + "\n")
        environment.chmod(0o600)
        docker("network", "create", network)
        created = False
        made_volume = False
        try:
            docker("volume", "create", volume)
            made_volume = True
            # Secret expands only into the owned mode-0600 configuration file, never argv/log output.
            boot = 'umask 077; printf "bind 0.0.0.0\\nprotected-mode yes\\nrequirepass %s\\nappendonly yes\\nappendfsync always\\nsave \\"\\"\\ndir /data\\nmaxmemory 128mb\\nmaxmemory-policy noeviction\\n" "$REDIS_PASSWORD" > /data/lab.conf; chown redis:redis /data/lab.conf; exec /usr/local/bin/docker-entrypoint.sh redis-server /data/lab.conf'
            docker(
                "create",
                "--name",
                name,
                "--network",
                network,
                "--publish",
                f"127.0.0.1:{selected_port}:6379",
                "--env-file",
                str(environment),
                "--memory",
                "256m",
                "--cpus",
                "1",
                "--pids-limit",
                "128",
                "--mount",
                "type=volume,source=" + volume + ",target=/data",
                IMAGE,
                "sh",
                "-c",
                boot,
            )
            created = True
            docker("start", name)
            ports = json.loads(docker("inspect", "--format", "{{json .NetworkSettings.Ports}}", name))
            port = ports["6379/tcp"][0]["HostPort"]
            url = f"redis://:{password}@127.0.0.1:{port}/0"
            client = Redis.from_url(url, socket_timeout=2, socket_connect_timeout=2)
            try:
                for _ in range(60):
                    try:
                        if client.ping():
                            break
                    except Exception:
                        pass
                    time.sleep(0.1)
                else:
                    raise RuntimeError("owned broker not ready")
                assert client.config_get("appendonly")["appendonly"] == "yes"
                yield url, name
            finally:
                client.close()
        finally:
            if created:
                docker("rm", "--force", "--volumes", name)
            if made_volume:
                docker("volume", "rm", volume)
            docker("network", "rm", network)
