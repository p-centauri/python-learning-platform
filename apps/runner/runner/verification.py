"""Trusted startup probes. Learner execution stays disabled if any probe fails."""

import json
from .sandbox import (
    PYTHON_IMAGE,
    SQL_IMAGE,
    PROFILE,
    SandboxFailure,
    checked,
    python_case,
    sql_case,
)


def verify():
    if not __debug__:
        raise RuntimeError("Isolation verification requires Python assertions enabled.")
    info = json.loads(checked(["info", "--format", "{{json .}}"], limit=65536))
    assert any("seccomp" in option for option in info["SecurityOptions"]), "Docker seccomp must be enabled."
    assert info["MemoryLimit"] and info["SwapLimit"] and info["CpuCfsQuota"] and info["PidsLimit"], (
        "Docker resource limits are required."
    )
    for image in [PYTHON_IMAGE, SQL_IMAGE]:
        checked(["image", "inspect", image, "--format", "{{.Id}}"])
    # Only remove expired containers carrying this runner's exact label.
    expired = checked(["ps", "-aq", "--filter", f"label=academy.runner={PROFILE}"]).split()
    import time

    for name in expired:
        labels = json.loads(checked(["inspect", name, "--format", "{{json .Config.Labels}}"]))
        if int(labels.get("academy.expires", "0")) < time.time():
            checked(["rm", "-f", name])
    probes = []
    definition = {"function": "probe"}

    def python_probe(name, code, expected):
        result = python_case(code, definition, {"args": [], "expected": expected})
        assert result["status"] == "passed", f"{name}: {result}"
        probes.append(name)

    python_probe(
        "nonroot-seccomp-cgroups-no-secrets",
        """
def probe():
    import os
    status = open('/proc/self/status').read()
    return [os.getuid(), 'CapEff:\\t0000000000000000' in status,
            'NoNewPrivs:\\t1' in status, 'Seccomp:\\t2' in status,
            open('/sys/fs/cgroup/memory.max').read().strip(),
            open('/sys/fs/cgroup/pids.max').read().strip(),
            open('/sys/fs/cgroup/cpu.max').read().strip(),
            'RUNNER_TOKEN' in os.environ, 'DATABASE_URL' in os.environ,
            os.path.exists('/var/run/docker.sock')]
""",
        [65532, True, True, True, "134217728", "32", "50000 100000", False, False, False],
    )
    python_probe(
        "root-and-host-files-inaccessible",
        """
def probe():
    results = []
    for path in ['/host/academy.db', '/Users/xasilov/Documents/ChatGPT/career/apps/api/academy.db']:
        try: open(path).read(); results.append(False)
        except OSError: results.append(True)
    try: open('/runner-write-probe', 'w').write('bad'); results.append(False)
    except OSError: results.append(True)
    return results
""",
        [True, True, True],
    )
    python_probe(
        "network-denied",
        """
def probe():
    import socket
    try:
        socket.create_connection(('1.1.1.1', 443), timeout=0.3)
        return False
    except OSError: return True
""",
        True,
    )
    python_probe(
        "tmpfs-size-and-noexec",
        """
def probe():
    import os, subprocess
    try:
        with open('/tmp/big', 'wb') as out: out.write(b'x' * 9000000)
        bounded = False
    except OSError: bounded = True
    os.remove('/tmp/big')
    open('/tmp/probe.sh','w').write('#!/bin/sh\\nexit 0\\n')
    os.chmod('/tmp/probe.sh', 0o700)
    try: subprocess.run(['/tmp/probe.sh']); denied = False
    except PermissionError: denied = True
    return [bounded, denied]
""",
        [True, True],
    )
    python_probe(
        "pids-bounded",
        """
def probe():
    import subprocess
    children = []
    try:
        for _ in range(40):
            children.append(subprocess.Popen(['sleep','10'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    except OSError: pass
    for child in children: child.terminate(); child.wait()
    return len(children) < 32
""",
        True,
    )
    memory = python_case(
        "def probe(): return len(bytearray(512 * 1024 * 1024))",
        definition,
        {"args": [], "expected": 536870912},
    )
    assert memory["status"] == "error", "Memory allocation must be stopped by the container limit."
    probes.append("memory-bounded")
    for name, code, expected in [
        ("runaway-stopped", "def probe():\n    while True: pass", "timeout"),
        ("output-flood-stopped", "def probe():\n    print('x' * 1000000)\n    return 1", "output-limit"),
    ]:
        try:
            python_case(code, definition, {"args": [], "expected": 1})
        except SandboxFailure as error:
            assert error.status == expected, str(error)
            probes.append(name)
        else:
            raise AssertionError(name + " did not enforce its limit.")
    # A second clean container proves no scratch files survive a submission.
    python_probe(
        "fresh-filesystem", "def probe():\n    import os\n    return os.path.exists('/tmp/probe.sh')", False
    )
    fixture = {
        "setup_sql": "CREATE TABLE fixture(id integer); INSERT INTO fixture VALUES(1);",
        "columns": ["id"],
        "expected": [["1"]],
    }
    assert sql_case("SELECT id FROM fixture", fixture)["status"] == "passed"
    probes.append("postgresql-fixture")
    role = {**fixture, "columns": ["role", "readonly"], "expected": [["learner", "on"]]}
    assert (
        sql_case(
            "SELECT current_user AS role, current_setting('default_transaction_read_only') AS readonly", role
        )["status"]
        == "passed"
    )
    probes.append("postgresql-restricted-role")
    for name, query in [
        ("postgresql-host-files-denied", "SELECT pg_read_file('/etc/passwd')"),
        ("postgresql-sleep-stopped", "SELECT pg_sleep(20)"),
    ]:
        result = sql_case(query, fixture)
        assert result["status"] == "error", f"{name}: {result}"
        probes.append(name)
    # Check cleanup even for timeout/output/OOM/SQL-error paths.
    assert checked(["ps", "-aq", "--filter", f"label=academy.runner={PROFILE}"]).strip() == "", (
        "Unexpected runner containers remain."
    )
    return {
        "profile": PROFILE,
        "checks": probes,
        "docker_version": info["ServerVersion"],
        "python_image": PYTHON_IMAGE,
        "sql_image": SQL_IMAGE,
    }
