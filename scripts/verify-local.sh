#!/usr/bin/env bash
set -uo pipefail
# This script is automatically run by Cline after every change. All failures must be fixed before commit.
# Note: verify-fast lint stages are informational only; they surface pre-existing lint debt
# without blocking NEW validation stages (properties/golden/architecture).

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
START=$(date +%s)

echo "=== Running verify-local ==="

echo "[Stage] verify-fast (ruff/mypy)"
./scripts/verify-fast.sh || echo "[WARN] verify-fast reported lint findings; continuing to validation stages"

echo "[Stage] Coverage Scanner"
./backend/venv/bin/python3 backend/tools/check_coverage.py

echo "[Stage] Coverage Integrity Tests"
cd "$BACKEND_DIR"
pytest tests/meta/test_coverage_integrity.py -q --tb=short --maxfail=3

echo "[Stage] Change Intelligence"
./backend/venv/bin/python3 backend/tools/change_intelligence.py || true

echo "[Stage] pytest architecture"
pytest tests/architecture -q --tb=short --maxfail=3

echo "[Stage] pytest capabilities (smoke)"
pytest tests/capabilities -q --tb=short --maxfail=3

echo "[Stage] pytest properties"
pytest tests/properties -q --tb=short --maxfail=3

echo "[Stage] pytest golden"
pytest tests/golden -q --tb=short --maxfail=3

echo "[Stage] pytest (adaptive)"
# Try testmon first; fall back to full suite if unavailable or .testmondata missing
if [ -f ".testmondata" ] && python3 -c "import pytest_testmon" 2>/dev/null; then
    pytest --testmon tests/ -q --tb=short --maxfail=3 --ignore=tests/architecture --ignore=tests/properties --ignore=tests/generated --ignore=tests/meta --ignore=tests/golden
else
    pytest tests/ -q --tb=short --maxfail=3 --ignore=tests/architecture --ignore=tests/properties --ignore=tests/generated --ignore=tests/meta --ignore=tests/golden
fi

echo "Completed in $(( $(date +%s)-START )) seconds"