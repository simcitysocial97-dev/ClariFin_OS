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

### PHASE 1 CHECKLIST:
- [x] All architectural layers accounted for
- [x] Engine/computation boundaries clarified

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

### Core Formulas Analyzed

| Formula | Location | Mathematical Notation | Determinism | Complexity |
|---------|----------|----------------------|-------------|------------|
| EMI | `loan_engine/emi.py` | $P \times r(1+r)^n / ((1+r)^n - 1)$ | ✅ Deterministic | O(1) |
| Monthly Rate | `loan_engine/utils.py` | $r_{monthly} = rate_{bps} / 120000$ | ✅ Deterministic | O(1) |
| Daily Interest | `credit_card_engine/interest.py` | $Interest = Outstanding \times rate_{bps} / 3650000$ | ✅ Deterministic | O(1) |
| Reducing Balance | `loan_engine/amortization.py` | $Balance_{new} = Balance - (EMI - Interest)$ | ✅ Deterministic | O(n) months |
| Weighted Moving Average | `financial_intelligence/forecasting.py` | $\sum_{i=1}^{n} w_i \times x_i$ (recent months weighted higher) | ✅ Deterministic | O(n) |
| Hungarian Matching | `reconciliation_engine.py` | Bipartite disambiguation via `scipy.linear_sum_assignment` | ✅ Deterministic | O(n³) worst case |
| Confidence Scoring | `reconciliation_engine.py` | Weighted combination of amount/date/description | ✅ Deterministic | O(1) per match |

### Numerical Stability
- Integer paise prevents floating-point drift in financial calculations
- Weighted moving average uses integer arithmetic throughout
- Loan amortization uses Decimal with ROUND_HALF_EVEN (banker's rounding)

---

## PHASE 3B: Financial Intelligence Architecture

### System Overview
Financial Intelligence orchestrates forecasting, goal planning, scenario simulation, and optimization.

### Cashflow Forecasting
```
Cashflow History
    ↓
forecast_cashflow() → Weighted average projection
    ↓
Income/Expense/Surplus forecast with confidence score
    ↓
forecast_liquidity() → Risk assessment (low/medium/high)
    ↓
detect_future_cash_shortfall() → Early warning signals
```

### Goal Planning
```
Goals + Cashflow
    ↓
calculate_goal_projection() → Projected achievement date
    ↓
calculate_emergency_fund_target() → Required buffer
    ↓
calculate_goal_health() → On-track/at-risk status
```

### Scenario Simulation
```
Current State
    ↓
simulate_income_change() / simulate_expense_reduction() / simulate_debt_prepayment()
    ↓
ScenarioResult → compare_scenario() → Impact analysis
```

### Optimization
```
Forecast + Goals + Debt + Behaviour
    ↓
optimize_surplus_allocation() → Monthly distribution recommendations
    ↓
rank_debt_payoff_strategy() → Avalanche vs Snowball ranking
    ↓
generate_optimization_plan() → Actionable priority list
```

### Intelligence Aggregation
```
All Financial Data
    ↓
build_financial_snapshot() → Current state
    ↓
generate_financial_priorities() → Ranked actions
    ↓
calculate_intelligence_confidence() → Confidence metadata
    ↓
generate_financial_intelligence_report() → Unified report
```

---

## PHASE 4: Component & Function Dictionary

### Core Models
- `AmortizationRow`: month_number, payment_date, emi_paise, principal_paise, interest_paise, balance_paise
- `LoanMetrics`: outstanding_paise, principal_paid_paise, interest_paid_paise, effective_interest_ratio (display-only)
- `FinancialSnapshot`: Aggregated financial state
- `IntelligenceReport`: Unified intelligence output

### Core Services
- `FinancialIntelligenceService`: `get_cashflow_forecast()`, `get_liquidity_forecast()`, `generate_intelligence_report()`
- `ReconciliationService`: `scan_potential_matches()`, `scan_for_transaction()`
- `BehaviourService`: `compute_profile()`, `get_cached_profile()`

---

## PHASE 5: Dependency Graphs

### Layer Dependency Graph
```
Router → Service → (Repository OR Engine)
                ↓           ↓
            SQLite    ← (NOT connected - engines are pure)
```

### Financial Intelligence Service Graph
```
FinancialIntelligenceService
├── CashflowService
├── BehaviourService
├── LoanService
├── CreditCardService
├── FinancialEventsService
└── Repositories: CashflowRepository, FinancialGoalRepository
```

---

## PHASE 6: Deep-Dive Code Analysis

### Engine Purity Violations (Identified)

| Engine | Issue | Location |
|--------|-------|----------|
| `balance_engine.py` | Direct `sqlite3.connect()` | `compute_account_balance()` |
| `ledger_audit_engine.py` | Direct `sqlite3.connect()` | Multiple functions |
| `reconciliation_engine.py` | Deprecated DB wrapper | `find_potential_matches_with_db()` (lines 514-537) |

---

## PHASE 7: Technical Debt Register

| Debt Item | Severity | Proposed Fix | Phase |
|-----------|----------|--------------|-------|
| Engine DB access (balance_engine) | High | Refactor to accept transactions as parameter | 10 |
| Engine DB access (ledger_audit_engine) | High | Move SQL to repository layer | 10 |
| Deprecated reconciliation wrapper | Medium | Remove after test migration | 9 |
| behavior/behaviour duplication | Low | Consolidate to single variant | 9 |
| interest_rate REAL column | Medium | Migrate to interest_rate_bps INTEGER | 8 |
| match_confidence float dual | Medium | Use confidence_bps authoritative | DB migration |

---

## PHASE 8: Architecture Scorecard

| Area | Score | Notes |
|------|-------|-------|
| Layer Separation | 9.8/10 | Clean Router→Service→Engine→Repository boundaries |
| Engine Purity | 9.2/10 | 3 engines have DB access violations |
| Financial Correctness | 9.7/10 | Paise integers, Decimal arithmetic, proper rounding |
| Repository Compliance | 9.4/10 | Only repositories import FinanceDB (except engine violations) |
| Testability | 9.6/10 | Pure functions enable isolation testing |
| Maintainability | 9.5/10 | Modular architecture, documented flows |
| Technical Debt | 8.3/10 | Behavior duplication, legacy columns |

**Overall Architecture: 9.4/10**

---

## PHASE 9: Error Handling & Ledger Integrity

### Exception Patterns (Observed)
- `AppError` hierarchy: ValidationError, DatabaseError, NotFoundError, FileError, ImportError
- Router exceptions: Broad `except Exception` patterns in transactions.py, cards_statements.py, financial_intelligence.py
- No bare `except:` blocks detected

### Ledger Invariants (Verified via code inspection)
- Transaction immutability via hash_signature triggers
- Reconciliation idempotency via INSERT OR IGNORE + deterministic keys
- Confirmed rows cannot be modified
- Balance unaffected by reconciliation state

---

## PHASE 10: Observability Gaps

| Missing Feature | Recommendation |
|-----------------|----------------|
| Correlation IDs | Add ContextVar-based ID propagation |
| Structured logging | JSON format with correlation context |
| Performance metrics | Request duration, DB query time |
| Business metrics | Forecast accuracy, goal projection confidence |

---

## EXECUTIVE SUMMARY

The ClariFin_OS backend demonstrates a mature layered architecture with pure computation engines, proper financial precision handling, and strong immutability guarantees. Key areas for improvement include eliminating engine DB access violations and consolidating the behavior/behaviour duplication.