# Verification Report

**Profile:** backend
**Generated:** 2026-08-08T15:43:50.978768+00:00
**Overall Status:** failed

## Changed Files

- `.gitignore`
- `backend/.gitignore`
- `backend/tests/fixtures/benchmark_fixtures.py`
- `backend/tests/generated/change-report.json`
- `backend/tests/generated/change-report.md`
- `backend/tests/generated/contract-coverage.json`
- `backend/tests/generated/mutation-gaps.md`
- `backend/tests/generated/mutation-map.json`
- `backend/tests/generated/mutation-readiness.json`
- `backend/tests/generated/mutation-readiness.md`
- `backend/tests/generated/mutation-registry.json`
- `backend/tests/generated/selective-plan.md`
- `backend/tests/generated/test-plan.md`
- `backend/tests/generated/test-strength.json`
- `backend/tests/generated/test-strength.md`
- `backend/tests/generated/validation-manifest.json`
- `backend/tests/generated/verification-matrix.md`
- `frontend/components/cards/credit-card-3d.tsx`
- `frontend/components/error-boundary.tsx`
- `frontend/components/primitives/inspector-block/inspector-block.tsx`
- `frontend/components/ui/empty-state.tsx`
- `frontend/eslint.config.mjs`
- `frontend/lib/capabilities/__tests__/contract.test.ts`
- `frontend/lib/context/member-context.tsx`
- `frontend/lib/graph/financial-graph-model.ts`
- `frontend/lib/hooks/use-cards.ts`
- `frontend/lib/hooks/use-query-finance.ts`
- `frontend/lib/hooks/use-reconciliation.ts`
- `frontend/lib/intelligence/passive-runtime.ts`
- `frontend/lib/parser/index.ts`
- `frontend/lib/runtime/runtime-provider.tsx`
- `frontend/lib/runtime/workspace-runtime.ts`
- `frontend/lib/scenario/runtime.ts`
- `frontend/lib/workspace/workspace-provider.tsx`
- `runtime/analyze_architecture.py`
- `runtime/analyze_engine_normalization.py`
- `runtime/analyze_engine_topology.py`
- `runtime/analyze_execution.py`
- `runtime/analyze_ownership.py`
- `runtime/generated/architecture-inventory-summary.json`
- `runtime/generated/architecture-inventory.json`
- `runtime/generated/architecture-provider.json`
- `runtime/generated/engine-normalization.json`
- `runtime/generated/engine-topology.json`
- `runtime/generated/engineering-events.jsonl`
- `runtime/generated/engineering-history.json`
- `runtime/generated/execution-graph.json`
- `runtime/generated/knowledge-index.json`
- `runtime/generated/ownership-graph.json`
- `runtime/generated/verification-cache.json`
- `runtime/generated/verification-report.md`

## Blast Radius

- **affected_engines**: []
- **affected_services**: []
- **affected_capabilities**: []
- **affected_tests**: []

## Verification Plan

- **Plan ID:** plan-20260808-153953
- **Scope:** backend
- **Targets:** 3
- **Steps:** 3
- **Estimated Duration:** 480s

## Tasks Executed

| Task ID | Name | Status | Duration |
|---------|------|--------|----------|
| step-0001 | bash .github/scripts/run_fast_checks.sh | passed | 100.2s |
| step-0002 | bash .github/scripts/run_backend_verification.sh | failed | 108.5s |
| step-0003 | bash .github/scripts/run_runtime_verification.sh | passed | 28.3s |

## Results Summary

- **Passed:** 2
- **Failed:** 1
- **Skipped:** 0
- **Total Duration:** 237.0s

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

- Investigate failing task: bash .github/scripts/run_backend_verification.sh
