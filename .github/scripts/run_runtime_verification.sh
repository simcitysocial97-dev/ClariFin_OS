#!/usr/bin/env bash
# .github/scripts/run_runtime_verification.sh
# Engineering Runtime self-verification.
# Executes the runtime's own test suite (runtime/tests/) plus a quick
# integrity scan. This is the canonical "runtime" verification gate.
# Invoked by: python runtime/verify.py runtime
# Exit code: 0 = pass, non-zero = fail

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED_CHECKS=()

echo "================================================"
echo "  ClariFin OS — Runtime Self-Verification"
echo "================================================"

# ── Runtime unit tests ───────────────────────────
echo -e "\n${YELLOW}[1/2] Runtime test suite...${NC}"
if python3 -m pytest runtime/tests/ -q --timeout=30; then
  echo -e "${GREEN}✓ Runtime tests passed${NC}"
else
  echo -e "${RED}✗ Runtime tests failed${NC}"
  FAILED_CHECKS+=("runtime-tests")
fi

# ── Integrity engine scan ─────────────────────────
echo -e "\n${YELLOW}[2/2] Architectural integrity...${NC}"
if python3 runtime/verify.py integrity; then
  echo -e "${GREEN}✓ Integrity scan passed${NC}"
else
  echo -e "${RED}✗ Integrity scan failed${NC}"
  FAILED_CHECKS+=("integrity")
fi

echo ""
echo "================================================"
if [ ${#FAILED_CHECKS[@]} -eq 0 ]; then
  echo -e "${GREEN}  All runtime checks passed!${NC}"
  echo "================================================"
  exit 0
else
  echo -e "${RED}  Failed checks: ${FAILED_CHECKS[*]}${NC}"
  echo "================================================"
  exit 1
fi
