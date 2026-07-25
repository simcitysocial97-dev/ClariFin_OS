#!/bin/bash
set -euo pipefail

echo "=== Mutation Testing Baseline (Cashflow Engine Only) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$BACKEND_DIR"

# Clean previous results
rm -rf .mutmut-cache

# Use venv-installed mutmut and venv pytest
"$BACKEND_DIR/venv/bin/mutmut" run \
    --paths-to-mutate src/engines/cashflow_engine.py \
    --tests-dir tests/ \
    --runner "$BACKEND_DIR/venv/bin/python -m pytest -q tests/capability/household_cashflow/test_capability.py tests/property/cashflow/test_engine_properties.py tests/invariant/cashflow.py tests/unit/engines/cashflow" \
    || true  # Don't fail on surviving mutants

# Generate HTML report
"$BACKEND_DIR/venv/bin/mutmut" html

# Get mutation score
echo ""
echo "=== Results ==="
"$BACKEND_DIR/venv/bin/mutmut" results

SCORE=$("$BACKEND_DIR/venv/bin/mutmut" results 2>/dev/null | grep -oP 'Mutation score.*:\s*\K[0-9.]+' || echo "0")
echo ""
echo "Baseline mutation score: ${SCORE}%"
echo "HTML report: htmlcov/index.html"