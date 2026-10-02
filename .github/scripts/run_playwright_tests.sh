#!/usr/bin/env bash
# .github/scripts/run_playwright_tests.sh
# End-to-end Playwright browser tests.
# Requires: node + browsers pre-installed by CI node setup.
# Invoked by: python -m runtime.verify playwright
# Exit code: 0 = pass, non-zero = fail

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT/frontend"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================"
echo "  ClariFin OS — Playwright E2E Tests"
echo "================================================"

# ED6: Pre-flight browser availability check — fail fast if browser not available
echo -e "\n${YELLOW}Checking browser availability...${NC}"
EXPECTED_CHROMIUM=$(node -e "const b=require('./node_modules/playwright-core/browsers.json').browsers; process.stdout.write(String(b.find(x=>x.name==='chromium').revision))")
EXPECTED_SHELL=$(node -e "const b=require('./node_modules/playwright-core/browsers.json').browsers; process.stdout.write(String(b.find(x=>x.name==='chromium-headless-shell').revision))")
BROWSER_LIST=$(npx --no-install playwright install --list)
if ! printf '%s\n' "$BROWSER_LIST" | grep -q "chromium-$EXPECTED_CHROMIUM" || ! printf '%s\n' "$BROWSER_LIST" | grep -q "chromium_headless_shell-$EXPECTED_SHELL"; then
  echo -e "${RED}✗ Required Playwright browser revision is unavailable. Run 'npx --no-install playwright install chromium' first.${NC}"
  echo "================================================"
  exit 1
fi
echo -e "${GREEN}✓ Browser 'chromium' revision $EXPECTED_CHROMIUM available${NC}"

mkdir -p test-results playwright-report

# Build the frontend first — Playwright's webServer (`npm start` = `next start`)
# serves the server-mode build from dist/ (C38.6: deterministic lifecycle).
echo -e "\n${YELLOW}Building frontend...${NC}"
npm run build

echo -e "\n${YELLOW}Running Playwright test suite...${NC}"
# PLAYWRIGHT_UPDATE_SNAPSHOTS=1 regenerates the visual baselines. It must only
# ever be set on a GitHub runner: baselines are rasterisation-specific, so a
# workstation running with a different font stack produces images that look
# correct locally and fail in CI.
update_flag=()
if [ "${PLAYWRIGHT_UPDATE_SNAPSHOTS:-}" = "1" ]; then
  echo -e "${YELLOW}PLAYWRIGHT_UPDATE_SNAPSHOTS=1 — regenerating visual baselines${NC}"
  update_flag=(--update-snapshots)
fi

if [ -n "${PLAYWRIGHT_PROJECT:-}" ]; then
  npx playwright test --project="${PLAYWRIGHT_PROJECT}" --reporter=list "${update_flag[@]}"
else
  npx playwright test --reporter=list "${update_flag[@]}"
fi

status=$?
if [ "$status" -eq 0 ]; then
  echo -e "${GREEN}✓ All Playwright tests passed${NC}"
  echo "================================================"
  exit 0
else
  echo -e "${RED}✗ Playwright tests failed${NC}"
  echo "================================================"
  exit "$status"
fi
