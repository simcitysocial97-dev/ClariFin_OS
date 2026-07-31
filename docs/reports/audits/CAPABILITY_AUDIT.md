# Capability Truth Audit

Part A of Phase 3.2 — Capability Validation & Real-World Verification

Audits every capability in the registry to verify all declared components exist
on disk and no stale mappings exist.

## Summary

- Total capabilities: 11
- Capabilities with missing components: 0
- Capabilities with stale mappings: 1

## Capability Details

### Account Management (`account_management`)

**Routers**:

- ✓ `src/routers/accounts.py`
- ✓ `src/routers/managed_accounts.py`

**Services**:

- ✓ `src/services/account_service.py`

**Engines**:

- ✓ `src/engines/account_engine/balance.py`
- ✓ `src/engines/account_engine/cashflow.py`
- ✓ `src/engines/account_engine/dormant.py`
- ✓ `src/engines/account_engine/history.py`
- ✓ `src/engines/account_engine/lifecycle.py`
- ✓ `src/engines/account_engine/metrics.py`
- ✓ `src/engines/balance_engine.py`

**Repositories**:

- ✓ `src/repositories/account_repository.py`
- ✓ `src/repositories/account_balance_repository.py`
- ✓ `src/repositories/account_link_repository.py`

**Tables**:

- ✓ `accounts`
- ✓ `account_balances`
- ✓ `account_links`

**Golden Datasets**:

- ✓ `tests/golden/datasets/normal_household.json`
- ✓ `tests/golden/datasets/salary_only.json`
- ✓ `tests/golden/datasets/family_household.json`

**Property Tests**:

- ✓ `tests/unit/engines/account/test_account_engine.py`
- ✓ `tests/properties/behaviour/test_engine_properties.py`

**Invariants**:

- ✓ `tests/invariants/test_account.py`

**Architecture Tests**:

- ✓ `tests/architecture`

**Contracts**:

- ✓ `POST /api/accounts`
- ✓ `GET /api/accounts/{account_id}`
- ✓ `GET /api/accounts/{account_id}/metrics`
- ✓ `POST /api/accounts/link`

**Status**: ✓ All components verified, no stale mappings

### Credit Cards (`credit_cards`)

**Routers**:

- ✓ `src/routers/credit_cards.py`
- ✓ `src/routers/cards_statements.py`

**Services**:

- ✓ `src/services/credit_card_service.py`

**Engines**:

- ✓ `src/engines/credit_card_engine/billing.py`
- ✓ `src/engines/credit_card_engine/emi.py`
- ✓ `src/engines/credit_card_engine/foreclosure.py`
- ✓ `src/engines/credit_card_engine/interest.py`
- ✓ `src/engines/credit_card_engine/metrics.py`
- ✓ `src/engines/credit_card_engine/outstanding.py`
- ✓ `src/engines/credit_card_engine/utilization.py`

**Repositories**:

- ✓ `src/repositories/credit_card_repository.py`
- ✓ `src/repositories/credit_card_statement_repository.py`

**Tables**:

- ✓ `credit_cards`
- ✓ `credit_card_statements`
- ✓ `credit_card_emi`
- ✓ `credit_card_foreclosure`

**Golden Datasets**:

- ✓ `tests/golden/datasets/credit_card_revolver.json`
- ✓ `tests/golden/datasets/cash_advance.json`
- ✓ `tests/golden/datasets/cc_statement_scenario.json`

**Property Tests**:

- ✓ `tests/properties/credit_cards/test_engine_properties.py`
- ✓ `tests/properties/credit_card_engine/test_billing_properties.py`
- ✓ `tests/properties/credit_card_engine/test_emi_properties.py`
- ✓ `tests/properties/credit_card_engine/test_interest_properties.py`

**Invariants**:

- ✓ `tests/invariants/test_credit.py`

**Architecture Tests**:

- ✓ `tests/architecture`

**Contracts**:

- ✓ `POST /api/credit-cards`
- ✓ `GET /api/credit-cards/{card_id}/statement`
- ✓ `POST /api/credit-cards/{card_id}/emi-convert`
- ✓ `POST /api/credit-cards/foreclosure-calculate`

**Status**: ✓ All components verified, no stale mappings

### Debt Management (`debt_management`)

**Routers**:

- ✓ `src/routers/loans.py`

**Services**:

- ✓ `src/services/loan_service.py`
- ✓ `src/services/loan_analysis_service.py`
- ✓ `src/services/loan_simulation_service.py`

**Engines**:

- ✓ `src/engines/loan_engine/amortization.py`
- ✓ `src/engines/loan_engine/emi.py`
- ✓ `src/engines/loan_engine/floating_rate.py`
- ✓ `src/engines/loan_engine/foreclosure.py`
- ✓ `src/engines/loan_engine/metrics.py`
- ✓ `src/engines/loan_engine/models.py`
- ✓ `src/engines/loan_engine/prepayment.py`
- ✓ `src/engines/loan_engine/utils.py`

**Repositories**:

- ✓ `src/repositories/loan_repository.py`
- ✓ `src/repositories/loan_payment_repository.py`

**Tables**:

- ✓ `loans`
- ✓ `loan_payments`
- ✓ `credit_card_emi`

**Golden Datasets**:

- ✓ `tests/golden/datasets/salary_plus_loan.json`
- ✓ `tests/golden/datasets/multiple_loans.json`
- ✓ `tests/golden/datasets/high_debt_household.json`

**Property Tests**:

- ✓ `tests/properties/lending/test_engine_properties.py`

**Invariants**:

- ✓ `tests/invariants/test_loan.py`

**Architecture Tests**:

- ✓ `tests/architecture`

**Contracts**:

- ✓ `POST /api/loans`
- ✓ `GET /api/loans/{loan_id}/schedule`
- ✓ `POST /api/loans/foreclosure-calculate`
- ✓ `POST /api/loans/prepayment-simulate`

**Status**: ✓ All components verified, no stale mappings

### Financial Events (`financial_events`)

**Routers**:

- ✓ `src/routers/financial_intelligence.py`

**Services**:

- ✓ `src/services/financial_events_service.py`

**Engines**:

- ✓ `src/engines/financial_events/lineage_walker.py`

**Repositories**:

- ✓ `src/repositories/financial_event_repository.py`

**Tables**:

- ✓ `financial_events`
- ✓ `financial_event_lifecycle_log`

**Golden Datasets**:

- ✓ `tests/golden/datasets/cc_statement_scenario.json`
- ✓ `tests/golden/datasets/salary_plus_loan.json`

**Property Tests**: None declared

**Invariants**:

- ✓ `tests/invariants/test_transaction.py`

**Architecture Tests**:

- ✓ `tests/architecture`

**Contracts**:

- ✓ `POST /api/financial-events`
- ✓ `GET /api/financial-events/{event_id}/lineage`
- ✓ `POST /api/financial-events/{event_id}/transition`

**Status**: ✓ All components verified, no stale mappings

### Financial Health (`financial_health`)

**Routers**:

- ✓ `src/routers/behaviour.py`
- ✓ `src/routers/behaviour_workspace.py`

**Services**:

- ✓ `src/services/behaviour_service.py`

**Engines**:

- ✓ `src/engines/behavior_engine.py`
- ✓ `src/engines/behaviour_engine/account.py`
- ✓ `src/engines/behaviour_engine/cashflow.py`
- ✓ `src/engines/behaviour_engine/credit_dependency.py`
- ✓ `src/engines/behaviour_engine/debt.py`
- ✓ `src/engines/behaviour_engine/income.py`
- ✓ `src/engines/behaviour_engine/lifestyle.py`
- ✓ `src/engines/behaviour_engine/patterns.py`
- ✓ `src/engines/behaviour_engine/profile.py`
- ✓ `src/engines/behaviour_engine/resilience.py`
- ✓ `src/engines/behaviour_engine/savings.py`
- ✓ `src/engines/behaviour_engine/stress.py`
- ✓ `src/engines/behaviour_engine/wellness.py`
- ✓ `src/engines/behaviour_engine/core.py`
- ✓ `src/engines/behaviour_engine/temporal.py`
- ✓ `src/engines/behaviour_engine/utils.py`

**Repositories**:

- ✓ `src/repositories/behaviour_repository.py`

**Tables**:

- ✓ `behaviour_profiles`
- ✓ `behaviour_scores`
- ✓ `financial_events`

**Golden Datasets**:

- ✓ `tests/golden/datasets/normal_household.json`
- ✓ `tests/golden/datasets/high_debt_household.json`
- ✓ `tests/golden/datasets/irregular_income.json`

**Property Tests**:

- ✓ `tests/properties/behaviour/test_engine_properties.py`
- ✓ `tests/unit/engines/behaviour/test_core.py`

**Invariants**:

- ✓ `tests/invariants/behaviour.py`

**Architecture Tests**:

- ✓ `tests/architecture`

**Contracts**:

- ✓ `GET /api/behavior/profile`
- ✓ `GET /api/behavior/wellness`
- ✓ `GET /api/behavior/resilience`
- ✓ `GET /api/behavior/stress`

**Status**: ✓ All components verified, no stale mappings

### Forecasting (`forecasting`)

**Routers**:

- ✓ `src/routers/financial_intelligence.py`

**Services**:

- ✓ `src/services/financial_intelligence_service.py`

**Engines**:

- ✓ `src/engines/financial_intelligence/forecasting.py`
- ✓ `src/engines/financial_intelligence/goal_planner.py`
- ✓ `src/engines/financial_intelligence/intelligence.py`
- ✓ `src/engines/financial_intelligence/optimization.py`
- ✓ `src/engines/financial_intelligence/scenario.py`
- ✓ `src/engines/financial_intelligence/models.py`
- ✓ `src/engines/financial_intelligence/utils.py`

**Repositories**:

- ✓ `src/repositories/financial_goal_repository.py`

**Tables**:

- ✓ `financial_goals`
- ✓ `forecasts`
- ✓ `scenarios`
- ✓ `financial_events`

**Golden Datasets**:

- ✓ `tests/golden/datasets/salary_only.json`
- ✓ `tests/golden/datasets/salary_plus_loan.json`
- ✓ `tests/golden/datasets/irregular_income.json`

**Property Tests**:

- ✓ `tests/properties/forecasting/test_engine_properties.py`

**Invariants**:

- ✓ `tests/invariants/forecast.py`

**Architecture Tests**:

- ✓ `tests/architecture`

**Contracts**:

- ✓ `GET /api/financial-intelligence/forecast`
- ✓ `POST /api/financial-intelligence/scenario`
- ✓ `GET /api/goals`
- ✓ `POST /api/goals`

**Status**: ✓ All components verified, no stale mappings

### Household Cashflow (`household_cashflow`)

**Routers**:

- ✓ `src/routers/cashflow.py`

**Services**:

- ✓ `src/services/cashflow_service.py`

**Engines**:

- ✓ `src/engines/cashflow_engine.py`

**Repositories**:

- ✓ `src/repositories/cashflow_repository.py`

**Tables**:

- ✓ `transactions`
- ✓ `accounts`
- ✓ `financial_events`
- ✓ `cashflow_summaries`

**Golden Datasets**:

- ✓ `tests/golden/datasets/normal_household.json`
- ✓ `tests/golden/datasets/salary_only.json`
- ✓ `tests/golden/datasets/salary_plus_loan.json`
- ✓ `tests/golden/datasets/family_household.json`

**Property Tests**:

- ✓ `tests/properties/cashflow/test_engine_properties.py`

**Invariants**:

- ✓ `tests/invariants/test_cashflow_invariants.py`

**Architecture Tests**:

- ✓ `tests/architecture`

**Contracts**:

- ✓ `POST /api/cashflow/monthly`
- ✓ `GET /api/cashflow/trends`

**Status**: ✓ All components verified, no stale mappings

### Pattern Analysis (`pattern_analysis`)

**Routers**:

- ✓ `src/routers/transactions.py`

**Services**: None declared

**Engines**:

- ✓ `src/engines/insight_generator.py`

**Repositories**:

- ✓ `src/repositories/pattern_repository.py`
- ✓ `src/repositories/liquidity_pattern_repository.py`

**Tables**:

- ✓ `patterns`
- ✓ `liquidity_patterns`
- ✓ `transactions`

**Golden Datasets**:

- ✓ `tests/golden/datasets/irregular_income.json`
- ✓ `tests/golden/datasets/normal_household.json`

**Property Tests**:

- ✓ `tests/unit/repositories/test_pattern_repository.py`

**Invariants**:

- ✓ `tests/invariants/test_transaction.py`

**Architecture Tests**:

- ✓ `tests/architecture`

**Contracts**:

- ✓ `GET /api/patterns`
- ✓ `GET /api/patterns/liquidity`
- ✓ `POST /api/patterns/detect`

**Status**: ✓ All components verified, no stale mappings

### Recommendations (`recommendations`)

**Routers**:

- ✓ `src/routers/financial_intelligence.py`

**Services**:

- ✓ `src/services/financial_intelligence_service.py`

**Engines**:

- ✓ `src/engines/recommendation_engine/recommendations.py`
- ✓ `src/engines/financial_intelligence/optimization.py`
- ✓ `src/engines/nudge_engine.py`

**Repositories**:

- ✓ `src/repositories/financial_goal_repository.py`

**Tables**:

- ✓ `recommendations`
- ✓ `financial_goals`
- ✓ `behaviour_scores`

**Golden Datasets**:

- ✓ `tests/golden/datasets/normal_household.json`
- ✓ `tests/golden/datasets/high_debt_household.json`
- ✓ `tests/golden/datasets/credit_card_revolver.json`

**Property Tests**:

- ✓ `tests/unit/engines/recommendation/test_recommendation_engine.py`

**Invariants**:

- ✓ `tests/invariants/behaviour.py`

**Architecture Tests**:

- ✓ `tests/architecture`

**Contracts**:

- ✓ `GET /api/optimization/recommendations`
- ✓ `GET /api/optimization/nudges`

**Status**: ✓ All components verified, no stale mappings

### Reconciliation (`reconciliation`)

**Routers**:

- ✓ `src/routers/reconciliation.py`

**Services**:

- ✓ `src/services/reconciliation_service.py`

**Engines**:

- ✓ `src/engines/reconciliation_engine.py`
- ✓ `src/engines/ledger_audit_engine.py`

**Repositories**:

- ✓ `src/repositories/reconciliation_repository.py`
- ✓ `src/repositories/reconciliation_audit_repository.py`

**Tables**:

- ✓ `transactions`
- ✓ `reconciliation_matches`
- ✓ `reconciliation_audit_log`

**Golden Datasets**:

- ✓ `tests/golden/datasets/normal_household.json`
- ✓ `tests/golden/datasets/salary_plus_loan.json`

**Property Tests**:

- ✓ `tests/unit/engines/reconciliation/test_reconciliation.py`
- ✓ `tests/invariants/test_reconciliation_determinism.py`

**Invariants**:

- ✓ `tests/invariants/test_transaction.py`

**Architecture Tests**:

- ✓ `tests/architecture`

**Contracts**:

- ✓ `POST /api/reconciliation/run`
- ✓ `GET /api/reconciliation/{session_id}/matches`
- ✓ `GET /api/reconciliation/unmatched`

**Stale Mappings**:

- ⚠ routers: src/routers/reconciliation_workspace.py (discovered but not registered)
- ⚠ services: src/services/reconciliation_workspace_service.py (discovered but not registered)

### Transaction Intelligence (`transaction_intelligence`)

**Routers**:

- ✓ `src/routers/transactions.py`

**Services**:

- ✓ `src/services/transaction_intelligence_service.py`

**Engines**:

- ✓ `src/engines/transaction_intelligence/cash_conversion_detector.py`
- ✓ `src/engines/transaction_intelligence/cc_payment_detector.py`
- ✓ `src/engines/transaction_intelligence/detector_result.py`
- ✓ `src/engines/transaction_intelligence/loan_emi_detector.py`

**Repositories**:

- ✓ `src/repositories/transaction_repository.py`
- ✓ `src/repositories/pattern_repository.py`

**Tables**:

- ✓ `transactions`
- ✓ `patterns`
- ✓ `liquidity_patterns`

**Golden Datasets**:

- ✓ `tests/golden/datasets/cc_statement_scenario.json`
- ✓ `tests/golden/datasets/cash_advance.json`
- ✓ `tests/golden/datasets/normal_household.json`

**Property Tests**:

- ✓ `tests/properties/credit_cards/test_engine_properties.py`

**Invariants**:

- ✓ `tests/invariants/test_statement.py`
- ✓ `tests/invariants/test_transaction.py`

**Architecture Tests**:

- ✓ `tests/architecture`

**Contracts**:

- ✓ `POST /api/transactions/detect-patterns`
- ✓ `GET /api/patterns/credit-card-payments`
- ✓ `GET /api/patterns/loan-emis`

**Status**: ✓ All components verified, no stale mappings
