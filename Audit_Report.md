# ClariFin_OS Backend Architecture Audit Report

## PHASE 1: Executive Summary & System Topology

- **High-Level Purpose:** ClariFin_OS is a Personal Financial Operating System that processes bank statement PDFs from Indian banks, extracts and categorizes transactions, and provides a unified dashboard for financial analysis. Its core principles are mathematical correctness and ledger integrity, ensuring every financial transaction is traceable and verifiable.

- **Architectural Pattern:** The backend primarily employs a **Layered Architecture**. This is evident from the distinct separation of concerns into Routers, Services, Engines, and Repositories.

- **Layer-by-Layer Responsibility Matrix:**
    - **Routers** (`src/routers/`, ~25 files): Handle HTTP requests, validate input parameters, and delegate to the appropriate Service layer. They are the API boundary and should not contain business logic or direct database access.
    - **Services** (`src/services/`, ~17 files): Orchestrate business logic. They coordinate interactions between Repositories (for data persistence) and Engines (for pure computations). Services should not contain SQL queries.
    - **Engines** (`src/engines/`, ~12+ packages): Contain pure computational and algorithmic logic. They are designed to be deterministic and should ideally have no direct database access or external dependencies, operating solely on input parameters and returning results.
    - **Repositories** (`src/repositories/`, ~26 files): Responsible for data access and persistence, primarily interacting with the SQLite database.
    - **Models** (`src/models/`, ~19 files): Define the data structures (Pydantic models) used across the application.
    - **Database** (`src/db.py`, `data/finance.db`): SQLite database managed by the `FinanceDB` class. All monetary values are stored as `INTEGER paise` (₹1.00 = 100 paise).

### PHASE 1 CHECKLIST:
- [x] Verified that all custom directories/layers in the repository are accounted for.
- [x] Confirmed the definition of boundaries between business logic (Services) and algorithmic computation (Engines).

---

## PHASE 2: End-to-End Execution Flow

### Execution Path A: Loan Schedule Generation & EMI Calculation

```
1. Router (src/routers/loans.py → get_loan_schedule)
   - Validates loan_id path parameter
   - Instantiates LoanService()
   - Calls service.get_schedule(loan_id)
   - Catches ValueError → raises NotFoundError

2. Service (src/services/loan_service.py → get_schedule)
   - Calls self.loan_repo.get_loan(loan_id) → returns loan dict
   - Extracts: outstanding_paise, interest_rate (float), tenure_months, disbursed_date
   - Converts rate_bps = int(loan["interest_rate"] * 100)
   - Calls generate_schedule(principal_paise=..., annual_rate_bps=..., tenure_months=..., start_date=...)

3. Engine (src/engines/loan_engine/amortization.py → generate_schedule)
   - Receives: principal_paise (int), annual_rate_bps (int), tenure_months (int), start_date (str)
   - Computes monthly_rate via bps_to_monthly_rate(annual_rate_bps) → Decimal
   - Calculates EMI via compute_emi_fixed() with caching (lru_cache)
   - Iterates months 1..tenure_months with ROUND_HALF_EVEN precision
   - Returns list[AmortizationRow]

4. Repository (src/repositories/loan_repository.py → get_loan)
   - SQL: SELECT * FROM loans WHERE id = ?
   - Returns dict with loan data
```

### Execution Path B: Transaction Reconciliation

```
1. Router (src/routers/reconciliation.py → scan_matches)
   - Expects household_id as query param (optional)
   - Delegates to ReconciliationService.scan_potential_matches()

2. Service (src/services/reconciliation_service.py → scan_potential_matches)
   - Builds household_account_map via AccountRepository
   - Calls self.repo.get_unreconciled_debits(household_id) → list[dict]
   - Calls self.repo.get_unreconciled_credits(household_id) → list[dict]
   - Calls find_potential_matches(debits, credits, household_account_map, max_date_window_days=3)

3. Engine (src/engines/reconciliation_engine.py → find_potential_matches)
   - Receives: debits list, credits list, household_account_map dict
   - For each debit/credit pair: validates amount, date, account boundaries
   - Applies Hungarian algorithm for bipartite disambiguation (when multiple candidates)
   - Returns list[dict] with confidence_bps (int 0-10000) authoritative field

4. Repository (src/repositories/reconciliation_repository.py)
   - get_unreconciled_debits(): SQL filtering
   - get_unreconciled_credits(): SQL filtering
```

### Execution Path C: EMI Payment Detection

```
1. Service (src/services/transaction_intelligence_service.py → classify_emi_payments)
   - Fetches unclassified debit transactions via TransactionRepository
   - Passes (debit_txn, loan_candidates, schedule_lookup) to detect_emi_payment()

2. Engine (src/engines/transaction_intelligence/loan_emi_detector.py → detect_emi_payment)
   - Pure function: no DB access
   - Checks amount tolerance: ±1%, date proximity: ±3 days, keywords
   - Returns EMIDetectionResult or None

3. Repository (src/repositories/transaction_classification_repository.py)
   - Persists classification via insert_classification()
```

### PHASE 2 CHECKLIST:
- [x] Traced at least two core execution paths from HTTP Request to Database Commit/Response.
- [x] Explicitly named every function, variable payload, and file path involved in the sequence.

---

## PHASE 3: Mathematical & Financial Formula Validation

### Formula Extraction & Analysis

| Formula | Location | Mathematical Notation | Status |
|---------|----------|---------------------|--------|
| **EMI (Equated Monthly Installment)** | `src/engines/loan_engine/emi.py` → `compute_emi_fixed()` | $EMI = P \times r \times (1+r)^n / ((1+r)^n - 1)$ | ✅ Decimal, ROUND_HALF_EVEN, cached |
| **Monthly Interest Rate** | `src/engines/loan_engine/utils.py` → `bps_to_monthly_rate()` | $r_{monthly} = rate_{bps} / 120000$ | ✅ Integer basis points |
| **Daily Interest (Credit Card)** | `src/engines/credit_card_engine/interest.py` | $r_{daily} = rate_{bps} / 3650000$ (365-day year) | ✅ Integer paise |
| **Reducing Balance Schedule** | `src/engines/loan_engine/amortization.py` | Each month: $Interest = Balance \times r_{monthly}$ | ✅ Decimal precision |
| **Prepayment Tenure Recalc** | `src/engines/loan_engine/prepayment.py` | $n = \ln(EMI / (EMI - P \times r)) / \ln(1 + r)$ | ✅ Logarithmic with Decimal |
| **Minimum Due (Credit Card)** | `src/engines/credit_card_engine/billing.py` | $MinDue = max(floor, Outstanding \times minDuePct/10000)$ | ✅ Basis points |
| **Confidence Score** | `src/engines/reconciliation_engine.py` | Weighted combination of amount, date, description | ⚠️ Float + bps dual |

### Data Type & Precision Audit

| Component | Type Used | Status | Notes |
|-----------|-----------|--------|-------|
| `principal_paise` | int | ✅ | Rupees × 100 |
| `emi_paise` | int | ✅ | Decimal computed |
| `interest_rate` in loans | REAL | ⚠️ | Legacy - migrate to bps |
| `effective_interest_ratio` in LoanMetrics | float | ⚠️ | Display-only ratio |
| `match_confidence` | REAL | ⚠️ | Deprecated, bps authoritative |
| `amount_paise` in transactions | INTEGER | ✅ | Primary column |

### Rounding Mechanism Analysis

| Location | Rounding Method | Status |
|----------|-----------------|--------|
| `emi.py` | `ROUND_HALF_EVEN` | ✅ Banker's rounding |
| `amortization.py` | `ROUND_HALF_EVEN` | ✅ Applied to interest |
| `credit_card_engine/interest.py` | `ROUND_HALF_EVEN` | ✅ Applied to daily interest |
| `common/calculations.py` | `ROUND_HALF_UP` | ✅ User-facing parsing |

### PHASE 3 CHECKLIST:
- [x] Extracted every formula and represented it in standard mathematical text.
- [x] Flagged any instance of floating-point inaccuracies.
- [x] Validated that rounding mechanisms do not introduce compound tracking errors.

---

## PHASE 4: Component & Function Dictionary

### Core Models (Domain Entities)

**Loan Engine Models** (`src/engines/loan_engine/models.py`):
- `AmortizationRow`: month_number, payment_date, emi_paise, principal_paise, interest_paise, balance_paise, cumulative_interest_paise
- `LoanMetrics`: outstanding_paise, principal_paid_paise, interest_paid_paise, remaining_interest_paise, remaining_tenure_months, tenure_saved_months, total_payments_remaining, effective_interest_ratio
- `PrepaymentResult`: prepayment_paise, mode, original_emi_paise, new_emi_paise, months_saved, interest_saved_paise, loan_closed, new_schedule

**Core Models** (`src/models/`):
- `Loan`: id, name, lender, principal_paise, tenure_months, interest_rate, disbursed_date, outstanding_paise
- `Transaction`: id, statement_id, date, description, amount_paise, type, category, hash_signature
- `Reconciliation`: id, debit_txn_id, credit_txn_id, amount_paise, date_diff_days, confidence_bps, match_type, deterministic_key, status

### Core Services

| Service | Key Functions | Purpose |
|---------|---------------|---------|
| `ReconciliationService` | `scan_potential_matches()`, `scan_for_transaction()`, `insert_match()` | Reconciliation orchestration |
| `LoanService` | `get_schedule()`, `compute_metrics()` | Loan business logic |
| `BehaviourService` | `compute_profile()`, `invalidate_behaviour_cache()` | Behavioral analytics |
| `TransactionIntelligenceService` | `classify_emi_payments()`, `detect_cash_conversions()` | Transaction classification |
| `CashflowService` | `compute_monthly_cashflow()` | Monthly cashflow analysis |

### Core Engines

| Engine | Key Functions | Status |
|--------|---------------|--------|
| `loan_engine/` | `compute_emi_fixed()`, `generate_schedule()`, `apply_prepayment()` | ✅ Pure functions |
| `reconciliation_engine.py` | `find_potential_matches()`, `find_matches_for_transaction()` | ⚠️ Mixed (has deprecated wrapper) |
| `behaviour_engine/` | `compute_profile()`, `detect_patterns()` | ✅ Pure functions |
| `credit_card_engine/` | `compute_daily_interest()`, `compute_outstanding()` | ✅ Pure functions |
| `cashflow_engine.py` | `compute_monthly_cashflow()` | ✅ Pure integer arithmetic |

### PHASE 4 CHECKLIST:
- [x] Documented core state-carrying classes across layers.
- [x] Mapped cross-layer dependencies (Router→Service→Engine→Repository).

---

## PHASE 5: Deep-Dive Code Analysis

### Engine Purity Violations (CRITICAL)

| Engine File | Lines | Issue | Recommendation |
|-------------|-------|-------|----------------|
| `reconciliation_engine.py` | 514-537 | `sqlite3.connect(db_path)` in `find_potential_matches_with_db()` | Deprecate wrapper |
| `balance_engine.py` | Multiple | Direct `sqlite3.connect(db_path)` in `compute_account_balance()` | Refactor to accept data as parameter |
| `ledger_audit_engine.py` | Multiple | Direct `sqlite3.connect(db_path)` | Move SQL to repository |

**Recommended Refactor Pattern:**
```python
# ✅ PURE FUNCTION - No DB access
def compute_account_balance(transactions: list[dict], account_id: str) -> dict:
     # Process transactions passed as parameter
     ...

# ❌ VIOLATION - Direct DB access
def compute_account_balance(db_path: str, account_id: str) -> dict:
    conn = sqlite3.connect(db_path)  # Should be in repository!
```

### Duplicate Code Systems (US/UK Spelling)

| Component | Status | Recommendation |
|-----------|--------|----------------|
| `routers/behavior.py` (32 lines) | Legacy wrapper | Mark deprecated, route to `behaviour.py` |
| `services/behavior_service.py` (22 lines) | Legacy shim | Add deprecation warning |
| `engines/behavior_engine.py` | Deprecated with warning | Remove after migration |

### Repository Boundary Compliance

✅ Only files under `src/repositories/` import FinanceDB. Exception: Some engines use direct `sqlite3.connect()`.

---

### PHASE 5 CHECKLIST:
- [x] Identified structural bottlenecks (engine DB access patterns)
- [x] Provided refactoring code snippets for purity violations
- [x] Documented duplicate code systems with resolution path
- [x] Verified repository boundary compliance

---

## PHASE 6: Error Handling & Ledger Integrity

### Exception Handling Patterns

**Error Classes** (`src/errors.py`):
- `AppError` (base): message, status_code, details
- `ValidationError` (400): Input validation errors  
- `DatabaseError` (500): Database operation errors
- `NotFoundError` (404): Resource not found
- `FileError`, `ImportError` (400): File/import errors

**Exception Handling Counts:**
- `transactions.py`: 5 `except Exception` instances
- `cards_statements.py`: 5 `except Exception` instances
- `behaviour.py`: Mixed `except Exception` and `except NotFoundError`
- `financial_intelligence.py`: 6 `except Exception` instances

**No bare `except:` blocks found** - Good practice maintained.

### Ledger Integrity Safeguards

| Invariant | Location | Status |
|-----------|----------|--------|
| Transaction immutability | `src/db.py` schema | ✅ Enforced via SQL triggers |
| Reconciliation idempotency | `ReconciliationRepository` | ✅ INSERT OR IGNORE + deterministic keys |
| Confirmed row immutability | Database triggers | ✅ Cannot modify once confirmed |
| Balance unaffected by reconciliation | Tests verified | ✅ Invariant upheld |

---

### PHASE 6 CHECKLIST:
- [x] Audited try-except blocks across routers
- [x] Verified transaction boundaries and immutability
- [x] Confirmed idempotent reconciliation design

---

## PHASE 7: Observability Strategy

### Current State

**Logging Infrastructure** (`src/logger.py`):
- Basic file/console logging
- `log_error()` with structured details
- No correlation IDs or request tracing
- No metric emission

**Missing Observability:**
- [ ] Correlation ID propagation
- [ ] Structured log events (JSON format)
- [ ] Performance metrics (request duration, DB query time)
- [ ] Business metrics (reconciliation match rate)
- [ ] Log sanitization for PII

### Recommended Telemetry Hooks

```python
# src/telemetry.py - Proposed
from contextvars import ContextVar

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

def set_correlation_id(req_id: str) -> None:
    correlation_id.set(req_id)

def get_correlation_id() -> str:
    return correlation_id.get()
```

---

### PHASE 7 CHECKLIST:
- [ ] Provided telemetry hooks (recommended in report)
- [x] Identified logging gaps
- [ ] Verified data protection in logs (recommended)

---

## EXECUTIVE SUMMARY OF FINDINGS

### 🔴 CRITICAL Issues (Must Fix)
1. **Engine Purity Violations:** 3 engines directly access SQLite instead of accepting data as parameters
2. **Duplicate Systems:** `behavior`/`behaviour` spelling variants cause maintenance overhead

### 🟡 WARNING Issues (Should Address)
1. `effective_interest_ratio: float` in `LoanMetrics` - non-financial ratio
2. `match_confidence: float` alongside `confidence_bps` - dual representation
3. Broad `except Exception` patterns in routers obscure root causes
4. No correlation IDs for request tracing

### 🟢 GOOD Practices
1. All monetary values stored as INTEGER paise
2. ROUND_HALF_EVEN rounding for financial calculations
3. Deterministic reconciliation matching
4. INSERT OR IGNORE for idempotency
5. No bare `except:` blocks
6. Transaction immutability via hash_signature triggers

---

## RECOMMENDED ACTIONS

### Immediate (Next Sprint)
- [ ] Refactor `balance_engine.py` to eliminate direct `sqlite3.connect()`
- [ ] Refractor `ledger_audit_engine.py` for repository pattern
- [ ] Deprecate `find_potential_matches_with_db()` wrapper
- [ ] Add deprecation notices to `behavior.py` and `behavior_service.py`

### Short-term (Next Month)
- [ ] Implement correlation ID framework
- [ ] Migrate `interest_rate` column to `interest_rate_bps` INTEGER
- [ ] Replace broad `except Exception` with specific types

### Long-term (Q3 2025)
- [ ] Consolidate `behavior`/`behaviour` systems
- [ ] Add OpenTelemetry metrics
- [ ] Add log sanitization for PII protection