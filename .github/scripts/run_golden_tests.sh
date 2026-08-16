#!/usr/bin/env bash
# .github/scripts/run_golden_tests.sh
# Golden dataset regression tests + capability tests.
# Invoked by: python runtime/verify.py golden
# Exit code: 0 = pass, non-zero = fail

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT/backend"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED_CHECKS=()

echo "================================================"
echo "  ClariFin OS — Golden Dataset Regression"
echo "================================================"

mkdir -p tests/generated/golden

# ── Golden regression tests ───────────────────────
echo -e "\n${YELLOW}[1/2] Golden regression tests...${NC}"
if pytest tests/golden/ \
    --timeout=120 \
    --tb=short \
    -v \
    --no-header \
    -p no:cacheprovider; then
  echo -e "${GREEN}✓ Golden regression tests passed${NC}"
else
  echo -e "${RED}✗ Golden regression tests failed${NC}"
  FAILED_CHECKS+=("golden-regression")
fi

# ── Capability smoke tests ────────────────────────
echo -e "\n${YELLOW}[2/2] Capability tests...${NC}"
if pytest tests/capability/ \
    --timeout=120 \
    --tb=short \
    -v \
    --no-header \
    -p no:cacheprovider; then
  echo -e "${GREEN}✓ Capability tests passed${NC}"
else
  echo -e "${RED}✗ Capability tests failed${NC}"
  FAILED_CHECKS+=("capability")
fi

echo ""
echo "================================================"
if [ ${#FAILED_CHECKS[@]} -eq 0 ]; then
  echo -e "${GREEN}  All golden checks passed!${NC}"
  echo "================================================"
  exit 0
else
  echo -e "${RED}  Failed checks: ${FAILED_CHECKS[*]}${NC}"
  echo "================================================"
  exit 1
fi
