# Mutation Validation Gaps Report

Generated: 2026-07-31T18:21:58.498985+00:00

## Summary

### `src/engines/account_engine/balance.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 1
  - `compute_balance_change`: blocked by ['open']

### `src/engines/account_engine/cashflow.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/account_engine/dormant.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/account_engine/history.py`

✗ No pure functions - blocked for mutation testing
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 2
  - `compute_balance_trend`: blocked by ['open']
  - `compute_balance_velocity`: blocked by ['open']

### `src/engines/account_engine/lifecycle.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/account_engine/metrics.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/balance_engine.py`

✗ No pure functions - blocked for mutation testing
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 4
  - `compute_running_balance`: blocked by ['sqlite3', 'import:sqlite3']
  - `compute_account_balance`: blocked by ['sqlite3', 'import:sqlite3']
  - `validate_statement_balance`: blocked by ['sqlite3', 'import:sqlite3']
  - `get_accounts_list`: blocked by ['sqlite3', 'import:sqlite3']

### `src/engines/behavior_engine.py`

✗ No pure functions - blocked for mutation testing
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 5
  - `invalidate_behavior_cache`: blocked by ['import:sqlite3']
  - `get_cached_behavior_profile`: blocked by ['import:sqlite3']
  - `set_cached_behavior_profile`: blocked by ['import:sqlite3']
  - `detect_india_risk_patterns`: blocked by ['os.', 'import:sqlite3']
  - `compute_behavior_profile`: blocked by ['import:sqlite3']

### `src/engines/behaviour_engine/account.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/behaviour_engine/cashflow.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/behaviour_engine/credit_dependency.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 2
  - `transactor_vs_revolver`: blocked by ['open']
  - `revolver_ratio`: blocked by ['open']

### `src/engines/behaviour_engine/debt.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/behaviour_engine/income.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/behaviour_engine/lifestyle.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/behaviour_engine/patterns.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/behaviour_engine/profile.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/behaviour_engine/resilience.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/behaviour_engine/savings.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/behaviour_engine/stress.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 1
  - `detect_risk_patterns`: blocked by ['os.']

### `src/engines/behaviour_engine/temporal.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/behaviour_engine/utils.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/behaviour_engine/wellness.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/cashflow_engine.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/credit_card_engine/billing.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/credit_card_engine/emi.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/credit_card_engine/foreclosure.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/credit_card_engine/interest.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/credit_card_engine/metrics.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/credit_card_engine/outstanding.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/credit_card_engine/utilization.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/financial_events/lineage_walker.py`

✗ No pure functions - blocked for mutation testing
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 3
  - `walk_lineage`: blocked by ['open']
  - `detect_revocations`: blocked by ['open']
  - `detect_rollover_scenarios`: blocked by ['open']

### `src/engines/financial_intelligence/forecasting.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 1
  - `forecast_credit_utilization`: blocked by ['open']

### `src/engines/financial_intelligence/goal_planner.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/financial_intelligence/intelligence.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/financial_intelligence/optimization.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/financial_intelligence/scenario.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/financial_intelligence/utils.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 1
  - `compute_trend_direction`: blocked by ['os.']

### `src/engines/insight_generator.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/ledger_audit_engine.py`

✗ No pure functions - blocked for mutation testing
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 3
  - `validate_ledger_integrity`: blocked by ['sqlite3', 'import:sqlite3']
  - `verify_hash_signatures`: blocked by ['sqlite3', 'import:sqlite3']
  - `run_full_audit`: blocked by ['import:sqlite3']

### `src/engines/loan_engine/amortization.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 1
  - `generate_schedule`: blocked by ['open']

### `src/engines/loan_engine/emi.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/loan_engine/floating_rate.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 1
  - `apply_floating_rate_change`: blocked by ['open']

### `src/engines/loan_engine/foreclosure.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/loan_engine/metrics.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 1
  - `compute_loan_metrics`: blocked by ['open']

### `src/engines/loan_engine/prepayment.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 1
  - `apply_prepayment_at_month`: blocked by ['open']

### `src/engines/loan_engine/utils.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/nudge_engine.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/recommendation_engine/recommendations.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/reconciliation_engine.py`

✗ No pure functions - blocked for mutation testing
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
✗ Impure functions (blockers): 2
  - `find_potential_matches`: blocked by ['sqlite3', 'import:sqlite3']
  - `find_matches_for_transaction`: blocked by ['sqlite3', 'import:sqlite3']

### `src/engines/transaction_intelligence/cash_conversion_detector.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/transaction_intelligence/cc_payment_detector.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available

### `src/engines/transaction_intelligence/loan_emi_detector.py`

✓ Pure functions detected
✓ Property tests available
✓ Golden datasets available
✓ Invariant tests available
✓ Contract tests available
