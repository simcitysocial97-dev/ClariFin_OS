#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="$REPO_ROOT/.venv/bin/python"
BACKEND_LOG="$REPO_ROOT/runtime/generated/frontend-contract-backend.log"
STARTED_BACKEND=false
BACKEND_PID=""

cleanup() {
  if [ "$STARTED_BACKEND" = true ] && [ -n "$BACKEND_PID" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if ! curl --fail --silent --show-error http://127.0.0.1:8000/platform/v1/health >/dev/null 2>&1; then
  mkdir -p "$(dirname "$BACKEND_LOG")"
  (
    cd "$REPO_ROOT/backend"
    exec "$PYTHON" -m uvicorn src.api:app --host 127.0.0.1 --port 8000
  ) >"$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!
  STARTED_BACKEND=true
  ready=false
  for _ in $(seq 1 60); do
    if curl --fail --silent http://127.0.0.1:8000/platform/v1/health >/dev/null 2>&1; then
      ready=true
      break
    fi
    sleep 1
  done
  if [ "$ready" != true ]; then
    printf 'Backend did not become ready\n' >&2
    if [ -f "$BACKEND_LOG" ]; then
      tail -50 "$BACKEND_LOG" >&2
    fi
    exit 1
  fi
fi

cd "$REPO_ROOT"
"$PYTHON" -m runtime.verify frontend
