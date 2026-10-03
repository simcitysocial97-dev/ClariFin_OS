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

project_flag=()
if [ -n "${PLAYWRIGHT_PROJECT:-}" ]; then
  project_flag=(--project="${PLAYWRIGHT_PROJECT}")
fi

# M11 — visual regression runs as its own pass against an immutable database.
#
# WHY
# ---
# Every spec shares one SQLite file. The suite WRITES to it: 14 POSTs were
# observed in a single run of `playwright.yml`, so by the time a
# visual-regression spec reaches its first screenshot, the data on screen
# depends on which specs ran before it, how many workers were active, and how
# many times a test was retried. Cashflow Trend's Y-axis ticks are derived from
# `domain={[0, 'dataMax + 100000']}`, so a varying dataMax moves the ticks and
# one `₹72K` label becomes 1 740 differing pixels — a red gate on a chart that
# did not change. In the worst observed run 11 of 13 snapshots drifted, one by
# 23% of the frame.
#
# Seeding the database (playwright.yml) fixes the STARTING state but not the
# problem: the suite then mutates it. So the visual specs are split out and run
# last, against a database re-seeded immediately beforehand and read-only for
# the duration of that pass.
#
# The main suite therefore excludes the visual specs. Both passes still run, so
# coverage is unchanged — only the order in which state is observed is fixed.
# `workers=1` on the visual pass removes worker scheduling from the equation;
# without writes to read, serial execution is safe and costs only a few seconds
# for ~50 screenshot assertions.
# M10-R2 — the functional pass can be sharded across runners.
#
# SAFETY. Every spec shares one SQLite file and the suite WRITES to it (see the WHY
# block above). Sharding is safe *across* runners precisely because each runner has its
# own checkout and therefore its own database, freshly seeded by the workflow — which is
# a stronger isolation guarantee than the single-runner case this script was written
# for. Within one shard the ordering caveats above still hold unchanged, because a shard
# is still a single process against a single database.
#
# `PLAYWRIGHT_SPEC_FILES` restricts the pass to an explicit list of spec files, assigned
# deterministically by the plan job. Whole files only: a shard never splits a spec, so
# `test.describe` blocks and their fixtures stay inside one process.
spec_filter=()
if [ -n "${PLAYWRIGHT_SPEC_FILES:-}" ]; then
  # shellcheck disable=SC2206 # deliberate word splitting: this is a file list
  spec_filter=(${PLAYWRIGHT_SPEC_FILES})
  echo -e "${GREEN}Shard scope: ${#spec_filter[@]} spec file(s)${NC}"
fi

# `PLAYWRIGHT_PASS` lets a leg run exactly one of the two passes. Without it the script
# runs both, which is the original single-runner behaviour.
run_pass() {
  case "${PLAYWRIGHT_PASS:-all}" in
    functional) return 0 ;;
    visual) return 1 ;;
    all) return 0 ;;
    *) echo -e "${RED}✗ Unknown PLAYWRIGHT_PASS=${PLAYWRIGHT_PASS}${NC}"; exit 1 ;;
  esac
}

if [ "$(run_pass; echo $?)" = "0" ]; then
  echo -e "${YELLOW}Pass 1/2 — functional suite (visual regression excluded)${NC}"
  npx playwright test "${project_flag[@]}" "${spec_filter[@]}" --reporter=list \
    --grep-invert "Visual Regression"
fi

if [ "$(run_pass; echo $?)" = "1" ]; then
  echo -e "\n${YELLOW}Pass 2/2 — visual regression (immutable, serial)${NC}"
  # Deliberately no spec filter: the visual pass is one serial sweep, and narrowing it
  # would silently drop screenshot assertions. The WHY block above explains why it must
  # not be sharded.
  if [ -n "${FINANCE_DB_PATH:-}" ]; then
    rm -f "${FINANCE_DB_PATH}" "${FINANCE_DB_PATH}-wal" "${FINANCE_DB_PATH}-shm"
    (cd "$REPO_ROOT" && PYTHONPATH=backend .venv/bin/python tools/e2e_seed.py --reset)
  else
    echo -e "${RED}✗ FINANCE_DB_PATH is not set.${NC}"
    exit 1
  fi
  set +e
  npx playwright test "${project_flag[@]}" --reporter=list \
    --grep "Visual Regression" --workers=1 "${update_flag[@]}"
  status=$?
  set -e
  if [ "$status" -eq 0 ]; then
    echo -e "${GREEN}✓ All Playwright tests passed${NC}"
    echo "================================================"
    exit 0
  fi
  echo -e "${RED}✗ Playwright tests failed${NC}"
  echo "================================================"
  exit "$status"
fi

echo -e "\n${YELLOW}Re-seeding the database for a deterministic visual pass...${NC}"
if [ -n "${FINANCE_DB_PATH:-}" ]; then
  rm -f "${FINANCE_DB_PATH}" "${FINANCE_DB_PATH}-wal" "${FINANCE_DB_PATH}-shm"
  (cd "$REPO_ROOT" && PYTHONPATH=backend .venv/bin/python tools/e2e_seed.py --reset)
else
  echo -e "${RED}✗ FINANCE_DB_PATH is not set.${NC}"
  echo -e "${RED}  Visual regression needs a dedicated, re-seedable database:${NC}"
  echo -e "${RED}  without one it would be compared against order-dependent${NC}"
  echo -e "${RED}  state. Set FINANCE_DB_PATH in the job environment.${NC}"
  exit 1
fi

echo -e "\n${YELLOW}Pass 2/2 — visual regression (immutable, serial)${NC}"
npx playwright test "${project_flag[@]}" --reporter=list \
  --grep "Visual Regression" --workers=1 "${update_flag[@]}"

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
