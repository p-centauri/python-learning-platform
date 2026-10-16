"""Create local runner credentials without printing them or overwriting existing ones."""

from pathlib import Path
import os
import secrets

root = Path(__file__).resolve().parents[1]
directory = root / ".local"
directory.mkdir(exist_ok=True)
path = directory / "runner.env"
try:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    pass
else:
    with os.fdopen(descriptor, "w") as output:
        output.write(f"RUNNER_URL=http://127.0.0.1:9000\nRUNNER_TOKEN={secrets.token_urlsafe(48)}\n")
path.chmod(0o600)
print("Runner configuration is saved in ignored .local/runner.env. Credentials were not printed.")
