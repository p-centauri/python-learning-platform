"""Create a private Docker Desktop runner environment; never exposes a new port."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / ".local/runner.env"
config = {}
for line in source.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        key, value = line.split("=", 1)
        config[key.removeprefix("export ")] = value.strip().strip("\"'")
if len(config.get("RUNNER_TOKEN", "")) < 32:
    raise SystemExit("Configure and verify the host runner first with make runner-setup and make runner.")
target = ROOT / ".local/compose-runner.env"
fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
os.fchmod(fd, 0o600)
with os.fdopen(fd, "w") as out:
    out.write("RUNNER_URL=http://host.docker.internal:9000\nRUNNER_TOKEN=" + config["RUNNER_TOKEN"] + "\n")
os.chmod(target, 0o600)
print(
    "Saved private .local/compose-runner.env for Docker Desktop. Keep the authenticated host controller on loopback; no Docker socket is mounted into the academy."
)
