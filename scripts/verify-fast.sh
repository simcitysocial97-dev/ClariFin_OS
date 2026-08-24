#!/usr/bin/env bash
set -euo pipefail
# This script is automatically run by Cline after every change. All failures must be fixed before commit.
#
# M10: routes ALL tooling through the single repository venv (./.venv) so no
# project verification depends on globally installed Python packages.

START=$(date +%s)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

echo "=== Running verify-fast ==="
echo "Backend dir: $BACKEND_DIR"

# Resolve the controlled interpreter: ./venv/bin/python (single repo venv).
# FAIL FAST if canonical environment is unavailable - no fallback to backend/.venv or PATH.
if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PY="$ROOT_DIR/.venv/bin/python"
    export PATH="$ROOT_DIR/.venv/bin:$PATH"
else
    echo "ERROR: Canonical environment not found at $ROOT_DIR/.venv" >&2
    echo "       Run './scripts/bootstrap.sh' to create the environment." >&2
    echo "       This script must not fall back to backend/.venv or system python." >&2
    exit 1
fi

echo "Controlled interpreter: $PY"
"$PY" --version

cd "$BACKEND_DIR"

echo "[Stage] ruff check --fix"
"$PY" -m ruff check src/ --fix

echo "[Stage] ruff format --check"
"$PY" -m ruff format --check src/

echo "[Stage] mypy (backend strict)"
"$PY" -m mypy src/

echo "Completed in $(( $(date +%s)-START )) seconds"

