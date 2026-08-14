#!/usr/bin/env bash
set -euo pipefail
# This script is automatically run by Cline after every change. All failures must be fixed before commit.
#
# M10: routes ALL tooling through the single repository venv (./.venv) so no
# project verification depends on globally installed Python packages. Falls back
# to PATH only if the venv has not been bootstrapped yet (loudly).

START=$(date +%s)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

echo "=== Running verify-fast ==="
echo "Backend dir: $BACKEND_DIR"

# Resolve the controlled interpreter: ./venv/bin/python (single repo venv).
if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PY="$ROOT_DIR/.venv/bin/python"
    export PATH="$ROOT_DIR/.venv/bin:$PATH"
elif [ -x "$BACKEND_DIR/.venv/bin/python" ]; then
    # Legacy backend venv — tolerated but NOT the M10 target. Bootstrap rebuilds.
    PY="$BACKEND_DIR/.venv/bin/python"
    export PATH="$BACKEND_DIR/.venv/bin:$PATH"
else
    echo "WARNING: no ./.venv found — run scripts/bootstrap.sh. Using PATH fallback." >&2
    PY="$(command -v python3 || command -v python)"
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

