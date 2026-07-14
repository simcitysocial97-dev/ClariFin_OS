# ClariFin_OS Backend Architecture Audit Report

## PHASE 1: Executive Summary & System Topology

- **Architectural Pattern:** Layered Architecture with Domain-Oriented Services and Functional Computation Engines.

- **Layer-by-Layer Responsibilities:**
  - **Routers** (`src/routers/`, ~25 files): HTTP request handling, parameter validation, delegation to services
  - **Services** (`src/services/`, ~17 files): Business orchestration, coordinates repositories and engines
  - **Engines** (`src/engines/`, ~12+ packages): Pure computational logic, deterministic functions
  - **Repositories** (`src/repositories/`, ~26 files): Data access and persistence, SQLite abstraction
  - **Models** (`src/models/`, ~19 files): Pydantic domain entities
  - **Database** (`src/db.py`, `data/finance.db`): SQLite with paise-based monetary storage

- **Architectural Invariants (Established Rules):**
  - Monetary values stored as integer paise (₹1 = 100 paise)
  - Interest rates use basis points internally (integer representation)
  - Engines are deterministic and side-effect free
  - Services orchestrate but delegate algorithms to engines
  - Repositories are the only layer responsible for persistence
  - Routers do not contain business logic
  - Financial calculations use `Decimal` for intermediate precision where needed
  - Ledger transactions are immutable after confirmation

---

## PHASE 2: End-to-End Execution Flow

### Execution Path A: Loan Schedule Generation
```
Router (loans.py → get_loan_schedule)
  → Service (loan_service.py → get_schedule)
    → Engine (loan_engine/amortization.py → generate_schedule)
      → Repository (loan_repository.py → get_loan)
```

### Execution Path B: Transaction Reconciliation
```
Router (reconciliation.py → scan_matches)
  → Service (reconciliation_service.py → scan_potential_matches)
    → Engine (reconciliation_engine.py → find_potential_matches)
      → Repository (reconciliation_repository.py)
```

### Execution Path C: EMI Payment Detection
```
Service (transaction_intelligence_service.py → classify_emi_payments)
  → Engine (transaction_intelligence/loan_emi_detector.py → detect_emi_payment)
    → Repository (transaction_classification_repository.py)
```

---

## PHASE 3: Mathematical & Financial Formula Validation

### Core Formulas Analyzed (Observed & Verified)

| Formula | Location | Mathematical Notation | Determinism | Complexity |
|---------|----------|----------------------|-------------|------------|
| EMI | `loan_engine/emi.py` | $P \times r(1+r)^n / ((1+r)^n - 1)$ | ✅ Deterministic | O(1) |
| Monthly Rate | `loan_engine/utils.py` | $r_{monthly} = rate_{bps} / 120000$ | ✅ Deterministic | O(1) |
| Daily Interest | `credit_card_engine/interest.py` | $Interest = Outstanding \times rate_{bps} / 3650000$ | ✅ Deterministic | O(1) |
| Reducing Balance | `loan_engine/amortization.py` | $Balance_{new} = Balance - (EMI - Interest)$ | ✅ Deterministic | O(n) months |
| Weighted Moving Average | `financial_intelligence/forecasting.py` | $\sum_{i=1}^{n} w_i \times x_i$ (linear weights, recent highest) | ✅ Deterministic | O(n) |
| Hungarian Matching | `reconciliation_engine.py` | `scipy.optimize.linear_sum_assignment` with inline fallback | ✅ Deterministic | O(n³) worst case |
| Confidence Scoring | `reconciliation_engine.py` | Weighted combination of amount/date/description | ✅ Deterministic | O(1) per match |

### Numerical Stability (Verified)
- Integer paise prevents floating-point drift in financial calculations
- Weighted moving average uses integer arithmetic throughout
- Loan amortization uses Decimal with ROUND_HALF_EVEN (banker's rounding)

---

## PHASE 4: Financial Intelligence Engine Deep Dive

### Forecast Engine
| Aspect | Details |
|--------|---------|
| **Inputs** | `cashflow_history: list[dict]` with month, income_paise, expense_paise, surplus_paise |
| **Outputs** | `forecast: list[dict]`, `confidence: Decimal`, `model_version: str` |
| **Assumptions** | Stationarity (recent months predict future), linear weights |
| **Edge Cases** | Empty history → zeros with 0.5 confidence; clamps forecast_months to 1-12 |
| **Failure Modes** | None detected; graceful degradation |

### Optimization Engine
| Aspect | Details |
|--------|---------|
| **Inputs** | monthly_surplus_paise, debts[], goals[], emergency_fund_status |
| **Outputs** | allocation[], expected_impact |
| **Priority Logic** | Emergency fund → High-interest debt (≥18% bps) → Medium-interest debt (8-18%) → Long-term goals → Investment |
| **Decision Rule** | If debt APR > investment return + emergency buffer exists, debt wins |
| **Edge Cases** | Zero/negative surplus → empty allocation |

### Scenario Engine
| Aspect | Details |
|--------|---------|
| **Inputs** | Current state, change parameters |
| **Outputs** | ScenarioResult with projected months, balance impact |
| **Capabilities** | simulate_income_change, simulate_expense_reduction, simulate_debt_prepayment, simulate_new_loan |
| **Constraints** | Negative surplus allowed; no validation for impossible balances |

---

## PHASE 5: Engine Dependency Matrix

| Engine | Inputs | Outputs | Depends On | Pure |
|--------|--------|---------|------------|------|
| forecast_cashflow | cashflow_history (dict) | forecast (dict) | utils (generate_month_sequence, compute_variance) | ✅ |
| forecast_liquidity | current_liquidity, cashflow_forecast | stress_month, risk_level | utils (project_running_balance, find_stress_month) | ✅ |
| detect_future_cash_shortfall | forecasts | flag, severity, reason | None (reads previous outputs) | ✅ |
| optimize_surplus_allocation | surplus, debts, goals, emergency_status | allocation, impact | utils (thresholds, ratios) | ✅ |
| rank_debt_payoff_strategy | debts[] | priority_order | None | ✅ |
| generate_optimization_plan | financial_state | actions, warnings, confidence | optimize_surplus_allocation, rank_debt_payoff, calculate_action_score | ✅ |
| simulate_expense_reduction | expenses, accounts | ScenarioResult | models | ✅ |
| compare_scenario | baseline, scenario | comparison | models | ✅ |
| build_financial_snapshot | all financial data | snapshot | aggregate functions | ✅ |
| generate_financial_priorities | snapshot | priority_actions | scoring functions | ✅ |
| find_potential_matches | debits, credits | matches | `_hungarian_solve` (scipy/inline) | ✅ |

---

## PHASE 6: Repository Ownership Matrix

| Repository | Tables Owned | Cohesion | N+1 Risks | Status |
|------------|--------------|----------|-----------|--------|
| TransactionRepository | transactions | High | Potential in reconciliation loops | Stable |
| LoanRepository | loans, loan_payments, loan_amortization_schedule | High | None | Stable |
| ReconciliationRepository | reconciliations, reconciliation_audit_log | High | None | Stable |
| CashflowRepository | monthly_aggregates (derived) | Medium | Derived from transactions | Stable |
| FinancialGoalRepository | financial_goals | High | None | Stable |
| AccountRepository | accounts, account_balances | High | None | Stable |
| BehaviourRepository | behaviour_snapshots | Medium | None | Stable |

---

## PHASE 7: Database Table → Repository → Service → Engine Pipeline

```
transactions
    ↓
TransactionRepository
    ↓
CashflowService → cashflow_engine
    ↓
forecast_cashflow() → forecast_liquidity() → detect_future_cash_shortfall()

loans
    ↓
LoanRepository
    ↓
LoanService → loan_engine
    ↓
generate_schedule() → compute_loan_metrics() → apply_prepayment()

financial_goals
    ↓
FinancialGoalRepository
    ↓
FinancialIntelligenceService → goal_planner
    ↓
calculate_goal_projection() → calculate_goal_health()
```

---

## PHASE 8: Technical Debt Register

| Debt | Severity | Owner | Target Phase | Status | Evidence |
|------|----------|-------|--------------|--------|----------|
| balance_engine DB access | High | Backend Team | Phase 10 | Open | `compute_account_balance()` uses sqlite3.connect() |
| ledger_audit_engine DB access | High | Backend Team | Phase 10 | Open | Multiple functions use direct sqlite3.connect() |
| reconciliation wrapper | Medium | Backend Team | Phase 9 | Open | `find_potential_matches_with_db()` lines 514-537 |
| behavior/behaviour duplication | Low | Backend Team | Phase 9 | Open | 32-line router + 22-line service duplicates |
| interest_rate REAL column | Medium | Backend Team | Phase 8 | Open | ARCHITECTURE.md recommends bps migration |
| match_confidence float dual | Medium | DB migration | Open | Open | bps is authoritative, float retained |

---

## PHASE 9: Architecture Scorecard (9.4/10)

| Area | Score | Notes |
|------|-------|-------|
| Layer Separation | 9.8/10 | Clean Router→Service→(Repository OR Engine) boundaries |
| Engine Purity | 9.2/10 | 3 engines have DB access violations |
| Financial Correctness | 9.7/10 | Paise integers, Decimal arithmetic, proper rounding |
| Repository Compliance | 9.4/10 | Only repositories import FinanceDB (3 violations) |
| Testability | 9.6/10 | Pure functions enable isolation testing |
| Maintainability | 9.5/10 | Modular architecture, documented flows |
| Technical Debt | 8.3/10 | Engine violations, legacy columns, naming duplication |

**Score Justification:** Deductions for remaining engine purity violations (balance_engine, ledger_audit_engine), legacy compatibility columns (interest_rate REAL), and behavior/behaviour naming duplication. All other layers demonstrate strong architectural discipline.

---

## PHASE 10: Extensibility Review

### Adding New Engines
The architecture supports adding Tax Engine, Insurance Engine, Retirement Engine, Portfolio Engine:

**Verified Support:**
- Engines are pure functions accepting dict/list inputs
- Constants/thresholds are centralized in utils
- Services compose engines without tight coupling
- Repository pattern is uniform across entities

**Integration Path:**
1. Create `engines/tax_engine/` with pure functions
2. Add `TaxService` to service layer
3. Register in FinancialIntelligenceService composition

**No blockers identified** - the orchestration layer follows a consistent composition pattern.

---

## EXECUTIVE SUMMARY

The ClariFin_OS backend achieves strong architectural integrity through layered separation, integer-based financial precision, and deterministic computation engines. The Financial Intelligence system demonstrates clean composition where each engine (forecasting, optimization, scenario, goal planning) is independently reusable. Key improvement areas: eliminate 3 engine DB access violations and consolidate the behavior/behaviour naming variants.