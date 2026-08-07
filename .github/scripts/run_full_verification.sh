#!/usr/bin/env bash
# .github/scripts/run_full_verification.sh
# Full verification: fast checks + backend + frontend.
# Invoked by: python runtime/verify.py full
# Exit code: 0 = pass, non-zero = fail

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

fail=0

echo "================================================"
echo "  ClariFin OS — Full Verification"
echo "================================================"

# ── Fast checks (lint, format, typecheck, unit) ──
echo -e "\n[1/3] Fast checks..."
bash "$SCRIPT_DIR/run_fast_checks.sh" || fail=1

# ── Backend verification (contract, invariant, property, engines) ──
echo -e "\n[2/3] Backend verification..."
bash "$SCRIPT_DIR/run_backend_verification.sh" || fail=1

# ── Frontend verification (eslint, tsc, vitest) ──
echo -e "\n[3/3] Frontend verification..."
bash "$SCRIPT_DIR/run_frontend_verification.sh" || fail=1

echo ""
echo "================================================"
if [ "$fail" -eq 0 ]; then
  echo -e "  All full verification checks passed!"
  echo "================================================"
  exit 0
else
  echo -e "  Failed checks detected."
  echo "================================================"
  exit 1
fi
