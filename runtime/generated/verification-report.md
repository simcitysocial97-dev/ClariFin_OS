# Verification Report

**Profile:** quick
**Generated:** 2026-08-07T17:35:16.071419+00:00
**Overall Status:** passed

## Changed Files

- `.github/scripts/run_fast_checks.sh`
- `.github/scripts/run_frontend_verification.sh`
- `.vscode/settings.json`
- `backend/diagnose_db.py`
- `backend/pyproject.toml`
- `backend/src/core/mappers/statement_mapper.py`
- `backend/src/engines/behavior_engine.py`
- `backend/src/engines/behaviour_engine/__init__.py`
- `backend/src/engines/behaviour_engine/core.py`
- `backend/src/engines/credit_card_engine/emi.py`
- `backend/src/engines/financial_intelligence/optimization.py`
- `backend/src/engines/insight_generator.py`
- `backend/src/engines/nudge_engine.py`
- `backend/src/main.py`
- `backend/src/routers/accounts.py`
- `backend/src/routers/cards_statements.py`
- `backend/src/services/cashflow_service.py`
- `backend/tests/audits/test_audit_minimal.py`
- `backend/tests/capability/pattern_analysis/test_capability.py`
- `backend/tests/conftest.py`
- `backend/tests/generated/capability-registry.yaml`
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
- `backend/tests/invariants/test_determinism.py`
- `backend/tests/invariants/test_reconciliation_determinism.py`
- `backend/tests/invariants/test_reconciliation_properties.py`
- `backend/tests/meta/test_change_intelligence.py`
- `backend/tests/meta/test_mutation_registry.py`
- `backend/tests/migrations/__init__.py`
- `backend/tests/migrations/test_migration_confidence_bps.py`
- `backend/tests/migrations/test_migration_household.py`
- `backend/tests/properties/behaviour/test_engine_properties.py`
- `backend/tests/properties/loan_engine/test_floating_rate_properties.py`
- `backend/tests/properties/loan_engine/test_prepayment_properties.py`
- `backend/tests/properties/recommendations/test_engine_properties.py`
- `backend/tests/unit/engines/behavior/test_behavior_engine.py`
- `backend/tests/unit/engines/credit_card/test_credit_card_engine.py`
- `backend/tests/unit/engines/reconciliation/test_reconciliation.py`
- `backend/tests/unit/repositories/test_account_balance_repository.py`
- `backend/tests/unit/repositories/test_account_link_repository.py`
- `backend/tests/unit/repositories/test_audit_repository.py`
- `backend/tests/unit/repositories/test_db.py`
- `backend/tests/unit/repositories/test_household_repository.py`
- `backend/tests/unit/repositories/test_institution_repository.py`
- `backend/tests/unit/services/test_services.py`
- `docs/EXECUTION_STATE.md`
- `frontend/app/command-center/page.tsx`
- `frontend/components/os-shell/__tests__/context-panel.test.tsx`
- `frontend/components/os-shell/context-panel.tsx`
- `frontend/eslint.config.mjs`
- `frontend/lib/design-system/__tests__/design-system.test.ts`
- `frontend/lib/design-system/tokens.ts`
- `frontend/lib/format.ts`
- `frontend/lib/mappers/credit-cards-mapper.ts`
- `frontend/lib/money.ts`
- `frontend/lib/search/index.ts`
- `frontend/lib/sort/index.ts`
- `frontend/lib/utils/format.ts`
- `frontend/tests/global-setup.ts`
- `frontend/types/financial.ts`
- `frontend/types/index.ts`
- `runtime/foundation/verification/planner/planner.py`
- `runtime/foundation/verification/registry/registry.py`
- `runtime/foundation/verification/verification.yaml`
- `runtime/generated/artifact-ownership.json`
- `runtime/generated/blast-radius.json`
- `runtime/generated/change-intelligence.json`
- `runtime/generated/cli-consistency.json`
- `runtime/generated/engineering-events.jsonl`
- `runtime/generated/engineering-history.json`
- `runtime/generated/engineering-memory.json`
- `runtime/generated/engineering-platform-audit-v5.json`
- `runtime/generated/engineering-platform-audit.json`
- `runtime/generated/engineering-platform-audit.md`
- `runtime/generated/engineering-risk.json`
- `runtime/generated/github-intelligence.json`
- `runtime/generated/intelligence-api.json`
- `runtime/generated/intelligence-constitution.json`
- `runtime/generated/intelligence-duplication.json`
- `runtime/generated/intelligence-inventory.json`
- `runtime/generated/intelligence-retirement-plan.json`
- `runtime/generated/knowledge-index.json`
- `runtime/generated/pipeline-certification.md`
- `runtime/generated/pipeline-validation.json`
- `runtime/generated/platform-state.json`
- `runtime/generated/program14.1-certification.md`
- `runtime/generated/repair-intelligence.json`
- `runtime/generated/runtime-simplification.json`
- `runtime/generated/system-health-score.json`
- `runtime/generated/test-resolution.json`
- `runtime/generated/verification-cache.json`
- `runtime/generated/verification-cost.json`
- `runtime/generated/verification-plan.json`
- `runtime/generated/verification-report.md`
- `runtime/tests/snapshots/verification-report.json`
- `tools/development/check_coverage.py`
- `tools/development/selective_verify.py`

## Blast Radius

- **affected_engines**: ['backend/src/engines/behaviour_engine', 'backend/src/engines/credit_card_engine', 'backend/src/engines/financial_intelligence', 'backend/src/engines/insight_generator.py', 'backend/src/engines/nudge_engine.py', 'backend/src/engines/account_engine', 'backend/src/engines/balance_engine.py']
- **affected_services**: ['backend/src/services/behaviour_service.py', 'backend/src/services/dashboard_service.py', 'backend/src/services/import_service.py', 'backend/src/services/credit_card_service.py', 'backend/src/services/financial_intelligence_service.py', 'backend/src/services/account_service.py', 'backend/src/services/statement_service.py']
- **affected_capabilities**: ['useBehaviourCapability', 'useCreditCardsCapability', 'useAccountsCapability']
- **affected_tests**: ['backend/tests/properties/behaviour/test_engine_properties.py', 'backend/tests/unit/engines/behaviour/test_core.py', 'backend/tests/unit/engines/behaviour/test_integration.py', 'backend/tests/unit/engines/behaviour/test_metrics.py', 'backend/tests/unit/engines/behaviour/test_patterns.py', 'backend/tests/properties/credit_card_engine/__init__.py', 'backend/tests/properties/credit_card_engine/test_billing_properties.py', 'backend/tests/properties/credit_card_engine/test_emi_properties.py', 'backend/tests/properties/credit_card_engine/test_interest_properties.py', 'backend/tests/properties/credit_cards/test_engine_properties.py', 'backend/tests/properties/lending/test_engine_properties.py', 'backend/tests/unit/engines/credit_card/test_credit_card_engine.py', 'backend/tests/properties/forecasting/test_engine_properties.py', 'backend/tests/properties/recommendations/test_engine_properties.py', 'backend/tests/unit/engines/account/test_account_engine.py', 'backend/tests/invariants/test_determinism.py']

## Verification Plan

- **Plan ID:** plan-20260807-173344
- **Scope:** quick
- **Targets:** 1
- **Steps:** 1
- **Estimated Duration:** 60s

## Tasks Executed

| Task ID | Name | Status | Duration |
|---------|------|--------|----------|
| step-0001 | bash .github/scripts/run_fast_checks.sh | passed | 91.5s |

## Results Summary

- **Passed:** 1
- **Failed:** 0
- **Skipped:** 0
- **Total Duration:** 91.5s

## Dependency Chains (Program 7A)

### backend/src/engines/behaviour_engine/__init__.py
- Engine: backend/src/engines/behaviour_engine
- Services: backend/src/services/behaviour_service.py, backend/src/services/dashboard_service.py, backend/src/services/import_service.py
- Endpoints: GET /cashflow-health, GET /debt-health, GET /monthly-report, GET /patterns, GET /profile
- Capabilities: useBehaviourCapability
- Tests: 5 affected

### backend/src/engines/behaviour_engine/core.py
- Engine: backend/src/engines/behaviour_engine
- Services: backend/src/services/behaviour_service.py, backend/src/services/dashboard_service.py, backend/src/services/import_service.py
- Endpoints: GET /cashflow-health, GET /debt-health, GET /monthly-report, GET /patterns, GET /profile
- Capabilities: useBehaviourCapability
- Tests: 5 affected

### backend/src/engines/credit_card_engine/emi.py
- Engine: backend/src/engines/credit_card_engine
- Services: backend/src/services/credit_card_service.py
- Endpoints: DELETE /credit-cards/{card_id}, GET /credit-cards, GET /credit-cards/{card_id}, GET /credit-cards/{card_id}/metrics, GET /credit-cards/{card_id}/next-statement-date
- Capabilities: useCreditCardsCapability
- Tests: 7 affected

### backend/src/engines/financial_intelligence/optimization.py
- Engine: backend/src/engines/financial_intelligence
- Services: backend/src/services/financial_intelligence_service.py
- Endpoints: GET /cashflow-forecast, GET /credit-forecast, GET /liquidity-forecast, GET /outlook, GET /priorities
- Tests: 1 affected

### backend/src/engines/insight_generator.py
- Engine: backend/src/engines/insight_generator.py

### backend/src/engines/nudge_engine.py
- Engine: backend/src/engines/nudge_engine.py
- Tests: 1 affected

### backend/src/routers/accounts.py
- Engine: backend/src/engines/account_engine
- Services: backend/src/services/account_service.py
- Endpoints: DELETE /accounts/manage/{account_id}, DELETE /accounts/{account_id}, DELETE /accounts/{account_id}/links/{linked_account_id}, GET /accounts, GET /accounts/manage
- Capabilities: useAccountsCapability
- Tests: 2 affected

### backend/src/routers/cards_statements.py
- Engine: backend/src/engines/balance_engine.py
- Services: backend/src/services/statement_service.py
- Tests: 1 affected

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

- Review changes in affected engines: backend/src/engines/behaviour_engine, backend/src/engines/credit_card_engine, backend/src/engines/financial_intelligence, backend/src/engines/insight_generator.py, backend/src/engines/nudge_engine.py, backend/src/engines/account_engine, backend/src/engines/balance_engine.py
