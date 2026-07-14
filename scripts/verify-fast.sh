#!/usr/bin/env bash
set -euo pipefail
# This script is automatically run by Cline after every change. All failures must be fixed before commit.

START=$(date +%s)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

echo "=== Running verify-fast ==="
echo "Backend dir: $BACKEND_DIR"

# Activate venv if available
if [ -d "$BACKEND_DIR/.venv" ]; then
    source "$BACKEND_DIR/.venv/bin/activate"
elif [ -d "$ROOT_DIR/.venv" ]; then
    source "$ROOT_DIR/.venv/bin/activate"
fi

cd "$BACKEND_DIR"

echo "[Stage] ruff check --fix"
ruff check src/ --fix

echo "[Stage] ruff format --check"
ruff format --check src/

echo "[Stage] pyright"
if command -v pyright >/dev/null 2>&1; then
    pyright src/
else
    echo "[Fallback] mypy"
    mypy src/
fi

echo "Completed in $(( $(date +%s)-START )) seconds"