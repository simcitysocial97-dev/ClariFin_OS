# Change Impact Report

Generated: 2026-07-29T17:42:18.301648+00:00

## Summary

| File | Risk | Capabilities | Confidence |
|------|------|--------------|------------|
| `.github/workflows/backend.yml` | LOW | UNKNOWN | LOW |
| `.vscode/settings.json` | LOW | UNKNOWN | LOW |
| `backend/diagnose_db.py` | LOW | UNKNOWN | LOW |
| `backend/src/engines/credit_card_engine/billing.py` | CRITICAL | credit_cards | HIGH |
| `backend/src/engines/credit_card_engine/emi.py` | CRITICAL | credit_cards | HIGH |
| `backend/src/engines/financial_events/lineage_walker.py` | HIGH | financial_events | MEDIUM |
| `backend/src/engines/loan_engine/amortization.py` | CRITICAL | debt_management | HIGH |
| `backend/src/engines/loan_engine/emi.py` | CRITICAL | debt_management | HIGH |
| `backend/src/engines/loan_engine/floating_rate.py` | CRITICAL | debt_management | HIGH |
| `backend/src/engines/loan_engine/models.py` | CRITICAL | debt_management | HIGH |
| `backend/src/engines/loan_engine/prepayment.py` | CRITICAL | debt_management | HIGH |
| `backend/src/repositories/pattern_repository.py` | HIGH | pattern_analysis, transaction_intelligence | HIGH |
| `backend/src/verification/intelligence/coverage_engine.py` | LOW | UNKNOWN | LOW |
| `backend/src/verification/intelligence/dependency_engine.py` | LOW | UNKNOWN | LOW |
| `backend/src/verification/intelligence/evidence_engine.py` | LOW | UNKNOWN | LOW |
| `backend/src/verification/intelligence/impact_engine.py` | LOW | UNKNOWN | LOW |
| `backend/src/verification/intelligence/report_engine.py` | LOW | UNKNOWN | LOW |
| `backend/src/verification/intelligence/risk_engine.py` | LOW | UNKNOWN | LOW |
| `backend/src/verification/intelligence/selective_engine.py` | LOW | UNKNOWN | LOW |
| `backend/src/verification/intelligence/self_validation.py` | LOW | UNKNOWN | LOW |
| `backend/src/verification/runtime/registries.py` | LOW | UNKNOWN | LOW |
| `backend/tests/audits/test_audit_minimal.py` | LOW | UNKNOWN | LOW |
| `backend/tests/capability/financial_events/test_capability.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_accounts.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_analytics.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_audit.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_banks.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_behaviour.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_cards.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_cashflow.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_categories.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_credit_cards.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_dashboard.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_export.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_financial_events.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_forecast.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_import.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_institutions.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_investments.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_loans.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_members.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_net_worth.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_networth.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_overview.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_reconciliation.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_reconciliations.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_statements.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_transactions.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_upload.py` | LOW | UNKNOWN | LOW |
| `backend/tests/contract/generated/test_v1.py` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/api-map.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/capability-registry.yaml` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/change-report.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/change-report.md` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/contract-coverage.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/contract-registry.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/mutation-gaps.md` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/mutation-map.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/mutation-readiness.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/mutation-readiness.md` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/mutation-registry.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/selective-plan.md` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/test-plan.md` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/test-strength.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/test-strength.md` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/validation-manifest.json` | LOW | UNKNOWN | LOW |
| `backend/tests/generated/verification-matrix.md` | LOW | UNKNOWN | LOW |
| `backend/tests/golden/datasets/cc_statement_scenario.json` | LOW | UNKNOWN | LOW |
| `backend/tests/golden/datasets/credit_card_revolver.json` | LOW | UNKNOWN | LOW |
| `backend/tests/golden/datasets/high_debt_household.json` | LOW | UNKNOWN | LOW |
| `backend/tests/golden/datasets/irregular_income.json` | LOW | UNKNOWN | LOW |
| `backend/tests/golden/datasets/multiple_loans.json` | LOW | UNKNOWN | LOW |
| `backend/tests/golden/datasets/normal_household.json` | LOW | UNKNOWN | LOW |
| `backend/tests/golden/test_regression.py` | LOW | UNKNOWN | LOW |
| `backend/tests/invariants/test_determinism.py` | LOW | UNKNOWN | LOW |
| `backend/tests/invariants/test_reconciliation_determinism.py` | LOW | UNKNOWN | LOW |
| `backend/tests/meta/test_capability_audit.py` | LOW | UNKNOWN | LOW |
| `backend/tests/meta/test_capability_coverage.py` | LOW | UNKNOWN | LOW |
| `backend/tests/meta/test_capability_isolation.py` | LOW | UNKNOWN | LOW |
| `backend/tests/meta/test_capability_regression.py` | LOW | UNKNOWN | LOW |
| `backend/tests/meta/test_false_negative_measurement.py` | LOW | UNKNOWN | LOW |
| `backend/tests/meta/test_false_positive_measurement.py` | LOW | UNKNOWN | LOW |
| `backend/tests/meta/test_github_actions_validation.py` | LOW | UNKNOWN | LOW |
| `backend/tests/meta/test_graph_integrity.py` | LOW | UNKNOWN | LOW |
| `backend/tests/meta/test_longitudinal_determinism.py` | LOW | UNKNOWN | LOW |
| `backend/tests/meta/test_mutation_verification.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/credit_card_engine/test_billing_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/credit_card_engine/test_emi_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/credit_card_engine/test_interest_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/credit_cards/test_engine_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/forecasting/test_engine_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/lending/test_engine_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/loan_engine/test_amortization_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/loan_engine/test_emi_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/loan_engine/test_floating_rate_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/loan_engine/test_foreclosure_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/loan_engine/test_metrics_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/loan_engine/test_prepayment_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/properties/reconciliation/test_engine_properties.py` | LOW | UNKNOWN | LOW |
| `backend/tests/unit/engines/behavior/test_behavior_engine.py` | CRITICAL | UNKNOWN | LOW |
| `backend/tests/unit/engines/behaviour/test_core.py` | CRITICAL | UNKNOWN | LOW |
| `backend/tests/unit/engines/reconciliation/test_reconciliation.py` | HIGH | UNKNOWN | LOW |
| `backend/tools/verification_intelligence.py` | LOW | UNKNOWN | LOW |
| `servers` | LOW | UNKNOWN | LOW |

## Detailed Analysis

### Changed: `.github/workflows/backend.yml`

**Risk:** LOW

**Confidence:** LOW


### Changed: `.vscode/settings.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/diagnose_db.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/engines/credit_card_engine/billing.py`

**Risk:** CRITICAL

**Confidence:** HIGH

**Affected Capabilities:**

- `credit_cards`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capability/credit_cards`
  - Property Tests:
    - `tests/properties/credit_card_engine`
    - `tests/properties/credit_cards`
  - Golden Datasets:
    - `cash_advance`
    - `cc_statement_scenario`
    - `credit_card_revolver`
  - Invariants:
    - `tests/invariants/test_credit.py`

**Recommended Verification:**
```bash
pytest tests/capability/credit_cards -q
pytest tests/properties/credit_card_engine -q
pytest tests/properties/credit_cards -q
pytest tests/golden -k 'cash_advance,cc_statement_scenario,credit_card_revolver' -q
```

### Changed: `backend/src/engines/credit_card_engine/emi.py`

**Risk:** CRITICAL

**Confidence:** HIGH

**Affected Capabilities:**

- `credit_cards`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capability/credit_cards`
  - Property Tests:
    - `tests/properties/credit_card_engine`
    - `tests/properties/credit_cards`
  - Golden Datasets:
    - `cash_advance`
    - `cc_statement_scenario`
    - `credit_card_revolver`
  - Invariants:
    - `tests/invariants/test_credit.py`

**Recommended Verification:**
```bash
pytest tests/capability/credit_cards -q
pytest tests/properties/credit_card_engine -q
pytest tests/properties/credit_cards -q
pytest tests/golden -k 'cash_advance,cc_statement_scenario,credit_card_revolver' -q
```

### Changed: `backend/src/engines/financial_events/lineage_walker.py`

**Risk:** HIGH

**Confidence:** MEDIUM

**Affected Capabilities:**

- `financial_events`

**Affected Tests:**

  - Capability Smoke Tests:
    - `tests/capability/financial_events`
  - Golden Datasets:
    - `cc_statement_scenario`
    - `salary_plus_loan`
  - Invariants:
    - `tests/invariants/test_transaction.py`

**Recommended Verification:**
```bash
pytest tests/capability/financial_events -q
pytest tests/golden -k 'cc_statement_scenario,salary_plus_loan' -q
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

### Changed: `backend/src/engines/loan_engine/floating_rate.py`

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

### Changed: `backend/src/engines/loan_engine/models.py`

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

### Changed: `backend/src/engines/loan_engine/prepayment.py`

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

### Changed: `backend/src/verification/intelligence/coverage_engine.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/verification/intelligence/dependency_engine.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/verification/intelligence/evidence_engine.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/verification/intelligence/impact_engine.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/verification/intelligence/report_engine.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/verification/intelligence/risk_engine.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/verification/intelligence/selective_engine.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/verification/intelligence/self_validation.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/src/verification/runtime/registries.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/audits/test_audit_minimal.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/capability/financial_events/test_capability.py`

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


### Changed: `backend/tests/contract/generated/test_behaviour.py`

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


### Changed: `backend/tests/contract/generated/test_credit_cards.py`

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


### Changed: `backend/tests/contract/generated/test_forecast.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_import.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_institutions.py`

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


### Changed: `backend/tests/contract/generated/test_net_worth.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_networth.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_overview.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/contract/generated/test_reconciliation.py`

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


### Changed: `backend/tests/generated/api-map.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/capability-registry.yaml`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/change-report.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/change-report.md`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/contract-coverage.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/contract-registry.json`

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


### Changed: `backend/tests/generated/selective-plan.md`

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


### Changed: `backend/tests/generated/validation-manifest.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/generated/verification-matrix.md`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/golden/datasets/cc_statement_scenario.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/golden/datasets/credit_card_revolver.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/golden/datasets/high_debt_household.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/golden/datasets/irregular_income.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/golden/datasets/multiple_loans.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/golden/datasets/normal_household.json`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/golden/test_regression.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/invariants/test_determinism.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/invariants/test_reconciliation_determinism.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/meta/test_capability_audit.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/meta/test_capability_coverage.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/meta/test_capability_isolation.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/meta/test_capability_regression.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/meta/test_false_negative_measurement.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/meta/test_false_positive_measurement.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/meta/test_github_actions_validation.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/meta/test_graph_integrity.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/meta/test_longitudinal_determinism.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/meta/test_mutation_verification.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/credit_card_engine/test_billing_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/credit_card_engine/test_emi_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/credit_card_engine/test_interest_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/credit_cards/test_engine_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/forecasting/test_engine_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/lending/test_engine_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/loan_engine/test_amortization_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/loan_engine/test_emi_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/loan_engine/test_floating_rate_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/loan_engine/test_foreclosure_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/loan_engine/test_metrics_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/loan_engine/test_prepayment_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/properties/reconciliation/test_engine_properties.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `backend/tests/unit/engines/behavior/test_behavior_engine.py`

**Risk:** CRITICAL

**Confidence:** LOW


### Changed: `backend/tests/unit/engines/behaviour/test_core.py`

**Risk:** CRITICAL

**Confidence:** LOW


### Changed: `backend/tests/unit/engines/reconciliation/test_reconciliation.py`

**Risk:** HIGH

**Confidence:** LOW


### Changed: `backend/tools/verification_intelligence.py`

**Risk:** LOW

**Confidence:** LOW


### Changed: `servers`

**Risk:** LOW

**Confidence:** LOW


## Overall Assessment

**Risk Level:** CRITICAL

**Risk Score:** 176
