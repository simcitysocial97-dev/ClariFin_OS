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
# M10-R3 (L7) — this guard was written when almost nothing was pinned, and it said
# "baselines are rasterisation-specific … must only ever be set on a GitHub runner".
#
# Investigated, because a blanket prohibition stops the baselines ever being corrected.
# Most of what it attributed to "rasterisation" was actually unpinned *configuration*,
# and is now deterministic:
#
#   * the UI font is SELF-HOSTED by the build (next/font/google emits 21 woff2 files
#     into dist/), including U+20B9 — verified by parsing the emitted unicode-range
#     blocks, not by eyeballing the CSS. Nothing depends on the machine's font list;
#   * the Chromium revision is checked above (EXPECTED_CHROMIUM);
#   * playwright.config.ts now pins locale, timezoneId, colorScheme and reducedMotion,
#     and sets expect.toHaveScreenshot{animations:'disabled'};
#   * the timeline no longer reads the wall clock (lib/runtime/clock.ts).
#
# What genuinely still varies between machines is Chromium's ANTI-ALIASING — Skia's
# hinting and subpixel settings differ with the host's fontconfig/freetype, and that
# cannot be pinned from application code.
#
# So the rule is narrowed to the true one: regenerate on a machine matching the runner's
# platform and Chromium, and treat a diff that is *only* soft grey-edge antialiasing as
# noise rather than a regression. Do not regenerate on a different platform, where the
# baselines would encode that platform's rasteriser.
_update_host_ok=1
case "$(uname -s)" in
  Linux) ;;
  *) _update_host_ok=0 ;;
esac
update_flag=()
if [ "${PLAYWRIGHT_UPDATE_SNAPSHOTS:-}" = "1" ]; then
  if [ "$_update_host_ok" -eq 1 ]; then
    echo -e "${YELLOW}PLAYWRIGHT_UPDATE_SNAPSHOTS=1 — regenerating visual baselines${NC}"
    echo -e "${YELLOW}  Host ${HOSTNAME:-local} $(uname -sr); chromium revision ${EXPECTED_CHROMIUM:-pinned}${NC}"
    update_flag=(--update-snapshots)
  else
    echo -e "${RED}Refusing to regenerate baselines on $(uname -s).${NC}"
    echo -e "${RED}Chromium's antialiasing is host-dependent and cannot be pinned from${NC}"
    echo -e "${RED}application code. Regenerate on Linux — the runner's platform — or the${NC}"
    echo -e "${RED}baselines will encode this platform's rasteriser.${NC}"
    exit 2
  fi
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
# M10-R2 — a leg runs exactly one of the two passes.
#
# `PLAYWRIGHT_PASS` is resolved into two plain booleans up front. An earlier version
# used `$(run_pass; echo $?)`, which is wrong under `set -euo pipefail`: `run_pass`
# returning 1 aborts the command substitution before `echo $?` can run, so the
# substitution is empty, NEITHER branch matches, and the script silently ran zero
# passes. A plain variable cannot fail that way.
PLAYWRIGHT_PASS="${PLAYWRIGHT_PASS:-all}"
case "$PLAYWRIGHT_PASS" in
  functional|visual|all) ;;
  *)
    echo -e "${RED}✗ Unknown PLAYWRIGHT_PASS=${PLAYWRIGHT_PASS} (expected functional, visual or all)${NC}"
    exit 1
    ;;
esac

OVERALL_RC=0

# M11-R4 — reporter selection.
#
# Both passes used to pass `--reporter=list` on the command line. A command-line
# `--reporter` REPLACES the reporter list in `playwright.config.ts` rather than adding
# to it, so the configured `json` reporter — which is the only place Playwright's own
# pass/fail/skip counts exist — never ran. `frontend/test-results/results.json` was
# never written on CI, which is why `playwright.yml` had to invent the counts its leg
# result document claimed (`passed: 0, failed: 0`): there was nothing there to read.
#
# The config already declares `list` alongside `html`, `json` and `junit`, so dropping
# the flag yields identical console output plus a machine-readable report. No reporter
# is added or removed, and no assertion changes.
if [ "$PLAYWRIGHT_PASS" != "visual" ]; then
  echo -e "${YELLOW}Pass 1/2 — functional suite (visual regression excluded)${NC}"
  # `set +e` so a failing suite is REPORTED and its exit code propagated, rather than
  # aborting the script before the reason is printed.
  set +e
  npx playwright test "${project_flag[@]}" ${spec_filter[@]+"${spec_filter[@]}"} \
    --grep-invert "Visual Regression"
  PASS1_RC=$?
  set -e
  if [ "$PASS1_RC" -ne 0 ]; then
    OVERALL_RC=$PASS1_RC
    echo -e "${RED}✗ Functional pass failed (exit ${PASS1_RC})${NC}"
  fi
fi

if [ "$PLAYWRIGHT_PASS" != "functional" ]; then
  echo -e "\n${YELLOW}Re-seeding the database for a deterministic visual pass...${NC}"
  if [ -z "${FINANCE_DB_PATH:-}" ]; then
    echo -e "${RED}✗ FINANCE_DB_PATH is not set.${NC}"
    echo -e "${RED}  Visual regression needs a dedicated, re-seable database:${NC}"
    echo -e "${RED}  without one it would be compared against order-dependent${NC}"
    echo -e "${RED}  state. Set FINANCE_DB_PATH in the job environment.${NC}"
    exit 1
  fi
  rm -f "${FINANCE_DB_PATH}" "${FINANCE_DB_PATH}-wal" "${FINANCE_DB_PATH}-shm"
  (cd "$REPO_ROOT" && PYTHONPATH=backend .venv/bin/python tools/e2e_seed.py --reset)

  echo -e "\n${YELLOW}Pass 2/2 — visual regression (immutable, serial)${NC}"
  # Deliberately NO spec filter: the visual pass is one serial sweep, and narrowing it
  # would silently drop screenshot assertions. The WHY block above explains why it must
  # not be sharded.
  set +e
  npx playwright test "${project_flag[@]}" \
    --grep "Visual Regression" --workers=1 ${update_flag[@]+"${update_flag[@]}"}
  PASS2_RC=$?
  set -e
  if [ "$PASS2_RC" -ne 0 ]; then
    OVERALL_RC=$PASS2_RC
    echo -e "${RED}✗ Visual pass failed (exit ${PASS2_RC})${NC}"
  fi
fi

if [ "$OVERALL_RC" -eq 0 ]; then
  echo -e "${GREEN}✓ All Playwright tests passed${NC}"
  echo "================================================"
  exit 0
fi

echo -e "${RED}✗ Playwright tests failed${NC}"
echo "================================================"
exit "$OVERALL_RC"
