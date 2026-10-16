#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$REPO_DIR/.venv/bin/python}"
API_PID=""
WEB_PID=""
RUNNER_PID=""
cleanup() {
  [ -z "$API_PID" ] || kill "$API_PID" 2>/dev/null || true
  [ -z "$WEB_PID" ] || kill "$WEB_PID" 2>/dev/null || true
  [ -z "$RUNNER_PID" ] || kill "$RUNNER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
if [ -f "$REPO_DIR/.local/runner.env" ]; then
  set -a
  source "$REPO_DIR/.local/runner.env"
  set +a
  bash "$REPO_DIR/scripts/runner.sh" &
  RUNNER_PID=$!
fi
cd "$REPO_DIR/apps/api"
"$PYTHON_BIN" -m alembic upgrade head
"$PYTHON_BIN" -m app.seed
"$PYTHON_BIN" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
API_PID=$!
cd "$REPO_DIR/apps/web"
node node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3000 &
WEB_PID=$!
wait "$API_PID" "$WEB_PID"
