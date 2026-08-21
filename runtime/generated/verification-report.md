# Verification Report

**Profile:** backend
**Generated:** 2026-08-21T18:00:36.019702+00:00
**Overall Status:** passed

## Changed Files

- `.github/scripts/run_api_contracts.sh`
- `.github/scripts/run_playwright_tests.sh`
- `.github/workflows/api-contracts.yml`
- `.kilo/plans/1787137122047-health-check-timeout-fix.md`
- `activeContext.md`
- `backend/src/api.py`
- `backend/src/core/dtos/dashboard_dto.py`
- `backend/src/core/dtos/reconciliation_dto.py`
- `backend/src/core/dtos/transaction_dto.py`
- `backend/src/core/mappers/transaction_mapper.py`
- `backend/src/engines/loan_engine/prepayment.py`
- `backend/src/extraction/camelot_extractor.py`
- `backend/src/extraction/hybrid_extractor.py`
- `backend/src/routers/reconciliation.py`
- `backend/src/routers/transactions.py`
- `backend/src/services/behaviour_service.py`
- `backend/src/services/dashboard_service.py`
- `backend/src/services/transaction_service.py`
- `backend/src/startup.py`
- `backend/tests/generated/openapi-current.json`
- `backend/tests/unit/engines/loan/test_c39_regression.py`
- `backend/tests/unit/services/test_behaviour_service.py`
- `docs/M9-C10-forensic-report.md`
- `docs/architecture/FRONTEND_BACKEND_RUNTIME_INTEGRATION.md`
- `docs/evidence/m9-c32-preflight/api-contract-evidence-committed.json`
- `docs/evidence/m9-c32-preflight/api-contract-evidence-pre-c32.json`
- `docs/evidence/m9-c32-preflight/openapi-committed.json`
- `docs/evidence/m9-c32-preflight/openapi-corrupted.json`
- `frontend/__tests__/api-contracts/behavior.contract.test.ts`
- `frontend/__tests__/api-contracts/reconciliation.contract.test.ts`
- `frontend/__tests__/api-contracts/transactions.contract.test.ts`
- `frontend/app/dashboard/page.tsx`
- `frontend/app/layout.tsx`
- `frontend/components/dashboard/behavior-score-card.tsx`
- `frontend/components/os-shell/left-rail.tsx`
- `frontend/components/os-shell/right-inspector.tsx`
- `frontend/components/os-shell/top-command-bar.tsx`
- `frontend/components/os-shell/workspace-container.tsx`
- `frontend/components/primitives/panel/panel.tsx`
- `frontend/components/query-provider.tsx`
- `frontend/generated/openapi-current.json`
- `frontend/lib/__tests__/gateway-invariance.test.ts`
- `frontend/lib/api/client.ts`
- `frontend/lib/api/gateway.ts`
- `frontend/lib/capabilities/use-accounts-capability.ts`
- `frontend/lib/capabilities/use-behaviour-capability.ts`
- `frontend/lib/capabilities/use-cashflow-capability.ts`
- `frontend/lib/capabilities/use-credit-cards-capability.ts`
- `frontend/lib/capabilities/use-forecast-capability.ts`
- `frontend/lib/capabilities/use-investments-capability.ts`
- `frontend/lib/capabilities/use-loans-capability.ts`
- `frontend/lib/capabilities/use-net-worth-capability.ts`
- `frontend/lib/capabilities/use-reconciliation-capability.ts`
- `frontend/lib/capabilities/use-transaction-capability.ts`
- `frontend/lib/config/navigation.ts`
- `frontend/lib/hooks/use-accounts.ts`
- `frontend/lib/hooks/use-analytics.ts`
- `frontend/lib/hooks/use-behavior-score.ts`
- `frontend/lib/hooks/use-cards.ts`
- `frontend/lib/hooks/use-cashflow.ts`
- `frontend/lib/hooks/use-dashboard-metrics.ts`
- `frontend/lib/hooks/use-investments.ts`
- `frontend/lib/hooks/use-loans.ts`
- `frontend/lib/hooks/use-networth.ts`
- `frontend/lib/hooks/use-overview.ts`
- `frontend/lib/hooks/use-query-finance.ts`
- `frontend/lib/hooks/use-reconciliation.ts`
- `frontend/lib/mappers/behaviour-mapper.ts`
- `frontend/lib/mappers/transaction-mapper.ts`
- `frontend/lib/schemas/behavior-score.ts`
- `frontend/lib/schemas/cashflow.ts`
- `frontend/lib/schemas/dashboard-metrics.ts`
- `frontend/lib/schemas/overview.ts`
- `frontend/lib/schemas/transaction.ts`
- `frontend/middleware.ts`
- `frontend/mocks/fixtures/behavior.ts`
- `frontend/mocks/fixtures/dashboard.ts`
- `frontend/mocks/fixtures/transactions.ts`
- `frontend/mocks/handlers/behavior.ts`
- `frontend/mocks/handlers/reconciliation.ts`
- `frontend/next.config.ts`
- `frontend/playwright.config.ts`
- `frontend/proxy.ts`
- `frontend/tests/e2e/fixtures/css-helpers.ts`
- `frontend/tests/e2e/fixtures/test-fixtures.ts`
- `frontend/tests/e2e/specs/behavior-scoring.spec.ts`
- `frontend/tests/e2e/specs/behavior.spec.ts`
- `frontend/tests/e2e/specs/dashboard.spec.ts`
- `frontend/tests/e2e/specs/e2e-financial-logic.spec.ts`
- `frontend/tests/e2e/specs/edge-cases.spec.ts`
- `frontend/tests/e2e/specs/health-check.spec.ts`
- `frontend/tests/e2e/specs/navigation.spec.ts`
- `frontend/tests/e2e/specs/performance.spec.ts`
- `frontend/tests/e2e/specs/reconciliation.spec.ts`
- `frontend/tests/e2e/specs/transactions.spec.ts`
- `frontend/tests/e2e/specs/visual-regression.spec.ts`
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
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/upload-button-chromium-linux.png`
- `frontend/tests/global-setup.ts`
- `frontend/types/api-generated.ts`
- `frontend/types/transaction.ts`
- `memory-bank/activeContext.md`
- `progress.md`
- `runtime/foundation/verification/api_contracts/__init__.py`
- `runtime/foundation/verification/api_contracts/c30_certification.py`
- `runtime/foundation/verification/api_contracts/fixture.py`
- `runtime/foundation/verification/api_contracts/gate.py`
- `runtime/foundation/verification/api_contracts/inventory.py`
- `runtime/foundation/verification/api_contracts/mutations.py`
- `runtime/foundation/verification/api_contracts/normalize.py`
- `runtime/foundation/verification/api_contracts/taxonomy.py`
- `runtime/foundation/verification/models/model.py`
- `runtime/foundation/verification/totals.py`
- `runtime/system/evidence/collectors/test_results.py`
- `runtime/tests/test_backend_evidence.py`
- `runtime/tests/test_c37_certification_arithmetic.py`
- `runtime/verify.py`
- `test-results/.last-run.json`
- `tools/e2e_seed.py`
- `.kilo/plans/1787286911071-c43-remaining-issues-plan.md`
- `backend/tests/probes/test_m4_exit_probe.py`
- `dependency-reports/dependency-health.md`
- `dependency-reports/npm-audit.txt`
- `dependency-reports/npm-outdated.json`
- `dependency-reports/python-audit.txt`
- `frontend/tests/e2e/snapshots/historical/analytics-mobile-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/analytics-mobile-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/analytics-page-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/analytics-page-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/behavior-page-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/behavior-page-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/cards-page-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/cards-page-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/categories-mobile-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/categories-mobile-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/categories-page-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/categories-page-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/dark-mode-dashboard-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/dark-mode-dashboard-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/dashboard-mobile-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/dashboard-mobile-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/dashboard-page-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/dashboard-page-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/family-mode-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/family-mode-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/header-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/header-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/home-mobile-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/home-mobile-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/home-page-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/home-page-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/import-page-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/import-page-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/mode-toggle-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/mode-toggle-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/personal-mode-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/personal-mode-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/reconciliation-page-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/reconciliation-page-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/settings-page-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/settings-page-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/sidebar-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/sidebar-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/transactions-mobile-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/transactions-mobile-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/transactions-page-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/transactions-page-tablet-linux.png`
- `frontend/tests/e2e/snapshots/historical/upload-button-firefox-linux.png`
- `frontend/tests/e2e/snapshots/historical/upload-button-tablet-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/analytics-mobile-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/analytics-page-firefox-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/analytics-page-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/behavior-page-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/cards-page-firefox-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/cards-page-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/categories-mobile-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/categories-page-firefox-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/categories-page-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/dark-mode-dashboard-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/dashboard-mobile-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/dashboard-page-firefox-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/dashboard-page-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/family-mode-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/header-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/home-mobile-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/home-page-firefox-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/home-page-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/import-page-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/personal-mode-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/reconciliation-page-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/settings-page-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/sidebar-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/transactions-mobile-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/transactions-page-firefox-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/transactions-page-mobile-chrome-linux.png`
- `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/upload-button-mobile-chrome-linux.png`
- `runtime/foundation/verification/product-support.md`

## Blast Radius

- **affected_engines**: ['backend/src/engines/loan_engine', 'backend/src/engines/reconciliation_engine.py', 'backend/src/engines/behaviour_engine', 'backend/src/engines/account_engine', 'backend/src/engines/credit_card_engine']
- **affected_services**: ['backend/src/services/loan_analysis_service.py', 'backend/src/services/loan_service.py', 'backend/src/services/loan_simulation_service.py', 'backend/src/services/transaction_intelligence_service.py', 'backend/src/services/reconciliation_service.py', 'backend/src/services/behaviour_service.py', 'backend/src/services/dashboard_service.py', 'backend/src/services/import_service.py', 'backend/src/services/account_service.py', 'backend/src/services/credit_card_service.py', 'service:backend/src/services/transaction_service.py', 'service:backend/src/services/dashboard_service.py', 'service:backend/src/services/import_service.py', 'service:backend/src/services/__init__.py']
- **affected_capabilities**: ['useLoansCapability', 'useReconciliationCapability', 'useBehaviourCapability', 'useAccountsCapability', 'useCreditCardsCapability', 'capability:useCashflowCapability', 'capability:useForecastCapability', 'capability:useInvestmentsCapability', 'capability:useNetWorthCapability', 'capability:useTransactionCapability', 'capability:useBehaviourCapability', 'capability:useReconciliationCapability', 'capability:useLoansCapability']
- **affected_tests**: ['backend/tests/properties/lending/test_engine_properties.py', 'backend/tests/properties/loan_engine/__init__.py', 'backend/tests/properties/loan_engine/test_amortization_properties.py', 'backend/tests/properties/loan_engine/test_emi_properties.py', 'backend/tests/properties/loan_engine/test_floating_rate_properties.py', 'backend/tests/properties/loan_engine/test_foreclosure_properties.py', 'backend/tests/properties/loan_engine/test_metrics_properties.py', 'backend/tests/properties/loan_engine/test_prepayment_properties.py', 'backend/tests/unit/engines/loan/test_amortization.py', 'backend/tests/unit/engines/loan/test_loan_engine.py', 'backend/tests/invariants/test_reconciliation_determinism.py', 'backend/tests/invariants/test_reconciliation_properties.py', 'backend/tests/properties/reconciliation/test_engine_properties.py', 'backend/tests/unit/engines/reconciliation/test_reconciliation.py', 'backend/tests/capability/pattern_analysis/test_capability.py', 'backend/tests/properties/behaviour/test_engine_properties.py', 'backend/tests/properties/recommendations/test_engine_properties.py', 'backend/tests/unit/engines/behavior/test_behavior_engine.py', 'backend/tests/unit/engines/behaviour/test_core.py', 'backend/tests/unit/engines/behaviour/test_integration.py', 'backend/tests/unit/engines/behaviour/test_metrics.py', 'backend/tests/unit/engines/behaviour/test_patterns.py', 'backend/tests/unit/engines/account/test_account_engine.py', 'backend/tests/properties/credit_card_engine/__init__.py', 'backend/tests/properties/credit_card_engine/test_billing_properties.py', 'backend/tests/properties/credit_card_engine/test_emi_properties.py', 'backend/tests/properties/credit_card_engine/test_interest_properties.py', 'backend/tests/properties/credit_cards/test_engine_properties.py', 'backend/tests/unit/engines/credit_card/test_credit_card_engine.py']

## Verification Plan

- **Plan ID:** plan-20260821-175234
- **Scope:** backend
- **Targets:** 10
- **Steps:** 4
- **Estimated Duration:** 660s

## Tasks Executed

| Task ID | Command | Status | Exit | Duration | Error | Stdout | Stderr |
|---------|---------|--------|------|----------|-------|--------|--------|
| step-0001 | bash .github/scripts/run_backend_verification.sh | VerificationStatus.PASSED | 0 | 83.9s |  | /home/vasantha/AI-Projects/ClariFin_OS/runtime/generated/execution/step-0001-stdout.txt | /home/vasantha/AI-Projects/ClariFin_OS/runtime/generated/execution/step-0001-stderr.txt |
| step-0002 | bash .github/scripts/run_fast_checks.sh | VerificationStatus.PASSED | 0 | 61.3s |  | /home/vasantha/AI-Projects/ClariFin_OS/runtime/generated/execution/step-0002-stdout.txt | /home/vasantha/AI-Projects/ClariFin_OS/runtime/generated/execution/step-0002-stderr.txt |
| step-0003 | bash .github/scripts/run_frontend_verification.sh | VerificationStatus.PASSED | 0 | 173.8s |  | /home/vasantha/AI-Projects/ClariFin_OS/runtime/generated/execution/step-0003-stdout.txt | /home/vasantha/AI-Projects/ClariFin_OS/runtime/generated/execution/step-0003-stderr.txt |
| step-0004 | bash .github/scripts/run_runtime_verification.sh | VerificationStatus.PASSED | 0 | 163.0s |  | /home/vasantha/AI-Projects/ClariFin_OS/runtime/generated/execution/step-0004-stdout.txt | /home/vasantha/AI-Projects/ClariFin_OS/runtime/generated/execution/step-0004-stderr.txt |

## Results Summary

- **Passed:** 4
- **Failed:** 0
- **Skipped:** 0
- **Total Duration:** 482.0s


## Dependency Chains (Program 7A)

### backend/src/engines/loan_engine/prepayment.py
- Engine: backend/src/engines/loan_engine
- Services: backend/src/services/loan_analysis_service.py, backend/src/services/loan_service.py, backend/src/services/loan_simulation_service.py, backend/src/services/transaction_intelligence_service.py
- Endpoints: DELETE /loans/{loan_id}, GET /loans, GET /loans/analysis/priority, GET /loans/{loan_id}, GET /loans/{loan_id}/schedule
- Capabilities: useLoansCapability
- Tests: 10 affected

### backend/src/routers/reconciliation.py
- Engine: backend/src/engines/reconciliation_engine.py
- Services: backend/src/services/reconciliation_service.py
- Endpoints: GET /pending, GET /scan, POST /batch-insert, POST /create, POST /{reconciliation_id}/confirm
- Capabilities: useReconciliationCapability
- Tests: 4 affected

### backend/src/services/behaviour_service.py
- Engine: backend/src/engines/behaviour_engine
- Services: backend/src/services/behaviour_service.py, backend/src/services/dashboard_service.py, backend/src/services/import_service.py
- Endpoints: GET /cashflow-health, GET /debt-health, GET /monthly-report, GET /patterns, GET /profile
- Capabilities: useBehaviourCapability
- Tests: 8 affected

### backend/src/services/dashboard_service.py
- Engine: backend/src/engines/behaviour_engine
- Services: backend/src/services/behaviour_service.py, backend/src/services/dashboard_service.py, backend/src/services/import_service.py
- Endpoints: GET /cashflow-health, GET /debt-health, GET /monthly-report, GET /patterns, GET /profile
- Capabilities: useBehaviourCapability
- Tests: 8 affected

### frontend/components/primitives/panel/panel.tsx
- Engine: backend/src/engines/account_engine
- Services: backend/src/services/account_service.py
- Endpoints: DELETE /accounts/manage/{account_id}, DELETE /accounts/{account_id}, DELETE /accounts/{account_id}/links/{linked_account_id}, GET /accounts, GET /accounts/manage
- Capabilities: useAccountsCapability
- Tests: 2 affected

### frontend/lib/capabilities/use-accounts-capability.ts
- Engine: backend/src/engines/account_engine
- Services: backend/src/services/account_service.py
- Endpoints: DELETE /accounts/manage/{account_id}, DELETE /accounts/{account_id}, DELETE /accounts/{account_id}/links/{linked_account_id}, GET /accounts, GET /accounts/manage
- Capabilities: useAccountsCapability
- Tests: 2 affected

### frontend/lib/capabilities/use-behaviour-capability.ts
- Engine: backend/src/engines/behaviour_engine
- Services: backend/src/services/behaviour_service.py, backend/src/services/dashboard_service.py, backend/src/services/import_service.py
- Endpoints: GET /cashflow-health, GET /debt-health, GET /monthly-report, GET /patterns, GET /profile
- Capabilities: useBehaviourCapability
- Tests: 8 affected

### frontend/lib/capabilities/use-credit-cards-capability.ts
- Engine: backend/src/engines/credit_card_engine
- Services: backend/src/services/credit_card_service.py
- Endpoints: DELETE /credit-cards/{card_id}, GET /credit-cards, GET /credit-cards/{card_id}, GET /credit-cards/{card_id}/metrics, GET /credit-cards/{card_id}/next-statement-date
- Capabilities: useCreditCardsCapability
- Tests: 7 affected

### frontend/lib/capabilities/use-loans-capability.ts
- Engine: backend/src/engines/loan_engine
- Services: backend/src/services/loan_analysis_service.py, backend/src/services/loan_service.py, backend/src/services/loan_simulation_service.py, backend/src/services/transaction_intelligence_service.py
- Endpoints: DELETE /loans/{loan_id}, GET /loans, GET /loans/analysis/priority, GET /loans/{loan_id}, GET /loans/{loan_id}/schedule
- Capabilities: useLoansCapability
- Tests: 10 affected

### frontend/lib/capabilities/use-reconciliation-capability.ts
- Engine: backend/src/engines/reconciliation_engine.py
- Services: backend/src/services/reconciliation_service.py
- Endpoints: GET /pending, GET /scan, POST /batch-insert, POST /create, POST /{reconciliation_id}/confirm
- Capabilities: useReconciliationCapability
- Tests: 4 affected

## Evidence Files

No evidence files generated.

## Recommendations

- Review changes in affected engines: backend/src/engines/loan_engine, backend/src/engines/reconciliation_engine.py, backend/src/engines/behaviour_engine, backend/src/engines/account_engine, backend/src/engines/credit_card_engine
