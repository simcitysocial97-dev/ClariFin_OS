# Traceability Matrix

Generated automatically. Shows the complete dependency chain for each capability.

## Account Management

**Capability ID:** `account_management`

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
| Router | `src/routers/accounts.py` | ✓ |
| Router | `src/routers/managed_accounts.py` | ✓ |
| Service | `src/services/account_service.py` | ✓ |
| Engine | `src/engines/account_engine/balance.py` | ✓ |
| Engine | `src/engines/account_engine/cashflow.py` | ✓ |
| Engine | `src/engines/account_engine/dormant.py` | ✓ |
| Engine | `src/engines/account_engine/history.py` | ✓ |
| Engine | `src/engines/account_engine/lifecycle.py` | ✓ |
| Engine | `src/engines/account_engine/metrics.py` | ✓ |
| Repository | `src/repositories/account_repository.py` | ✓ |
| Repository | `src/repositories/account_balance_repository.py` | ✓ |
| Repository | `src/repositories/account_link_repository.py` | ✓ |
| Table | `accounts` | ✓ |
| Table | `account_balances` | ✓ |
| Table | `account_links` | ✓ |
| Golden Dataset | `tests/golden/datasets/normal_household.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/salary_only.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/family_household.json` | ✓ |
| Property Test | `tests/unit/engines/account/test_account_engine.py` | ✓ |
| Property Test | `tests/properties/behaviour/test_engine_properties.py` | ✓ |
| Invariant | `tests/invariants/test_account.py` | ✓ |

## Credit Cards

**Capability ID:** `credit_cards`

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
| Router | `src/routers/credit_cards.py` | ✓ |
| Router | `src/routers/cards_statements.py` | ✓ |
| Service | `src/services/credit_card_service.py` | ✓ |
| Engine | `src/engines/credit_card_engine/billing.py` | ✓ |
| Engine | `src/engines/credit_card_engine/emi.py` | ✓ |
| Engine | `src/engines/credit_card_engine/foreclosure.py` | ✓ |
| Engine | `src/engines/credit_card_engine/interest.py` | ✓ |
| Engine | `src/engines/credit_card_engine/metrics.py` | ✓ |
| Engine | `src/engines/credit_card_engine/outstanding.py` | ✓ |
| Engine | `src/engines/credit_card_engine/utilization.py` | ✓ |
| Repository | `src/repositories/credit_card_repository.py` | ✓ |
| Repository | `src/repositories/credit_card_statement_repository.py` | ✓ |
| Table | `credit_cards` | ✓ |
| Table | `credit_card_statements` | ✓ |
| Table | `credit_card_emi` | ✓ |
| Table | `credit_card_foreclosure` | ✓ |
| Golden Dataset | `tests/golden/datasets/credit_card_revolver.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/cash_advance.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/cc_statement_scenario.json` | ✓ |
| Property Test | `tests/properties/credit_cards/test_engine_properties.py` | ✓ |
| Invariant | `tests/invariants/test_credit.py` | ✓ |

## Debt Management

**Capability ID:** `debt_management`

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
| Router | `src/routers/loans.py` | ✓ |
| Service | `src/services/loan_service.py` | ✓ |
| Service | `src/services/loan_analysis_service.py` | ✓ |
| Service | `src/services/loan_simulation_service.py` | ✓ |
| Engine | `src/engines/loan_engine/amortization.py` | ✓ |
| Engine | `src/engines/loan_engine/emi.py` | ✓ |
| Engine | `src/engines/loan_engine/floating_rate.py` | ✓ |
| Engine | `src/engines/loan_engine/foreclosure.py` | ✓ |
| Engine | `src/engines/loan_engine/metrics.py` | ✓ |
| Engine | `src/engines/loan_engine/models.py` | ✓ |
| Engine | `src/engines/loan_engine/prepayment.py` | ✓ |
| Engine | `src/engines/loan_engine/utils.py` | ✓ |
| Repository | `src/repositories/loan_repository.py` | ✓ |
| Repository | `src/repositories/loan_payment_repository.py` | ✓ |
| Table | `loans` | ✓ |
| Table | `loan_payments` | ✓ |
| Table | `credit_card_emi` | ✓ |
| Golden Dataset | `tests/golden/datasets/salary_plus_loan.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/multiple_loans.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/high_debt_household.json` | ✓ |
| Property Test | `tests/properties/lending/test_engine_properties.py` | ✓ |
| Invariant | `tests/invariants/test_loan.py` | ✓ |

## Financial Events

**Capability ID:** `financial_events`

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
| Router | `src/routers/financial_intelligence.py` | ✓ |
| Service | `src/services/financial_events_service.py` | ✓ |
| Engine | `src/engines/financial_events/lineage_walker.py` | ✓ |
| Repository | `src/repositories/financial_event_repository.py` | ✓ |
| Table | `financial_events` | ✓ |
| Table | `financial_event_lifecycle_log` | ✓ |
| Golden Dataset | `tests/golden/datasets/cc_statement_scenario.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/salary_plus_loan.json` | ✓ |
| Invariant | `tests/invariants/test_transaction.py` | ✓ |

## Financial Health

**Capability ID:** `financial_health`

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
| Router | `src/routers/behaviour.py` | ✓ |
| Router | `src/routers/behaviour_workspace.py` | ✓ |
| Service | `src/services/behaviour_service.py` | ✓ |
| Engine | `src/engines/behaviour_engine/account.py` | ✓ |
| Engine | `src/engines/behaviour_engine/cashflow.py` | ✓ |
| Engine | `src/engines/behaviour_engine/credit_dependency.py` | ✓ |
| Engine | `src/engines/behaviour_engine/debt.py` | ✓ |
| Engine | `src/engines/behaviour_engine/income.py` | ✓ |
| Engine | `src/engines/behaviour_engine/lifestyle.py` | ✓ |
| Engine | `src/engines/behaviour_engine/patterns.py` | ✓ |
| Engine | `src/engines/behaviour_engine/profile.py` | ✓ |
| Engine | `src/engines/behaviour_engine/resilience.py` | ✓ |
| Engine | `src/engines/behaviour_engine/savings.py` | ✓ |
| Engine | `src/engines/behaviour_engine/stress.py` | ✓ |
| Engine | `src/engines/behaviour_engine/wellness.py` | ✓ |
| Repository | `src/repositories/behaviour_repository.py` | ✓ |
| Table | `behaviour_profiles` | ✓ |
| Table | `behaviour_scores` | ✓ |
| Table | `financial_events` | ✓ |
| Golden Dataset | `tests/golden/datasets/normal_household.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/high_debt_household.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/irregular_income.json` | ✓ |
| Property Test | `tests/properties/behaviour/test_engine_properties.py` | ✓ |
| Invariant | `tests/invariants/behaviour.py` | ✓ |

## Forecasting

**Capability ID:** `forecasting`

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
| Router | `src/routers/financial_intelligence.py` | ✓ |
| Service | `src/services/financial_intelligence_service.py` | ✓ |
| Engine | `src/engines/financial_intelligence/forecasting.py` | ✓ |
| Engine | `src/engines/financial_intelligence/goal_planner.py` | ✓ |
| Engine | `src/engines/financial_intelligence/intelligence.py` | ✓ |
| Engine | `src/engines/financial_intelligence/optimization.py` | ✓ |
| Engine | `src/engines/financial_intelligence/scenario.py` | ✓ |
| Repository | `src/repositories/financial_goal_repository.py` | ✓ |
| Table | `financial_goals` | ✓ |
| Table | `forecasts` | ✓ |
| Table | `scenarios` | ✓ |
| Table | `financial_events` | ✓ |
| Golden Dataset | `tests/golden/datasets/salary_only.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/salary_plus_loan.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/irregular_income.json` | ✓ |
| Property Test | `tests/properties/forecasting/test_engine_properties.py` | ✓ |
| Invariant | `tests/invariants/forecast.py` | ✓ |

## Household Cashflow

**Capability ID:** `household_cashflow`

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
| Router | `src/routers/cashflow.py` | ✓ |
| Service | `src/services/cashflow_service.py` | ✓ |
| Engine | `src/engines/cashflow_engine.py` | ✓ |
| Repository | `src/repositories/cashflow_repository.py` | ✓ |
| Table | `transactions` | ✓ |
| Table | `accounts` | ✓ |
| Table | `financial_events` | ✓ |
| Table | `cashflow_summaries` | ✓ |
| Golden Dataset | `tests/golden/datasets/normal_household.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/salary_only.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/salary_plus_loan.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/family_household.json` | ✓ |
| Property Test | `tests/properties/cashflow/test_engine_properties.py` | ✓ |
| Invariant | `tests/invariants/test_cashflow_invariants.py` | ✓ |

## Pattern Analysis

**Capability ID:** `pattern_analysis`

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
| Router | `src/routers/transactions.py` | ✓ |
| Engine | `src/engines/insight_generator.py` | ✓ |
| Repository | `src/repositories/pattern_repository.py` | ✓ |
| Repository | `src/repositories/liquidity_pattern_repository.py` | ✓ |
| Table | `patterns` | ✓ |
| Table | `liquidity_patterns` | ✓ |
| Table | `transactions` | ✓ |
| Golden Dataset | `tests/golden/datasets/irregular_income.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/normal_household.json` | ✓ |
| Property Test | `tests/unit/repositories/test_pattern_repository.py` | ✓ |
| Invariant | `tests/invariants/test_transaction.py` | ✓ |

## Recommendations

**Capability ID:** `recommendations`

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
| Router | `src/routers/financial_intelligence.py` | ✓ |
| Service | `src/services/financial_intelligence_service.py` | ✓ |
| Engine | `src/engines/recommendation_engine/recommendations.py` | ✓ |
| Engine | `src/engines/financial_intelligence/optimization.py` | ✓ |
| Engine | `src/engines/nudge_engine.py` | ✓ |
| Repository | `src/repositories/financial_goal_repository.py` | ✓ |
| Table | `recommendations` | ✓ |
| Table | `financial_goals` | ✓ |
| Table | `behaviour_scores` | ✓ |
| Golden Dataset | `tests/golden/datasets/normal_household.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/high_debt_household.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/credit_card_revolver.json` | ✓ |
| Property Test | `tests/unit/engines/recommendation/test_recommendation_engine.py` | ✓ |
| Invariant | `tests/invariants/behaviour.py` | ✓ |

## Reconciliation

**Capability ID:** `reconciliation`

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
| Router | `src/routers/reconciliation.py` | ✓ |
| Service | `src/services/reconciliation_service.py` | ✓ |
| Engine | `src/engines/reconciliation_engine.py` | ✓ |
| Repository | `src/repositories/reconciliation_repository.py` | ✓ |
| Repository | `src/repositories/reconciliation_audit_repository.py` | ✓ |
| Table | `transactions` | ✓ |
| Table | `reconciliation_matches` | ✓ |
| Table | `reconciliation_audit_log` | ✓ |
| Golden Dataset | `tests/golden/datasets/normal_household.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/salary_plus_loan.json` | ✓ |
| Property Test | `tests/unit/engines/reconciliation/test_reconciliation.py` | ✓ |
| Property Test | `tests/invariants/test_reconciliation_determinism.py` | ✓ |
| Invariant | `tests/invariants/test_transaction.py` | ✓ |

## Transaction Intelligence

**Capability ID:** `transaction_intelligence`

### Dependency Chain

| Layer | Artifact | Status |
|-------|----------|--------|
| Router | `src/routers/transactions.py` | ✓ |
| Service | `src/services/transaction_intelligence_service.py` | ✓ |
| Engine | `src/engines/transaction_intelligence/cash_conversion_detector.py` | ✓ |
| Engine | `src/engines/transaction_intelligence/cc_payment_detector.py` | ✓ |
| Engine | `src/engines/transaction_intelligence/detector_result.py` | ✓ |
| Engine | `src/engines/transaction_intelligence/loan_emi_detector.py` | ✓ |
| Repository | `src/repositories/transaction_repository.py` | ✓ |
| Repository | `src/repositories/pattern_repository.py` | ✓ |
| Table | `transactions` | ✓ |
| Table | `patterns` | ✓ |
| Table | `liquidity_patterns` | ✓ |
| Golden Dataset | `tests/golden/datasets/cc_statement_scenario.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/cash_advance.json` | ✓ |
| Golden Dataset | `tests/golden/datasets/normal_household.json` | ✓ |
| Property Test | `tests/properties/credit_cards/test_engine_properties.py` | ✓ |
| Invariant | `tests/invariants/test_statement.py` | ✓ |
| Invariant | `tests/invariants/test_transaction.py` | ✓ |
