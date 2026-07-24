# Engine Contracts

> Extracted from production code. Each contract documents inputs, outputs, dependencies,
> business invariants, failure conditions, and known technical debt.

---

## 1. CashflowEngine

**Module:** `src/engines/cashflow_engine.py`
**Purity:** Pure (no DB access, no side effects)

### Purpose
Compute monthly cashflow analysis from income/expense summaries and financial event overlays. Determines whether a month is surplus, deficit-covered-by-credit, or deficit.

### Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| `cash_summary` | `dict[str, Any]` | `{income_paise: int, expense_paise: int}` |
| `financial_events` | `list[dict[str, Any]]` | Events with `event_type`, `amount_paise`, `asset_change_paise`, `liability_change_paise`, `expense_paise`, `income_paise` |
| `scope` | `str` | `"household"` or `"individual"` |
| `owner_id` | `str \| None` | Scope owner identifier |

### Outputs

| Key | Type | Description |
|-----|------|-------------|
| `cash_surplus` | `int` | income_paise - expense_paise (integer paise) |
| `true_savings` | `int` | cash_surplus adjusted for cash-related events |
| `liability_adjusted_savings` | `int` | true_savings minus liability increases |
| `net_worth_impact` | `int` | asset change minus liability change |
| `month_classification` | `str` | One of: "surplus", "deficit_covered_by_credit", "deficit" |
| `credit_dependency_ratio` | `float` | Ratio of credit-funded expenses (0-1) |

### Dependencies
- `decimal.Decimal` — safe division only

### Business Invariants
1. `income_paise >= 0` and `expense_paise >= 0`
2. `cash_surplus = income_paise - expense_paise` (mathematical identity)
3. `true_savings >= cash_surplus` when financial_events add cash
4. `credit_dependency_ratio` in [0, 1] range
5. Month classification is exactly one of three valid strings
6. All monetary outputs are integers (paise)
7. Monetary outputs are never None (default 0)

### Failure Conditions
- `cash_summary` missing `income_paise` or `expense_paise` → KeyError
- Non-integer paise values → downstream assertion failure

### Known Technical Debt
- Month classification logic does not handle multi-month rollover
- `credit_dependency_ratio` can exceed 1.0 in extreme deficit scenarios

---

## 2. BalanceEngine

**Module:** `src/engines/balance_engine.py`
**Purity:** Impure (opens sqlite3 connection directly)

### Purpose
Compute running balance for accounts by iterating transactions ordered by date. Provides deterministic balance reconstruction from transaction history.

### Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| `db_path` | `str` | Path to SQLite database file |
| `account_id` | `str \| None` | Filter to specific account |
| `starting_balance_paise` | `int` | Initial balance (default 0) |

### Outputs

| Key | Type | Description |
|-----|------|-------------|
| balance sequence | `list[dict]` | Each row: `{date_iso, amount_paise, running_balance_paise}` |

### Dependencies
- `sqlite3` — direct database connection
- `datetime` — date parsing

### Business Invariants
1. Running balance for row N = previous balance + transaction amount
2. Transactions sorted chronologically (date_iso ASC)
3. All amounts in integer paise
4. Starting balance can be negative (overdraft)

### Failure Conditions
- `db_path` not found → sqlite3.OperationalError
- Corrupt transactions table → sqlite3.DatabaseError
- No transactions → returns empty list

### Known Technical Debt
- **AR-1 violation**: Calls `sqlite3.connect()` directly instead of accepting data via parameters
- Should accept `list[dict]` of transactions and `int` starting balance
- Refactoring target: make pure, push SQL to repository layer

---

## 3. ReconciliationEngine

**Module:** `src/engines/reconciliation_engine.py`
**Purity:** Mostly pure (one legacy DB wrapper)

### Purpose
Bipartite matching of debit and credit transactions using Hungarian algorithm with date-weighted and amount-weighted scoring.

### Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| `debits` | `list[dict[str, Any]]` | Debit transactions to match |
| `credits` | `list[dict[str, Any]]` | Credit transactions to match |
| `household_account_map` | `dict[str, str] \| None` | Account ID → household ID mapping |
| `max_date_window_days` | `int` | Max days between matched txns (default 90) |
| `min_confidence_bps` | `int` | Minimum confidence threshold (default 1500) |

### Outputs

| Key | Type | Description |
|-----|------|-------------|
| matches | `list[dict]` | Matched pairs with confidence score |
| unmatched_debits | `list[dict]` | Debits without match |
| unmatched_credits | `list[dict]` | Credits without match |

### Dependencies
- `datetime` — date window calculations
- `pathlib.Path` — (only in legacy DB wrapper)

### Business Invariants
1. Each debit matched to at most one credit
2. Each credit matched to at most one debit
3. Match confidence in [0, 10000] bps
4. Date difference between matched pairs ≤ max_date_window_days
5. Amount difference penalized proportionally
6. Same-account matches preferred (household scope)
7. Matching is deterministic — same inputs → same outputs

### Failure Conditions
- Empty debits or credits → returns all unmatched
- Large datasets → O(n³) Hungarian algorithm performance

### Known Technical Debt
- `find_potential_matches_with_db()` is a legacy DB wrapper (sqlite3)
- Hungarian algorithm is O(n³) — potential perf issue at scale
- No tie-breaking for equal-confidence matches

---

## 4. AccountEngine

**Module:** `src/engines/account_engine/` (6 files)
**Purity:** Pure (all files, no DB access)

### Sub-modules

| File | Functions | Purpose |
|------|-----------|---------|
| `balance.py` | `compute_average_balance`, `compute_balance_change`, `compute_balance_growth_percentage` | Balance math |
| `cashflow.py` | `compute_net_cash_flow`, `compute_cash_flow_rate`, `compute_income_expense_ratio` | Cash flow ratios |
| `dormant.py` | `compute_days_since_activity`, `is_account_dormant` | Dormancy detection |
| `history.py` | `compute_balance_trend`, `compute_balance_velocity` | Balance trends |
| `lifecycle.py` | `compute_account_status`, `is_account_closed` | Account lifecycle |
| `metrics.py` | `compute_account_metrics` | Aggregate metrics |

### Business Invariants
1. Average balance = sum(balances) / len(balances) [integer paise]
2. Balance change = closing - opening
3. Net cash flow = credits - debits
4. Days since activity is non-negative
5. Account status is one of: active, dormant, closed, inactive
6. Income/expense ratio is finite for expense > 0
7. Balance growth percentage is integer (0 = no growth)

### Known Technical Debt
- `compute_income_expense_ratio` returns integer — loses precision
- `compute_average_balance` uses Decimal rounding — verify against financial requirements
- `compute_balance_growth_percentage` returns 0 for zero previous balance (division by zero guard)

---

## 5. BehaviourEngine

**Module:** `src/engines/behaviour_engine/` (12 files)
**Purity:** Pure (all files, no DB access)

### Sub-modules

| File | Functions | Purpose |
|------|-----------|---------|
| `account.py` | `compute_account_concentration`, `compute_idle_cash_amount`, `detect_balance_volatility`, `detect_low_balance_risk` | Account profile |
| `cashflow.py` | `compute_income_stability`, `compute_expense_stability`, `compute_cashflow_stability_index` | Cashflow stability |
| `credit_dependency.py` | `artificial_income_flag`, `credit_dependency_ratio`, `transactor_vs_revolver`, `revolver_ratio`, `debt_rolling_flag` | Credit behaviour |
| `debt.py` | `compute_credit_dependency_ratio`, `compute_debt_cycle_score` | Debt analysis |
| `income.py` | `classify_income_source`, `compute_salary_dependence_ratio`, `compute_income_diversification_score`, `filter_true_income` | Income analysis |
| `lifestyle.py` | `compute_lifestyle_inflation`, `compute_lifestyle_creep_index` | Lifestyle analysis |
| `patterns.py` | `detect_impulse_transactions`, `compute_weekend_spend_ratio` | Spending patterns |
| `profile.py` | `compute_behaviour_profile` | Aggregate profile |
| `resilience.py` | `compute_resilience_score` | Financial resilience |
| `savings.py` | `compute_savings_rate`, `compute_emergency_fund_coverage` | Savings metrics |
| `stress.py` | `compute_financial_stress_score` | Stress indicators |
| `temporal.py` | Time-based pattern detection | Temporal patterns |
| `utils.py` | Shared helpers | Utilities |
| `wellness.py` | `compute_wellness_score` | Overall wellness |

### Business Invariants
1. All scores normalized to [0, 1] range or integer 0-100
2. Income stability is monotonic — more stable → higher score
3. Credit dependency ratio in [0, 1]
4. Savings rate ≤ 1.0 (cannot save more than income)
5. Emergency fund coverage is months (integer)
6. Resilience score ∈ [0, 100]
7. Wellness score ∈ [0, 100]

### Known Technical Debt
- `behavior_engine.py` (top-level) is deprecated — delegates to BehaviourService
- Some score functions use hardcoded thresholds — configurable?
- `classify_income_source` returns tuple[str, float] — mixed types

---

## 6. CreditCardEngine

**Module:** `src/engines/credit_card_engine/` (7 files)
**Purity:** Pure (all files, no DB access)

### Sub-modules

| File | Functions | Purpose |
|------|-----------|---------|
| `billing.py` | Cycle calculation, due date computation | Billing cycle |
| `emi.py` | EMI conversion, schedule generation | EMI calculation |
| `foreclosure.py` | Foreclosure amount, savings | Early closure |
| `interest.py` | Interest calculation, daily compounding | Interest math |
| `metrics.py` | Utilization, payment ratios | Card metrics |
| `outstanding.py` | Outstanding tracking, payments | Balance tracking |
| `utilization.py` | Credit utilization ratio | Utilization |

### Business Invariants
1. Credit utilization = outstanding / limit (0-1)
2. Available credit = limit - outstanding
3. Interest is non-negative
4. EMI tenure > 0 months
5. Total repayment ≥ principal (total interest ≥ 0)
6. Minimum due > 0 when outstanding > 0
7. All monetary values in integer paise
8. Foreclosure amount ≤ remaining outstanding

### Known Technical Debt
- No consolidated entry point — callers must import from sub-modules

---

## 7. LoanEngine

**Module:** `src/engines/loan_engine/` (9 files)
**Purity:** Pure (all files, no DB access)

### Sub-modules

| File | Functions | Purpose |
|------|-----------|---------|
| `amortization.py` | `calculate_amortization_schedule` | EMI schedule generation |
| `emi.py` | `calculate_emi`, `calculate_total_interest` | EMI math |
| `floating_rate.py` | Rate adjustment logic | Floating rate handling |
| `foreclosure.py` | Foreclosure calculation | Early repayment |
| `metrics.py` | Loan health metrics | Performance |
| `models.py` | Data classes | Type definitions |
| `prepayment.py` | Prepayment simulation | Extra payment |
| `utils.py` | Helpers | Shared utilities |

### Business Invariants
1. Principal monotonically decreases during repayment
2. Final balance = 0 (fully amortized)
3. Interest per period ≥ 0
4. EMI amount is constant (fixed-rate schedule)
5. Outstanding ≤ principal (cannot owe more than borrowed)
6. Tenure > 0 for active loans
7. All monetary values in integer paise
8. Prepayment reduces total interest

### Known Technical Debt
- `models.py` contains both data classes AND computation — separation violation
- Floating rate logic not fully tested for rate-index tracking

---

## 8. FinancialEventsEngine

**Module:** `src/engines/financial_events/lineage_walker.py`
**Purity:** Pure (no DB access)

### Purpose
Track financial event lineage — walk chains of linked events to detect rollover scenarios and settlement chains.

### Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| `events` | `list[dict[str, Any]]` | Financial events with lifecycle_state, event_type, account_id |
| `event_id` | `str` | Starting event ID |
| `direction` | `Literal["forward", "backward"]` | Traversal direction |

### Outputs

| Key | Type | Description |
|-----|------|-------------|
| lineage chain | `list[dict]` | Ordered list of linked events |

### Business Invariants
1. Event chain is acyclic (no circular references)
2. Linked events share the same account_id
3. Event dates are chronological along the chain
4. Forward traversal from open → closed → archived
5. Backward traversal finds funding sources

---

## 9. FinancialIntelligenceEngine

**Module:** `src/engines/financial_intelligence/` (8 files)
**Purity:** Mostly pure

### Sub-modules

| File | Purpose |
|------|---------|
| `forecasting.py` | Cashflow/liquidity forecasting |
| `goal_planner.py` | Financial goal planning |
| `intelligence.py` | Risk/opportunity detection |
| `models.py` | Data structures |
| `optimization.py` | Optimization suggestions |
| `scenario.py` | What-if scenarios |
| `utils.py` | Shared utilities |

### Business Invariants
1. Forecast confidence in [0, 10000] bps
2. Goal timelines are positive integers (months)
3. Optimization suggestions are non-negative (no cost if already optimal)

---

## 10. TransactionIntelligenceEngine

**Module:** `src/engines/transaction_intelligence/` (4 files)
**Purity:** Pure (no DB access)

### Sub-modules

| File | Functions | Purpose |
|------|-----------|---------|
| `cash_conversion_detector.py` | `detect_cash_conversion_cycles` | CC cash advance detection |
| `cc_payment_detector.py` | `detect_cc_payments` | Credit card payment detection |
| `detector_result.py` | `DetectorResult` dataclass | Result type |
| `loan_emi_detector.py` | `detect_loan_emi` | EMI payment detection |

### Business Invariants
1. Detected amounts ≤ transaction amounts
2. Detection confidence in [0, 10000] bps
3. CC payment detection requires matching creditor description
4. EMI detection requires consistent monthly amounts (± tolerance)

---

## 11. NudgeEngine

**Module:** `src/engines/nudge_engine.py`
**Purity:** Pure

### Purpose
Generate behavioral nudges based on financial patterns and thresholds.

### Business Invariants
1. Nudge count is non-negative
2. Each nudge has a unique type identifier
3. Nudge priority is one of: low, medium, high

---

## 12. InsightGenerator

**Module:** `src/engines/insight_generator.py`
**Purity:** Pure

### Purpose
Extract financial insights from transaction/account data.

### Known Technical Debt
- Minimal documentation — contract inferred from signature analysis
- Likely under-tested

---

## 13. LedgerAuditEngine

**Module:** `src/engines/ledger_audit_engine.py`
**Purity:** Impure (sqlite3)

### Purpose
Audit the ledger for consistency violations (balance mismatches, missing transactions, orphaned records).

### Known Technical Debt
- **AR-1 violation**: Direct sqlite3 access
- Read-only queries — acceptable impurity for audit tool

---

## 14. RecommendationEngine

**Module:** `src/engines/recommendation_engine/recommendations.py`
**Purity:** Pure

### Purpose
Generate financial recommendations based on account state and behaviour scores.

### Known Technical Debt
- Minimal test coverage
- Recommendation logic is rule-based with hardcoded thresholds

---

## 15. BehaviorEngine (Deprecated)

**Module:** `src/engines/behavior_engine.py`
**Purity:** Delegates to BehaviourService

### Purpose
Legacy shim — delegates all computation to `BehaviourService`. Do not use for new code.

### Status
- **DEPRECATED** — canonical implementation is `behaviour_engine/` package
- Remove once no callers remain