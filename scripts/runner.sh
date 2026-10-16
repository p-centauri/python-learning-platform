#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
set -a
source "$REPO_DIR/.local/runner.env"
set +a
cd "$REPO_DIR/apps/runner"
exec "$REPO_DIR/.venv/bin/python" -m uvicorn runner.main:app --host 127.0.0.1 --port 9000
