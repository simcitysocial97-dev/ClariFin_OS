# Verification Report

**Profile:** quick
**Generated:** 2026-08-05T12:05:59.567468+00:00
**Overall Status:** failed

## Changed Files

- `.github/actions/job-summary/action.yml`
- `.github/actions/setup-node-env/action.yml`
- `.github/actions/setup-python-env/action.yml`
- `.github/actions/upload-test-artifacts/action.yml`
- `.github/scripts/run_fast_checks.sh`
- `.github/scripts/run_mutation_selective.sh`
- `.github/workflows/backend-verify.yml`
- `.github/workflows/backend.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/frontend-build.yml`
- `.github/workflows/frontend.yml`
- `.github/workflows/full-validation.yml`
- `.github/workflows/golden.yml`
- `.github/workflows/mutation.yml`
- `.github/workflows/nightly-property-tests.yml`
- `.github/workflows/playwright.yml`
- `.github/workflows/quality.yml`
- `docs/EXECUTION_STATE.md`
- `frontend/components/global-search/search-provider.tsx`
- `frontend/lib/validation/__tests__/performance.test.tsx`
- `frontend/styles/financial-os.css`
- `runtime/foundation/verification/__init__.py`
- `runtime/foundation/verification/models/__init__.py`
- `runtime/foundation/verification/models/model.py`
- `runtime/foundation/verification/planner/planner.py`
- `runtime/foundation/verification/registry/registry.py`
- `runtime/foundation/verification/verification.yaml`

## Blast Radius

- **affected_engines**: []
- **affected_services**: []
- **affected_capabilities**: []
- **affected_tests**: []

## Verification Plan

- **Plan ID:** plan-20260805-120542
- **Scope:** quick
- **Targets:** 10
- **Steps:** 10
- **Estimated Duration:** 9480s

## Tasks Executed

| Task ID | Name | Status | Duration |
|---------|------|--------|----------|
| step-0001 | .github/scripts/run_contract_tests.sh | failed | 0.0s |
| step-0002 | .github/scripts/run_contract_tests.sh | failed | 0.0s |
| step-0003 | bash .github/scripts/run_migration_verification.sh | failed | 0.0s |
| step-0004 | .github/scripts/run_contract_tests.sh | failed | 0.0s |
| step-0005 | .github/scripts/run_contract_tests.sh | failed | 0.0s |
| step-0006 | bash .github/scripts/run_runtime_verification.sh | passed | 17.1s |
| step-0007 | .github/scripts/run_contract_tests.sh | failed | 0.0s |
| step-0008 | .github/scripts/run_contract_tests.sh | failed | 0.0s |
| step-0009 | .github/scripts/run_fast_checks.sh | failed | 0.0s |
| step-0010 | .github/scripts/run_contract_tests.sh | failed | 0.0s |

## Results Summary

- **Passed:** 1
- **Failed:** 9
- **Skipped:** 0
- **Total Duration:** 17.1s

## Dependency Chains (Program 7A)

No dependency chains available (Program 7A cross-layer map not loaded).

## Evidence Files

- `runtime/generated/verification/samples/contract_partial.json`
- `runtime/generated/verification/samples/coverage_empty.json`
- `runtime/generated/verification/samples/run_aggregator_tests.py`
- `runtime/generated/verification/samples/summary.md`
- `runtime/generated/verification/samples/run_collector_tests.py`
- `runtime/generated/verification/samples/contract_valid.json`
- `runtime/generated/verification/samples/junit_partial.xml`
- `runtime/generated/verification/samples/coverage_invalid.json`
- `runtime/generated/verification/samples/junit_valid.xml`
- `runtime/generated/verification/samples/coverage_valid.json`
- `runtime/generated/verification/samples/contract_invalid.json`
- `runtime/generated/verification/samples/contract_empty.json`
- `runtime/generated/verification/samples/junit_empty.xml`
- `runtime/generated/verification/samples/junit_invalid.xml`
- `runtime/generated/verification/samples/coverage_partial.json`
- `runtime/generated/verification/samples/summary.json`
- `runtime/generated/verification/samples/mutation_invalid/loan-results.txt`
- `runtime/generated/verification/samples/mutation_invalid/mutation-summary.json`
- `runtime/generated/verification/samples/mutation_valid/loan-results.txt`
- `runtime/generated/verification/samples/mutation_valid/mutation-summary.json`
- `runtime/generated/verification/samples/partial_evidence/test-results/junit.xml`
- `runtime/generated/verification/samples/evidence_dir/test-results/junit.xml`
- `runtime/generated/verification/samples/evidence_dir/coverage/coverage.json`
- `runtime/generated/verification/samples/evidence_dir/mutation/loan-results.txt`
- `runtime/generated/verification/samples/evidence_dir/mutation/mutation-summary.json`
- `runtime/generated/verification/samples/evidence_dir/contract/contract.json`
- `runtime/generated/verification/samples/evidence_dir/backend/tests/generated/junit-property.xml`

## Recommendations

- Investigate failing task: .github/scripts/run_contract_tests.sh
- Investigate failing task: .github/scripts/run_contract_tests.sh
- Investigate failing task: bash .github/scripts/run_migration_verification.sh
- Investigate failing task: .github/scripts/run_contract_tests.sh
- Investigate failing task: .github/scripts/run_contract_tests.sh
- Investigate failing task: .github/scripts/run_contract_tests.sh
- Investigate failing task: .github/scripts/run_contract_tests.sh
- Investigate failing task: .github/scripts/run_fast_checks.sh
- Investigate failing task: .github/scripts/run_contract_tests.sh
