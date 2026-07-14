#!/usr/bin/env bash
set -euo pipefail
# This script is automatically run by Cline after every change. All failures must be fixed before commit.

START=$(date +%s)

echo "=== Running verify-local ==="

# Execute verify-fast
./scripts/verify-fast.sh

echo "[Stage] pytest architecture"
pytest tests/architecture -q --tb=short --maxfail=3

echo "[Stage] pytest properties"
pytest tests/properties -q --tb=short --maxfail=3

echo "[Stage] pytest golden"
pytest tests/golden -q --tb=short --maxfail=3

echo "[Stage] pytest (adaptive)"
# Try testmon first; fall back to full suite if unavailable or .testmondata missing
if [ -f ".testmondata" ] && ./venv/bin/python3 -c "import pytest_testmon" 2>/dev/null; then
    pytest --testmon tests/ -q --tb=short --maxfail=3 --ignore=tests/architecture --ignore=tests/properties --ignore=tests/golden
else
    pytest tests/ -q --tb=short --maxfail=3 --ignore=tests/architecture --ignore=tests/properties --ignore=tests/golden
fi

echo "Completed in $(( $(date +%s)-START )) seconds"