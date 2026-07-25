#!/usr/bin/env bash
# .github/scripts/run_fast_checks.sh
# Fast checks that run on every push
# Target: complete in under 5 minutes
# Exit code: 0 = pass, non-zero = fail

set -euo pipefail

# Colors for readable output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKEND_DIR="${1:-backend}"
FAILED_CHECKS=()

echo "================================================"
echo "  ClariFin OS — Fast Quality Checks"
echo "  Target: under 5 minutes"
echo "================================================"

cd "$BACKEND_DIR"

# ── Check 1: Ruff linting ─────────────────────────
echo -e "\n${YELLOW}[1/5] Ruff lint check...${NC}"
if ruff check . --output-format=github; then
  echo -e "${GREEN}✓ Ruff passed${NC}"
else
  echo -e "${RED}✗ Ruff failed${NC}"
  FAILED_CHECKS+=("ruff")
fi

# ── Check 2: Black formatting ─────────────────────
echo -e "\n${YELLOW}[2/5] Black format check...${NC}"
if black --check --diff .; then
  echo -e "${GREEN}✓ Black passed${NC}"
else
  echo -e "${RED}✗ Black failed${NC}"
  FAILED_CHECKS+=("black")
fi

# ── Check 3: Mypy type checking ───────────────────
echo -e "\n${YELLOW}[3/5] Mypy type check...${NC}"
# Only check src directory, not tests (tests are harder to type)
if mypy src/ --ignore-missing-imports --no-error-summary 2>/dev/null; then
  echo -e "${GREEN}✓ Mypy passed${NC}"
else
  echo -e "${YELLOW}⚠ Mypy had issues (non-blocking for now)${NC}"
  # Note: not added to FAILED_CHECKS yet — enable when types are clean
fi

# ── Check 4: Unit tests ───────────────────────────
echo -e "\n${YELLOW}[4/5] Unit tests...${NC}"
if pytest tests/unit/ \
    -x \
    --timeout=30 \
    --tb=short \
    -q \
    --no-header \
    -n auto; then
  echo -e "${GREEN}✓ Unit tests passed${NC}"
else
  echo -e "${RED}✗ Unit tests failed${NC}"
  FAILED_CHECKS+=("unit-tests")
fi

# ── Check 5: Architecture boundaries ─────────────
echo -e "\n${YELLOW}[5/5] Architecture boundary tests...${NC}"
if pytest tests/architecture/ \
    --timeout=30 \
    --tb=short \
    -q \
    --no-header; then
  echo -e "${GREEN}✓ Architecture tests passed${NC}"
else
  echo -e "${RED}✗ Architecture tests failed${NC}"
  FAILED_CHECKS+=("architecture-tests")
fi

# ── Summary ───────────────────────────────────────
echo ""
echo "================================================"
if [ ${#FAILED_CHECKS[@]} -eq 0 ]; then
  echo -e "${GREEN}  All fast checks passed!${NC}"
  echo "================================================"
  exit 0
else
  echo -e "${RED}  Failed checks: ${FAILED_CHECKS[*]}${NC}"
  echo "================================================"
  exit 1
fi
