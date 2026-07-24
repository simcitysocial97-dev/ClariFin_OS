# Change Impact Analysis

Generated automatically. Shows what capabilities/tests would be affected by modifying a file.

## `src/engines/account_engine/balance.py`

**Capabilities:**
  - Account Management (`account_management`)

**Golden Tests:**
  - `family_household`
  - `normal_household`
  - `salary_only`

## `src/engines/account_engine/cashflow.py`

**Capabilities:**
  - Account Management (`account_management`)

**Golden Tests:**
  - `family_household`
  - `normal_household`
  - `salary_only`

## `src/engines/account_engine/dormant.py`

**Capabilities:**
  - Account Management (`account_management`)

**Golden Tests:**
  - `family_household`
  - `normal_household`
  - `salary_only`

## `src/engines/account_engine/history.py`

**Capabilities:**
  - Account Management (`account_management`)

**Golden Tests:**
  - `family_household`
  - `normal_household`
  - `salary_only`

## `src/engines/account_engine/lifecycle.py`

**Capabilities:**
  - Account Management (`account_management`)

**Golden Tests:**
  - `family_household`
  - `normal_household`
  - `salary_only`

## `src/engines/account_engine/metrics.py`

**Capabilities:**
  - Account Management (`account_management`)

**Golden Tests:**
  - `family_household`
  - `normal_household`
  - `salary_only`

## `src/engines/behaviour_engine/account.py`

**Capabilities:**
  - Financial Health (`financial_health`)

**Golden Tests:**
  - `high_debt_household`
  - `irregular_income`
  - `normal_household`

## `src/engines/behaviour_engine/cashflow.py`

**Capabilities:**
  - Financial Health (`financial_health`)

**Golden Tests:**
  - `high_debt_household`
  - `irregular_income`
  - `normal_household`

## `src/engines/behaviour_engine/credit_dependency.py`

**Capabilities:**
  - Financial Health (`financial_health`)

**Golden Tests:**
  - `high_debt_household`
  - `irregular_income`
  - `normal_household`

## `src/engines/behaviour_engine/debt.py`

**Capabilities:**
  - Financial Health (`financial_health`)

**Golden Tests:**
  - `high_debt_household`
  - `irregular_income`
  - `normal_household`

## `src/engines/behaviour_engine/income.py`

**Capabilities:**
  - Financial Health (`financial_health`)

**Golden Tests:**
  - `high_debt_household`
  - `irregular_income`
  - `normal_household`

## `src/engines/behaviour_engine/lifestyle.py`

**Capabilities:**
  - Financial Health (`financial_health`)

**Golden Tests:**
  - `high_debt_household`
  - `irregular_income`
  - `normal_household`

## `src/engines/behaviour_engine/patterns.py`

**Capabilities:**
  - Financial Health (`financial_health`)

**Golden Tests:**
  - `high_debt_household`
  - `irregular_income`
  - `normal_household`

## `src/engines/behaviour_engine/profile.py`

**Capabilities:**
  - Financial Health (`financial_health`)

**Golden Tests:**
  - `high_debt_household`
  - `irregular_income`
  - `normal_household`

## `src/engines/behaviour_engine/resilience.py`

**Capabilities:**
  - Financial Health (`financial_health`)

**Golden Tests:**
  - `high_debt_household`
  - `irregular_income`
  - `normal_household`

## `src/engines/behaviour_engine/savings.py`

**Capabilities:**
  - Financial Health (`financial_health`)

**Golden Tests:**
  - `high_debt_household`
  - `irregular_income`
  - `normal_household`

## `src/engines/behaviour_engine/stress.py`

**Capabilities:**
  - Financial Health (`financial_health`)

**Golden Tests:**
  - `high_debt_household`
  - `irregular_income`
  - `normal_household`

## `src/engines/behaviour_engine/wellness.py`

**Capabilities:**
  - Financial Health (`financial_health`)

**Golden Tests:**
  - `high_debt_household`
  - `irregular_income`
  - `normal_household`

## `src/engines/cashflow_engine.py`

**Capabilities:**
  - Household Cashflow (`household_cashflow`)

**Golden Tests:**
  - `family_household`
  - `normal_household`
  - `salary_only`
  - `salary_plus_loan`

## `src/engines/credit_card_engine/billing.py`

**Capabilities:**
  - Credit Cards (`credit_cards`)

**Golden Tests:**
  - `cash_advance`
  - `cc_statement_scenario`
  - `credit_card_revolver`

## `src/engines/credit_card_engine/emi.py`

**Capabilities:**
  - Credit Cards (`credit_cards`)

**Golden Tests:**
  - `cash_advance`
  - `cc_statement_scenario`
  - `credit_card_revolver`

## `src/engines/credit_card_engine/foreclosure.py`

**Capabilities:**
  - Credit Cards (`credit_cards`)

**Golden Tests:**
  - `cash_advance`
  - `cc_statement_scenario`
  - `credit_card_revolver`

## `src/engines/credit_card_engine/interest.py`

**Capabilities:**
  - Credit Cards (`credit_cards`)

**Golden Tests:**
  - `cash_advance`
  - `cc_statement_scenario`
  - `credit_card_revolver`

## `src/engines/credit_card_engine/metrics.py`

**Capabilities:**
  - Credit Cards (`credit_cards`)

**Golden Tests:**
  - `cash_advance`
  - `cc_statement_scenario`
  - `credit_card_revolver`

## `src/engines/credit_card_engine/outstanding.py`

**Capabilities:**
  - Credit Cards (`credit_cards`)

**Golden Tests:**
  - `cash_advance`
  - `cc_statement_scenario`
  - `credit_card_revolver`

## `src/engines/credit_card_engine/utilization.py`

**Capabilities:**
  - Credit Cards (`credit_cards`)

**Golden Tests:**
  - `cash_advance`
  - `cc_statement_scenario`
  - `credit_card_revolver`

## `src/engines/financial_events/lineage_walker.py`

**Capabilities:**
  - Financial Events (`financial_events`)

**Golden Tests:**
  - `cc_statement_scenario`
  - `salary_plus_loan`

## `src/engines/financial_intelligence/forecasting.py`

**Capabilities:**
  - Forecasting (`forecasting`)

**Golden Tests:**
  - `irregular_income`
  - `salary_only`
  - `salary_plus_loan`

## `src/engines/financial_intelligence/goal_planner.py`

**Capabilities:**
  - Forecasting (`forecasting`)

**Golden Tests:**
  - `irregular_income`
  - `salary_only`
  - `salary_plus_loan`

## `src/engines/financial_intelligence/intelligence.py`

**Capabilities:**
  - Forecasting (`forecasting`)

**Golden Tests:**
  - `irregular_income`
  - `salary_only`
  - `salary_plus_loan`

## `src/engines/financial_intelligence/optimization.py`

**Capabilities:**
  - Forecasting (`forecasting`)
  - Recommendations (`recommendations`)

**Golden Tests:**
  - `credit_card_revolver`
  - `high_debt_household`
  - `irregular_income`
  - `normal_household`
  - `salary_only`
  - `salary_plus_loan`

## `src/engines/financial_intelligence/scenario.py`

**Capabilities:**
  - Forecasting (`forecasting`)

**Golden Tests:**
  - `irregular_income`
  - `salary_only`
  - `salary_plus_loan`

## `src/engines/insight_generator.py`

**Capabilities:**
  - Pattern Analysis (`pattern_analysis`)

**Golden Tests:**
  - `irregular_income`
  - `normal_household`

## `src/engines/loan_engine/amortization.py`

**Capabilities:**
  - Debt Management (`debt_management`)

**Golden Tests:**
  - `high_debt_household`
  - `multiple_loans`
  - `salary_plus_loan`

## `src/engines/loan_engine/emi.py`

**Capabilities:**
  - Debt Management (`debt_management`)

**Golden Tests:**
  - `high_debt_household`
  - `multiple_loans`
  - `salary_plus_loan`

## `src/engines/loan_engine/floating_rate.py`

**Capabilities:**
  - Debt Management (`debt_management`)

**Golden Tests:**
  - `high_debt_household`
  - `multiple_loans`
  - `salary_plus_loan`

## `src/engines/loan_engine/foreclosure.py`

**Capabilities:**
  - Debt Management (`debt_management`)

**Golden Tests:**
  - `high_debt_household`
  - `multiple_loans`
  - `salary_plus_loan`

## `src/engines/loan_engine/metrics.py`

**Capabilities:**
  - Debt Management (`debt_management`)

**Golden Tests:**
  - `high_debt_household`
  - `multiple_loans`
  - `salary_plus_loan`

## `src/engines/loan_engine/models.py`

**Capabilities:**
  - Debt Management (`debt_management`)

**Golden Tests:**
  - `high_debt_household`
  - `multiple_loans`
  - `salary_plus_loan`

## `src/engines/loan_engine/prepayment.py`

**Capabilities:**
  - Debt Management (`debt_management`)

**Golden Tests:**
  - `high_debt_household`
  - `multiple_loans`
  - `salary_plus_loan`

## `src/engines/loan_engine/utils.py`

**Capabilities:**
  - Debt Management (`debt_management`)

**Golden Tests:**
  - `high_debt_household`
  - `multiple_loans`
  - `salary_plus_loan`

## `src/engines/nudge_engine.py`

**Capabilities:**
  - Recommendations (`recommendations`)

**Golden Tests:**
  - `credit_card_revolver`
  - `high_debt_household`
  - `normal_household`

## `src/engines/recommendation_engine/recommendations.py`

**Capabilities:**
  - Recommendations (`recommendations`)

**Golden Tests:**
  - `credit_card_revolver`
  - `high_debt_household`
  - `normal_household`

## `src/engines/reconciliation_engine.py`

**Capabilities:**
  - Reconciliation (`reconciliation`)

**Golden Tests:**
  - `normal_household`
  - `salary_plus_loan`

## `src/engines/transaction_intelligence/cash_conversion_detector.py`

**Capabilities:**
  - Transaction Intelligence (`transaction_intelligence`)

**Golden Tests:**
  - `cash_advance`
  - `cc_statement_scenario`
  - `normal_household`

## `src/engines/transaction_intelligence/cc_payment_detector.py`

**Capabilities:**
  - Transaction Intelligence (`transaction_intelligence`)

**Golden Tests:**
  - `cash_advance`
  - `cc_statement_scenario`
  - `normal_household`

## `src/engines/transaction_intelligence/detector_result.py`

**Capabilities:**
  - Transaction Intelligence (`transaction_intelligence`)

**Golden Tests:**
  - `cash_advance`
  - `cc_statement_scenario`
  - `normal_household`

## `src/engines/transaction_intelligence/loan_emi_detector.py`

**Capabilities:**
  - Transaction Intelligence (`transaction_intelligence`)

**Golden Tests:**
  - `cash_advance`
  - `cc_statement_scenario`
  - `normal_household`

## `src/repositories/account_balance_repository.py`

**Capabilities:**
  - Account Management (`account_management`)

## `src/repositories/account_link_repository.py`

**Capabilities:**
  - Account Management (`account_management`)

## `src/repositories/account_repository.py`

**Capabilities:**
  - Account Management (`account_management`)

## `src/repositories/behaviour_repository.py`

**Capabilities:**
  - Financial Health (`financial_health`)

## `src/repositories/cashflow_repository.py`

**Capabilities:**
  - Household Cashflow (`household_cashflow`)

## `src/repositories/credit_card_repository.py`

**Capabilities:**
  - Credit Cards (`credit_cards`)

## `src/repositories/credit_card_statement_repository.py`

**Capabilities:**
  - Credit Cards (`credit_cards`)

## `src/repositories/financial_event_repository.py`

**Capabilities:**
  - Financial Events (`financial_events`)

## `src/repositories/financial_goal_repository.py`

**Capabilities:**
  - Forecasting (`forecasting`)
  - Recommendations (`recommendations`)

## `src/repositories/liquidity_pattern_repository.py`

**Capabilities:**
  - Pattern Analysis (`pattern_analysis`)

## `src/repositories/loan_payment_repository.py`

**Capabilities:**
  - Debt Management (`debt_management`)

## `src/repositories/loan_repository.py`

**Capabilities:**
  - Debt Management (`debt_management`)

## `src/repositories/pattern_repository.py`

**Capabilities:**
  - Pattern Analysis (`pattern_analysis`)
  - Transaction Intelligence (`transaction_intelligence`)

## `src/repositories/reconciliation_audit_repository.py`

**Capabilities:**
  - Reconciliation (`reconciliation`)

## `src/repositories/reconciliation_repository.py`

**Capabilities:**
  - Reconciliation (`reconciliation`)

## `src/repositories/transaction_repository.py`

**Capabilities:**
  - Transaction Intelligence (`transaction_intelligence`)

## `src/routers/accounts.py`

**Capabilities:**
  - Account Management (`account_management`)

**Property Tests:**
  - `tests/properties/accountmanagement`

## `src/routers/behaviour.py`

**Capabilities:**
  - Financial Health (`financial_health`)

**Property Tests:**
  - `tests/properties/financialhealth`

## `src/routers/behaviour_workspace.py`

**Capabilities:**
  - Financial Health (`financial_health`)

**Property Tests:**
  - `tests/properties/financialhealth`

## `src/routers/cards_statements.py`

**Capabilities:**
  - Credit Cards (`credit_cards`)

**Property Tests:**
  - `tests/properties/creditcards`

## `src/routers/cashflow.py`

**Capabilities:**
  - Household Cashflow (`household_cashflow`)

**Property Tests:**
  - `tests/properties/householdcashflow`

## `src/routers/credit_cards.py`

**Capabilities:**
  - Credit Cards (`credit_cards`)

**Property Tests:**
  - `tests/properties/creditcards`

## `src/routers/financial_intelligence.py`

**Capabilities:**
  - Financial Events (`financial_events`)
  - Forecasting (`forecasting`)
  - Recommendations (`recommendations`)

**Property Tests:**
  - `tests/properties/financialevents`
  - `tests/properties/forecasting`
  - `tests/properties/recommendations`

## `src/routers/loans.py`

**Capabilities:**
  - Debt Management (`debt_management`)

**Property Tests:**
  - `tests/properties/debtmanagement`

## `src/routers/managed_accounts.py`

**Capabilities:**
  - Account Management (`account_management`)

**Property Tests:**
  - `tests/properties/accountmanagement`

## `src/routers/reconciliation.py`

**Capabilities:**
  - Reconciliation (`reconciliation`)

**Property Tests:**
  - `tests/properties/reconciliation`

## `src/routers/transactions.py`

**Capabilities:**
  - Pattern Analysis (`pattern_analysis`)
  - Transaction Intelligence (`transaction_intelligence`)

**Property Tests:**
  - `tests/properties/patternanalysis`
  - `tests/properties/transactionintelligence`

## `src/services/account_service.py`

**Capabilities:**
  - Account Management (`account_management`)

## `src/services/behaviour_service.py`

**Capabilities:**
  - Financial Health (`financial_health`)

## `src/services/cashflow_service.py`

**Capabilities:**
  - Household Cashflow (`household_cashflow`)

## `src/services/credit_card_service.py`

**Capabilities:**
  - Credit Cards (`credit_cards`)

## `src/services/financial_events_service.py`

**Capabilities:**
  - Financial Events (`financial_events`)

## `src/services/financial_intelligence_service.py`

**Capabilities:**
  - Forecasting (`forecasting`)
  - Recommendations (`recommendations`)

## `src/services/loan_analysis_service.py`

**Capabilities:**
  - Debt Management (`debt_management`)

## `src/services/loan_service.py`

**Capabilities:**
  - Debt Management (`debt_management`)

## `src/services/loan_simulation_service.py`

**Capabilities:**
  - Debt Management (`debt_management`)

## `src/services/reconciliation_service.py`

**Capabilities:**
  - Reconciliation (`reconciliation`)

## `src/services/transaction_intelligence_service.py`

**Capabilities:**
  - Transaction Intelligence (`transaction_intelligence`)
