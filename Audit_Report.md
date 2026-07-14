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

### PHASE 1 CHECKLIST:
- [x] All architectural layers accounted for
- [x] Engine/computation boundaries documented

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
| Weighted Moving Average | `financial_intelligence/forecasting.py` | $\sum_{i=1}^{n} w_i \times x_i$ (recent months weighted higher) | ✅ Deterministic | O(n) |
| Hungarian Matching | `reconciliation_engine.py` | Bipartite disambiguation via `scipy.linear_sum_assignment` | ✅ Deterministic | O(n³) worst case |
| Confidence Scoring | `reconciliation_engine.py` | Weighted combination of amount/date/description | ✅ Deterministic | O(1) per match |

### Numerical Stability (Verified)
- Integer paise prevents floating-point drift in financial calculations
- Weighted moving average uses integer arithmetic throughout
- Loan amortization uses Decimal with ROUND_HALF_EVEN (banker's rounding)

---

## PHASE 3B: Financial Intelligence Architecture (Phase 9 Composition)

### Complete Orchestration Pipeline

```
Repositories
      │
      ▼
CashflowService ──► BehaviourService ──► LoanService ──► CreditCardService
      │                    │               │                  │
      ▼                    ▼               ▼                  ▼
cashflow_engine      behaviour_engine/      loan_engine/    credit_card_engine/
      │                    │               │                  │
      ▼                    ▼───────────────┴──────────────────▼
              FinancialIntelligenceService
                      │
                      ▼
        ┌─────────────┼─────────────┐
        ▼            ▼            ▼
forecasting.py  goal_planner.py  optimization.py
        ▼            ▼            ▼
    scenario.py  intelligence.py
                      │
                      ▼
       Unified Financial Intelligence Report
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

---

## PHASE 5: Dependency Graphs

### Layer Dependency Graph
```
                Router
                   │
                   ▼
           Application Service
           ┌────────┴────────┐
           ▼        ▼
Repository Layer  Engine Layer
           ▼        ▼
        SQLite   Pure Computation
```

---

## PHASE 6: Deep-Dive Code Analysis (Observed Issues)

### Engine Purity Violations

| Engine | Issue | Location | Status |
|--------|-------|----------|--------|
| `balance_engine.py` | Direct `sqlite3.connect()` | `compute_account_balance()` | Open |
| `ledger_audit_engine.py` | Direct `sqlite3.connect()` | Multiple functions | Open |
| `reconciliation_engine.py` | Deprecated DB wrapper | `find_potential_matches_with_db()` (lines 514-537) | Open |

---

## PHASE 7: Technical Debt Register

| Debt | Severity | Owner | Target Phase | Status |
|------|----------|-------|--------------|--------|
| balance_engine DB access | High | Backend Team | Phase 10 | Open |
| ledger_audit_engine DB access | High | Backend Team | Phase 10 | Open |
| Deprecated reconciliation wrapper | Medium | Backend Team | Phase 9 | Open |
| behavior/behaviour duplication | Low | Backend Team | Phase 9 | Open |
| interest_rate REAL column | Medium | Backend Team | Phase 8 | Open |
| match_confidence float dual | Medium | Backend Team | DB migration | Open |

---

## PHASE 8: Architecture Scorecard (9.4/10)

| Area | Score | Notes |
|------|-------|-------|
| Layer Separation | 9.8/10 | Clean Router→Service→(Repository OR Engine) boundaries |
| Engine Purity | 9.2/10 | 3 engines have DB access violations |
| Financial Correctness | 9.7/10 | Paise integers, Decimal arithmetic, proper rounding |
| Repository Compliance | 9.4/10 | Only repositories import FinanceDB (3 violations identified) |
| Testability | 9.6/10 | Pure functions enable isolation testing |
| Maintainability | 9.5/10 | Modular architecture, documented flows |
| Technical Debt | 8.3/10 | Engine violations, legacy columns, naming duplication |

**Score Justification:** Deductions for remaining engine purity violations, legacy compatibility columns, and behavior/behaviour naming duplication.

---

## PHASE 9: Error Handling & Observability

### Current State (Observed)
- `AppError` hierarchy with ValidationError, DatabaseError, NotFoundError
- Broad `except Exception` patterns in transactions.py, cards_statements.py, financial_intelligence.py
- No bare `except:` blocks detected

### Target State (Recommended)
- Domain-specific exceptions in services
- Centralized exception translation to HTTP responses via error handlers
- Unexpected exceptions logged with full context, returned as generic 500 responses

---

## PHASE 10: Observability Gaps

| Missing Feature | Recommendation |
|-----------------|----------------|
| Correlation IDs | Add ContextVar-based ID propagation for request tracing |
| Structured logging | JSON format with correlation context and model_version |
| Performance metrics | Request duration, DB query time, engine execution time |
| Business metrics | Forecast accuracy, goal projection confidence, match rate |

---

## EXECUTIVE SUMMARY

The ClariFin_OS backend achieves strong architectural integrity through layered separation, integer-based financial precision, and deterministic computation engines. Key improvement areas: eliminate 3 engine DB access violations, consolidate behavior/behaviour naming variants, and add correlation ID framework for production observability.