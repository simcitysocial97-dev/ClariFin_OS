# Change Impact Report

Generated: 2026-07-28T03:59:18.182266+00:00

## Summary

| File | Risk | Capabilities | Confidence |
|------|------|--------------|------------|
| `.github/actions/setup-python-env/action.yml` | LOW | UNKNOWN | LOW |
| `.github/workflows/backend.yml` | LOW | UNKNOWN | LOW |
| `.github/workflows/mutation.yml` | LOW | UNKNOWN | LOW |
| `.github/workflows/nightly-property-tests.yml` | LOW | UNKNOWN | LOW |
| `.github/workflows/quality.yml` | LOW | UNKNOWN | LOW |
| `backend/.coverage` | LOW | UNKNOWN | LOW |
| `backend/html/index.html` | LOW | UNKNOWN | LOW |
| `backend/html/src/engines/cashflow_engine.py.html` | CRITICAL | household_cashflow | LOW |
| `backend/requirements-frozen.txt` | LOW | UNKNOWN | LOW |
| `backend/scripts/migration_007_reconciliation_audit.py` | HIGH | UNKNOWN | LOW |
| `backend/src/api.py` | LOW | UNKNOWN | LOW |
| `backend/src/common/database.py` | LOW | UNKNOWN | LOW |
| `backend/src/config.py` | LOW | UNKNOWN | LOW |
| `backend/src/data/finance.db` | LOW | UNKNOWN | LOW |
| `backend/src/db.py` | LOW | UNKNOWN | LOW |
| `backend/src/engines/cashflow_engine.py` | CRITICAL | household_cashflow | HIGH |
| `backend/src/engines/loan_engine/amortization.py` | CRITICAL | debt_management | HIGH |
| `backend/src/engines/loan_engine/emi.py` | CRITICAL | debt_management | HIGH |
| `backend/src/models/account_balance.py` | LOW | UNKNOWN | LOW |
| `backend/src/models/account_link.py` | LOW | UNKNOWN | LOW |
| `backend/src/models/transaction.py` | LOW | UNKNOWN | LOW |
| `backend/src/repositories/account_balance_repository.py` | HIGH | account_management | HIGH |
| `backend/src/repositories/account_link_repository.py` | HIGH | account_management | HIGH |
| `backend/src/repositories/base.py` | HIGH | UNKNOWN | LOW |
| `backend/src/repositories/investment_repository.py` | HIGH | UNKNOWN | LOW |
| `backend/src/repositories/loan_repository.py` | HIGH | debt_management | HIGH |
| `backend/src/repositories/pattern_repository.py` | HIGH | pattern_analysis, transaction_intelligence | HIGH |
| `backend/src/repositories/reconciliation_repository.py` | HIGH | reconciliation | HIGH |
| `backend/src/repositories/transaction_repository.py` | HIGH | transaction_intelligence | HIGH |
| `backend/src/routers/financial_events.py` | MEDIUM | UNKNOWN | LOW |
| `backend/src/routers/reconciliation.py` | MEDIUM | reconciliation | HIGH |
| `backend/src/services/account_service.py` | MEDIUM | account_management | HIGH |
| `backend/src/services/base.py` | MEDIUM | UNKNOWN | LOW |
| `backend/tests/audits/test_audit_minimal.py` | LOW | UNKNOWN | LOW |
| `backend/tests/conftest.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_accounts.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_analytics.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_audit.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_banks.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_cards.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_cashflow.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_categories.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_dashboard.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_export.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_financial_events.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_import.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_investments.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_loans.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_members.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_networth.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_overview.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_reconciliations.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_statements.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_transactions.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_upload.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_v1.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/schema_validators.py` | HIGH | UNKNOWN | LOW |
| `backend/tests/generated/capability-registry.yaml` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/change-impact.md` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/change-report.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/change-report.md` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/coverage.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/mutation-gaps.md` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/mutation-map.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/mutation-readiness.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/mutation-readiness.md` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/mutation-registry.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/selective-history.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/selective-plan.md` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/selective-summary.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/test-plan.md` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/test-strength.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/test-strength.md` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/traceability.md` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/validation-manifest.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/verification-matrix.md` | LOW | UNKNOWN | LOW |
| `backend/tests/integration/e2e/test_statement_upload_pipeline.py` | LOW | UNKNOWN | LOW |
| `backend/tests/invariants/test_determinism.py` | LOW | UNKNOWN | LOW |
| `backend/tests/invariants/test_reconciliation_determinism.py` | LOW | UNKNOWN | LOW |
| `backend/tests/meta/test_selective_verify.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/behaviour/test_engine_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/forecasting/test_engine_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/reconciliation/test_engine_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/unit/engines/account/test_account_engine.py` | HIGH | UNKNOWN | LOW |
| `backend/tests/unit/engines/behaviour/test_core.py` | CRITICAL | UNKNOWN | LOW |
| `backend/tests/unit/engines/behaviour/test_integration.py` | CRITICAL | UNKNOWN | LOW |
| `backend/tests/unit/engines/behaviour/test_metrics.py` | CRITICAL | UNKNOWN | LOW |
| `backend/tests/unit/engines/behaviour/test_patterns.py` | CRITICAL | UNKNOWN | LOW |
| `backend/tests/unit/engines/loan/test_amortization.py` | CRITICAL | UNKNOWN | LOW |
| `backend/tests/unit/engines/loan/test_loan_engine.py` | CRITICAL | UNKNOWN | LOW |
| `backend/tests/unit/engines/recommendation/test_recommendation_engine.py` | HIGH | UNKNOWN | LOW |
| `backend/tests/unit/engines/reconciliation/test_reconciliation.py` | HIGH | UNKNOWN | LOW |
| `backend/tests/unit/repositories/test_account_balance_repository.py` | HIGH | UNKNOWN | LOW |
| `backend/tests/unit/repositories/test_account_link_repository.py` | HIGH | UNKNOWN | LOW |
| `backend/tests/unit/repositories/test_pattern_repository.py` | HIGH | UNKNOWN | LOW |
| `backend/tools/check_coverage.py` | LOW | UNKNOWN | LOW |
| `backend/tools/generate_contract_tests.py` | LOW | UNKNOWN | LOW |
| `backend/tools/selective_verify.py` | LOW | UNKNOWN | LOW |
| `memory-bank/activeContext.md` | LOW | UNKNOWN | LOW |
| `servers` | LOW | UNKNOWN | LOW |

## Detailed Analysis

### Changed: `.github/actions/setup-python-env/action.yml`

**Risk:** LOW

**Confidence:** LOW


### Changed: `.github/workflows/backend.yml`

**Risk:** LOW

**Confidence:** LOW


### Changed: `.github/workflows/mutation.yml`

**Risk:** LOW

**Confidence:** LOW


### Changed: `.github/workflows/nightly-property-tests.yml`

**Risk:** LOW

**Confidence:** LOW


### Changed: `.github/workflows/quality.yml`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/.coverage`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/html/index.html`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/html/src/engines/cashflow_engine.py.html`

**Risk:** CRITICAL

**Confidence:** LOW

**Affected Capabilities:**

- `household_cashflow`


### Changed: `backend/requirements-frozen.txt`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/scripts/migration_007_reconciliation_audit.py`

**Risk:** HIGH

**Confidence:** LOW


### Changed: `backend/src/api.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/common/database.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/config.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/data/finance.db`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/db.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/engines/cashflow_engine.py`

**Risk:** CRITICAL

**Confidence:** HIGH

**Affected Capabilities:**

- `household_cashflow`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capability/household_cashflow`
  - Property Tests:
    - `tests/properties/cashflow`
  - Golden Datasets:
    - `family_household`
    - `normal_household`
    - `salary_only`
    - `salary_plus_loan`
  - Invariants:
    - `tests/invariants/test_cashflow_invariants.py`

**Recommended Verification:**
```bash
pytest tests/capability/household_cashflow -q
pytest tests/properties/cashflow -q
pytest tests/golden -k 'family_household,normal_household,salary_only' -q
```

### Changed: `backend/src/engines/loan_engine/amortization.py`

**Risk:** CRITICAL

**Confidence:** HIGH

**Affected Capabilities:**

- `debt_management`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capability/debt_management`
  - Property Tests:
    - `tests/properties/lending`
  - Golden Datasets:
    - `high_debt_household`
    - `multiple_loans`
    - `salary_plus_loan`
  - Invariants:
    - `tests/invariants/test_loan.py`

**Recommended Verification:**
```bash
pytest tests/capability/debt_management -q
pytest tests/properties/lending -q
pytest tests/golden -k 'high_debt_household,multiple_loans,salary_plus_loan' -q
```

### Changed: `backend/src/engines/loan_engine/emi.py`

**Risk:** CRITICAL

**Confidence:** HIGH

**Affected Capabilities:**

- `debt_management`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capability/debt_management`
  - Property Tests:
    - `tests/properties/lending`
  - Golden Datasets:
    - `high_debt_household`
    - `multiple_loans`
    - `salary_plus_loan`
  - Invariants:
    - `tests/invariants/test_loan.py`

**Recommended Verification:**
```bash
pytest tests/capability/debt_management -q
pytest tests/properties/lending -q
pytest tests/golden -k 'high_debt_household,multiple_loans,salary_plus_loan' -q
```

### Changed: `backend/src/models/account_balance.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/models/account_link.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/models/transaction.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/repositories/account_balance_repository.py`

**Risk:** HIGH

**Confidence:** HIGH

**Affected Capabilities:**

- `account_management`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capability/account_management`

**Recommended Verification:**
```bash
pytest tests/capability/account_management -q
```

### Changed: `backend/src/repositories/account_link_repository.py`

**Risk:** HIGH

**Confidence:** HIGH

**Affected Capabilities:**

- `account_management`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capability/account_management`

**Recommended Verification:**
```bash
pytest tests/capability/account_management -q
```

### Changed: `backend/src/repositories/base.py`

**Risk:** HIGH

**Confidence:** LOW


### Changed: `backend/src/repositories/investment_repository.py`

**Risk:** HIGH

**Confidence:** LOW


### Changed: `backend/src/repositories/loan_repository.py`

**Risk:** HIGH

**Confidence:** HIGH

**Affected Capabilities:**

- `debt_management`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capability/debt_management`

**Recommended Verification:**
```bash
pytest tests/capability/debt_management -q
```

### Changed: `backend/src/repositories/pattern_repository.py`

**Risk:** HIGH

**Confidence:** HIGH

**Affected Capabilities:**

- `pattern_analysis`
- `transaction_intelligence`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capability/pattern_analysis`
    - `tests/capability/transaction_intelligence`

**Recommended Verification:**
```bash
pytest tests/capability/pattern_analysis -q
pytest tests/capability/transaction_intelligence -q
```

### Changed: `backend/src/repositories/reconciliation_repository.py`

**Risk:** HIGH

**Confidence:** HIGH

**Affected Capabilities:**

- `reconciliation`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capability/reconciliation`

**Recommended Verification:**
```bash
pytest tests/capability/reconciliation -q
```

### Changed: `backend/src/repositories/transaction_repository.py`

**Risk:** HIGH

**Confidence:** HIGH

**Affected Capabilities:**

- `transaction_intelligence`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capability/transaction_intelligence`

**Recommended Verification:**
```bash
pytest tests/capability/transaction_intelligence -q
```

### Changed: `backend/src/routers/financial_events.py`

**Risk:** MEDIUM

**Confidence:** LOW


### Changed: `backend/src/routers/reconciliation.py`

**Risk:** MEDIUM

**Confidence:** HIGH

**Affected Capabilities:**

- `reconciliation`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capability/reconciliation`
  - Property Tests:
    - `tests/properties/reconciliation`

**Recommended Verification:**
```bash
pytest tests/capability/reconciliation -q
pytest tests/properties/reconciliation -q
```

### Changed: `backend/src/services/account_service.py`

**Risk:** MEDIUM

**Confidence:** HIGH

**Affected Capabilities:**

- `account_management`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capability/account_management`

**Recommended Verification:**
```bash
pytest tests/capability/account_management -q
```

### Changed: `backend/src/services/base.py`

**Risk:** MEDIUM

**Confidence:** LOW


### Changed: `backend/tests/audits/test_audit_minimal.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/conftest.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_accounts.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_analytics.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_audit.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_banks.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_cards.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_cashflow.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_categories.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_dashboard.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_export.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_financial_events.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_import.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_investments.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_loans.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_members.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_networth.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_overview.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_reconciliations.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_statements.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_transactions.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_upload.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_v1.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/schema_validators.py`

**Risk:** HIGH

**Confidence:** LOW


### Changed: `backend/tests/generated/capability-registry.yaml`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/change-impact.md`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/change-report.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/change-report.md`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/coverage.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/mutation-gaps.md`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/mutation-map.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/mutation-readiness.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/mutation-readiness.md`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/mutation-registry.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/selective-history.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/selective-plan.md`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/selective-summary.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/test-plan.md`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/test-strength.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/test-strength.md`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/traceability.md`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/validation-manifest.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/verification-matrix.md`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/integration/e2e/test_statement_upload_pipeline.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/invariants/test_determinism.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/invariants/test_reconciliation_determinism.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/meta/test_selective_verify.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/behaviour/test_engine_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/forecasting/test_engine_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/reconciliation/test_engine_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/unit/engines/account/test_account_engine.py`

**Risk:** HIGH

**Confidence:** LOW


### Changed: `backend/tests/unit/engines/behaviour/test_core.py`

**Risk:** CRITICAL

**Confidence:** LOW


### Changed: `backend/tests/unit/engines/behaviour/test_integration.py`

**Risk:** CRITICAL

**Confidence:** LOW


### Changed: `backend/tests/unit/engines/behaviour/test_metrics.py`

**Risk:** CRITICAL

**Confidence:** LOW


### Changed: `backend/tests/unit/engines/behaviour/test_patterns.py`

**Risk:** CRITICAL

**Confidence:** LOW


### Changed: `backend/tests/unit/engines/loan/test_amortization.py`

**Risk:** CRITICAL

**Confidence:** LOW


### Changed: `backend/tests/unit/engines/loan/test_loan_engine.py`

**Risk:** CRITICAL

**Confidence:** LOW


### Changed: `backend/tests/unit/engines/recommendation/test_recommendation_engine.py`

**Risk:** HIGH

**Confidence:** LOW


### Changed: `backend/tests/unit/engines/reconciliation/test_reconciliation.py`

**Risk:** HIGH

**Confidence:** LOW


### Changed: `backend/tests/unit/repositories/test_account_balance_repository.py`

**Risk:** HIGH

**Confidence:** LOW


### Changed: `backend/tests/unit/repositories/test_account_link_repository.py`

**Risk:** HIGH

**Confidence:** LOW


### Changed: `backend/tests/unit/repositories/test_pattern_repository.py`

**Risk:** HIGH

**Confidence:** LOW


### Changed: `backend/tools/check_coverage.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tools/generate_contract_tests.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tools/selective_verify.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `memory-bank/activeContext.md`

**Risk:** LOW

**Confidence:** LOW


### Changed: `servers`

**Risk:** LOW

**Confidence:** LOW


## Overall Assessment

**Risk Level:** CRITICAL

**Risk Score:** 222
