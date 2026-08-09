# Verification Report

**Profile:** contracts
**Generated:** 2026-08-09T11:51:29.971044+00:00
**Overall Status:** failed

## Changed Files

- `runtime/generated/engineering-events.jsonl`
- `runtime/generated/engineering-history.json`
- `runtime/generated/knowledge-index.json`
- `runtime/generated/verification-cache.json`
- `runtime/generated/verification-report.md`

## Blast Radius

- **affected_engines**: []
- **affected_services**: []
- **affected_capabilities**: []
- **affected_tests**: []

## Verification Plan

- **Plan ID:** plan-20260809-114910
- **Scope:** contracts
- **Targets:** 6
- **Steps:** 3
- **Estimated Duration:** 480s

## Tasks Executed

| Task ID | Name | Status | Duration |
|---------|------|--------|----------|
| step-0001 | bash .github/scripts/run_fast_checks.sh | passed | 63.3s |
| step-0002 | bash .github/scripts/run_backend_verification.sh | failed | 59.3s |
| step-0003 | bash .github/scripts/run_runtime_verification.sh | passed | 17.1s |

## Results Summary

- **Passed:** 2
- **Failed:** 1
- **Skipped:** 0
- **Total Duration:** 139.8s

## Dependency Chains (Program 7A)

No dependency chains available (Program 7A cross-layer map not loaded).

## Evidence Files

No evidence files generated.

## Recommendations

- Investigate failing task: bash .github/scripts/run_backend_verification.sh
