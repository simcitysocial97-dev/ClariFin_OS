# Verification Report

**Profile:** playwright
**Generated:** 2026-08-17T00:49:07.725772+00:00
**Overall Status:** failed

## Changed Files

- `memory-bank/activeContext.md`
- `progress.md`
- `activeContext.md`
- `backend/tests/invariants/_m4_exit_probe/test_m4_exit_probe.py`
- `docs/M9-C10-forensic-report.md`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/analytics-mobile-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/analytics-page-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/behavior-page-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/cards-page-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/categories-mobile-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/categories-page-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/dark-mode-dashboard-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/dashboard-mobile-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/dashboard-page-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/family-mode-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/header-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/home-mobile-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/home-page-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/import-page-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/personal-mode-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/reconciliation-page-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/settings-page-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/sidebar-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/transactions-mobile-chromium-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/transactions-page-chromium-linux.png`
- `test-results/.last-run.json`

## Blast Radius

- **affected_engines**: []
- **affected_services**: []
- **affected_capabilities**: []
- **affected_tests**: []

## Verification Plan

- **Plan ID:** plan-20260817-004804
- **Scope:** playwright
- **Targets:** 1
- **Steps:** 1
- **Estimated Duration:** 1800s

## Tasks Executed

| Task ID | Command | Status | Exit | Duration | Error | Stdout | Stderr |
|---------|---------|--------|------|----------|-------|--------|--------|
| step-0001 | bash .github/scripts/run_playwright_tests.sh | VerificationStatus.FAILED | 1 | 62.9s | ⚠ Warning: Next.js inferred your workspace root, but it may not be correct.  We detected multiple lockfiles and selected the directory of /home/vasantha/AI-Projects/ClariFin_OS/package-lock.json as... | /home/vasantha/AI-Projects/ClariFin_OS/runtime/generated/execution/step-0001-stdout.txt | /home/vasantha/AI-Projects/ClariFin_OS/runtime/generated/execution/step-0001-stderr.txt |

## Results Summary

- **Passed:** 0
- **Failed:** 1
- **Skipped:** 0
- **Total Duration:** 62.9s

## Failure Details

### step-0001
- Unit: `playwright-e2e`
- Classification: COMMAND_FAILURE
- Command: `bash .github/scripts/run_playwright_tests.sh`
- Exit code: 1
- Reason: ⚠ Warning: Next.js inferred your workspace root, but it may not be correct.  We detected multiple lockfiles and selected the directory of /home/vasantha/AI-Projects/ClariFin_OS/package-lock.json as the root directory.  To silence this warning, set `turbopack.root` in your Next.js config, or consider removing one of the lockfiles if it's not needed.    See https://nextjs.org/docs/app/api-reference/config/next-config-js/turbopack#root-directory for more information.  Detected additional lockfil...
- Full evidence: `/home/vasantha/AI-Projects/ClariFin_OS/runtime/generated/execution/step-0001-stderr.txt`


## Dependency Chains (Program 7A)

No dependency chains available (Program 7A cross-layer map not loaded).

## Evidence Files

No evidence files generated.

## Recommendations

- Investigate failing task: bash .github/scripts/run_playwright_tests.sh
