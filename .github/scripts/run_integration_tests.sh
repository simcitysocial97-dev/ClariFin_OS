#!/usr/bin/env bash
# .github/scripts/run_integration_tests.sh
# Integration tests: API integration and cross-capability tests.
# Invoked by: python runtime/verify.py integration
# Exit code: 0 = pass, non-zero = fail

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT/backend" || { echo "backend/ not found"; exit 1; }

# Canonical Python resolver (venv-first)
if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
  PY="$REPO_ROOT/.venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi

fail=0

echo "================================================"
echo "  ClariFin OS — Integration Tests"
echo "================================================"

if [ -d "tests/integration" ]; then
  echo -e "\n>> pytest tests/integration"
  "$PY" -m pytest tests/integration/ \
    -q \
    --no-header \
    --tb=short \
    --timeout=120
  rc=$?
  [ "$rc" -eq 5 ] && rc=0
  [ "$rc" -ne 0 ] && fail=1
else
  echo "No tests/integration directory found, skipping."
fi

echo ""
echo "================================================"
if [ "$fail" -eq 0 ]; then
  echo -e "  Integration tests passed!"
  echo "================================================"
  exit 0
else
  echo -e "  Integration tests failed."
  echo "================================================"
  exit 1
fi
