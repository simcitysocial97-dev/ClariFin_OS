# Loan Intelligence Engine - ClariFinOS 2.0

*Enterprise-grade loan analytics and optimization*

---

## Purpose

Transform loan tracking into proactive debt optimization. Users should understand every aspect of their debt: cost, risk, and optimization opportunities.

---

## Architecture

Strict layered separation. Data flows one direction; no layer reaches across boundaries.

```
Engine → Services → Repositories → Routers
```

- **Engine (calculation-only):** Pure financial math — EMI, amortization, prepayment recalculation, floating-rate simulation, foreclosure payoff, loan analysis. No I/O, no DB, no request objects. Fully unit-testable and deterministic.
- **Services (orchestration):** Coordinate engines and repositories, apply business rules, and enforce invariants. Services call engines for math and repositories for persistence. Services never touch `FinanceDB` directly.
- **Repositories (persistence-only):** The ONLY layer permitted to import `FinanceDB` / `get_db()`. CRUD and query execution only — no financial calculations, no business logic.
- **Routers (transport):** Parse requests, delegate to services, serialize responses. Routers MUST NOT import `FinanceDB` or `get_db()`, and MUST NOT contain calculation logic.

**Boundary rules:**
- No `FinanceDB` import outside `src/repositories/`.
- Engines never import repositories or routers.
- Routers never call engines directly for computation (go through services).

---

## Implemented Features

The following capabilities are implemented and supported:

- **Loan CRUD** — Create, read, update, delete loans via the repository layer.
- **EMI** — Fixed and floating EMI computation.
- **Amortization** — Full schedule generation with principal/interest split and running balance.
- **Prepayment** — Recurring, lump-sum, and annual-bonus strategies with `REDUCE_TENURE` / `REDUCE_EMI` modes.
- **Floating-rate simulation** — Rate-reset modeling (MCLR annual / repo quarterly) with forward schedule projection.
- **Foreclosure** — Outstanding payoff computation including accrued interest to the closure date.
- **Loan analysis** — DTI, liability ratio, affordability, and interest-saved metrics (read-only analytics).
- **Performance optimizations** — Cached schedules, validated schedule regeneration, indexed queries.
- **Validation invariants** — Enforced at service/engine boundaries (non-negative balances, EMI reconciliation to the last paise, schedule sum-checks).

---

## Removed Features

The following capabilities are **intentionally out of scope**. They are removed by design, not missing or pending. Do not reimplement without explicit product sign-off.

- **Health scoring** — Loan health score and `LoanHealthService` removed.
- **Tax calculations** — Section 24 / 80C / pre-EMI tax benefit modeling removed.
- **Refinance analysis** — Break-even refinance evaluation removed.
- **Payoff strategies** — Avalanche / snowball / custom-priority optimization removed.
- **Comparison engine** — Cross-loan comparison engine removed.

---

## Supported Loan Types

| Type | Interest Model | Characteristics |
|------|--------------|-----------------|
| **Home Loan** | Floating (MCLR/BPLR) | Long tenure (10-30y), tax benefits |
| **Personal Loan** | Fixed | Short tenure (1-5y), no tax benefits |
| **Vehicle Loan** | Fixed/Floating | Asset depreciation, hypothecation |
| **Education Loan** | Fixed/Floating | Moratorium period, parent co-borrower |
| **Gold Loan** | Fixed | Overdraft facility, rate quarterly reset |
| **Business Loan** | Floating | Cash flow linkage, collateral |
| **Credit Line** | Floating | Overdraft, usage-based charges |
| **Overdraft** | Floating | Account-linked, daily interest |

---

## Interest Models

### Fixed Interest
```
EMI = P × r × (1+r)^n / ((1+r)^n - 1)

Where:
P = Principal (paise)
r = Monthly rate = annual_rate / (12 × 100)
n = Tenure in months

Interest for month = Outstanding × r
Principal for month = EMI - Interest
```

### Floating Interest
```
New_EMI = New_P × r_new × (1+r_new)^n_remaining / ((1+r_new)^n_remaining - 1)

Rate Reset Conditions:
- MCLR-based: Annual reset
- Repo-rate based: Quarterly reset
- Spread adjustment: Bank discretion
```

### Hybrid Interest
```
Year 1-3: Fixed at base_rate + spread
Year 4+: Floating at MCLR + spread

Teaser Rate Structure requires special amortization tracking.
```

---

## Amortization Schedule

### Standard Schedule
```
Month | Date | EMI | Principal | Interest | Balance | Cumulative Interest
1     | 2025-01-01 | 25000 | 15000 | 10000 | 8485000 | 10000
2     | 2025-02-01 | 25000 | 15250 | 9750 | 8469750 | 19750
...
```

### Dynamic Adjustements
- **Prepayment**: Recalculates remaining schedule
- **Rate Changes**: Adjusts future interest component
- **Tenure Extension**: Reduces EMI, increases total interest
- **Missed Payment**: Capitalizes interest, charges penalty

---

## Prepayment Strategies

### Recurring Prepayment
```
Scenario: Monthly surplus of ₹50,000

Monthly_prepend_paise = 5000000
Apply to earliest loan by avalanche priority

Interest Saved = Σ(remaining_interest) before - after
Tenure Reduced = months_to_closure before - after
```

### One-Time Lump Sum
```
Prepayment_amount = User input (paise)
Mode options:
- REDUCE_TENURE: Same EMI, shorter loan
- REDUCE_EMI: Same tenure, lower payments
```

### Annual Bonus Payment
```
Bonus_amount = Annual surplus event
Optimize timing (before rate reset for floating)
```

---

## Refinance Evaluation

> **REMOVED — Intentionally out of scope.** See [Removed Features](#removed-features). Not implemented; do not reimplement without sign-off.

### Break-Even Analysis
```
Savings_per_month = Old_EMI - New_EMI
One_time_cost = (New_Principal - Old_Outstanding) + processing_fees

Break_even_months = One_time_cost / Savings_per_month

If Break_even_months < Remaining_months: Refinance beneficial
```

### Tax Benefit Consideration
```
Old_tax_benefit = interest_paid_old × deduction_rate
New_tax_benefit = interest_paid_new × deduction_rate

Net_savings = gross_savings + tax_benefit_difference
```

---

## Payoff Strategies

> **REMOVED — Intentionally out of scope.** See [Removed Features](#removed-features). Not implemented; do not reimplement without sign-off.

### Avalanche Method
```
Priority order:
1. Highest interest rate first
2. Within same rate: longest tenure first
3. Minimum payment to others

Mathematical: Minimum total interest
Psychological: May feel slow for large balances
```

### Snowball Method
```
Priority order:
1. Smallest principal first
2. Within same principal: highest rate first

Mathematical: Maximum interest paid
Psychological: Quick wins motivate
```

### Custom Priority
```
User-defined priority based on:
- Emotional value (car vs home)
- Asset importance
- Cash flow impact
```

---

## Key Financial Metrics

### Debt-to-Income Ratio (DTI)
```
DTI = (Total_monthly_EMI + other_debt_payments) / Monthly_income × 100

Ratios:
- < 20%: Excellent
- 20-30%: Good
- 30-40%: Caution
- > 40%: Risky
```

### Liability Ratio
```
Liability_Ratio = Total_liabilities / Net_worth × 100

- < 50%: Healthy
- 50-100%: Moderate risk
- > 100%: Negative net worth
```

### Loan Affordability
```
Max_EMI = Monthly_income × max_dti (typically 40%)
Affordability_Score = (Current_EMI / Max_EMI) × 100

- > 100: Over capacity
- 80-100: Stretched
- 50-80: Comfortable
- < 50: Healthy
```

### Interest Saved
```
Interest_saved = Original_schedule_interest - Remaining_schedule_interest - prepayment_amount
```

---

## Tax Benefit Calculations

> **REMOVED — Intentionally out of scope.** See [Removed Features](#removed-features). Not implemented; do not reimplement without sign-off.

### Section 24 (Home Loan Interest)
```
Deduction_limit = ₹2,00,000 (old regime) / ₹3,00,000 (new regime)
Tax_savings = interest_paid × tax_rate (typically 20-30%)
```

### Section 80C (Principal Repayment)
```
Deduction_limit = ₹1,50,000 total across all 80C investments
Principal_repayment_qualifies = true
```

### Pre-EMI Interest
```
Home_loan_pre_emi_interest = Under_construction_period_interest
Deduction_available = true (max ₹50,000 under 80C + 24 combined)
```

---

## Loan Health Score

> **REMOVED — Intentionally out of scope.** See [Removed Features](#removed-features). Not implemented; do not reimplement without sign-off.

### Formula
```
Health_Score = 0.25 × DTI_Score + 0.25 × Utilization_Score + 0.25 × Stress_Score + 0.25 × Payment_Score

Where:
- DTI_Score = min(1, (Max_DTI - Current_DTI) / Max_DTI) × 100
- Utilization_Score = min(1, Sanction_Amount / Outstanding) × 100
- Stress_Score = 100 - Missed_payment_rate × 50
- Payment_Score = Months_since_start / 12 (capped at 100)
```

---

## Database Schema

### Required Changes
```sql
-- Extend loans table
ALTER TABLE loans ADD COLUMN interest_type TEXT DEFAULT 'fixed';
ALTER TABLE loans ADD COLUMN floating_baselined_rate REAL;
ALTER TABLE loans ADD COLUMN last_rate_reset_date TEXT;
ALTER TABLE loans ADD COLUMN prepayment_mode TEXT DEFAULT 'reduce_tenure';

-- New tables
CREATE TABLE loan_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id TEXT NOT NULL REFERENCES loans(id),
    payment_date TEXT NOT NULL,
    amount_paise INTEGER NOT NULL,
    principal_paise INTEGER NOT NULL,
    interest_paise INTEGER NOT NULL,
    late_fee_paise INTEGER DEFAULT 0,
    source_account_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE loan_scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id TEXT NOT NULL REFERENCES loans(id),
    scenario_name TEXT NOT NULL,
    prepayment_paise INTEGER,
    prepayment_date TEXT,
    new_tenure_months INTEGER,
    new_emi_paise INTEGER,
    interest_saved_paise INTEGER,
    months_saved INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);
```

---

## API Contract

All monetary values are in **paise** (₹1.00 = 100 paise) as `INTEGER`. All interest rates are in **basis points** (`rate_bps`, e.g. `875` = 8.75%). No loose floats for currency.

### Request / Response DTOs
- Loan create/update: `{ principal_paise: int, rate_bps: int, tenure_months: int, interest_type: "fixed"|"floating", ... }`
- Schedule response: `{ rows: [{ month, date, emi_paise, principal_paise, interest_paise, balance_paise, cumulative_interest_paise }] }`
- Prepayment simulation request: `{ prepayment_paise: int, mode: "reduce_tenure"|"reduce_emi", date: str }`
- Floating-rate simulation request: `{ new_rate_bps: int, effective_date: str }`
- Foreclosure request: `{ closure_date: str }` → `{ payoff_paise: int, accrued_interest_paise: int }`
- Loan analysis response: `{ dti_pct: int, liability_ratio_pct: int, affordability_pct: int, interest_saved_paise: int }`

### Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/loans` | GET | List loans |
| `/api/v1/loans` | POST | Create loan |
| `/api/v1/loans/{id}` | GET | Loan details with amortization |
| `/api/v1/loans/{id}/schedule` | GET | Monthly amortization schedule |
| `/api/v1/loans/{id}/prepayment-simulation` | POST | Simulate prepayment impact |
| `/api/v1/loans/{id}/floating-rate-simulation` | POST | Simulate floating-rate reset |
| `/api/v1/loans/{id}/foreclosure` | POST | Foreclosure payoff quote |
| `/api/v1/loans/{id}/analysis` | GET | Loan analysis metrics |
| `/api/v1/loans/{id}/payments` | POST | Record payment |

> Removed endpoints (out of scope): `/refinance-analysis`, `/health`, `/scenarios` (comparison).

---

## Services Required

> `LoanHealthService` and health-score / refinance methods are **removed** (see [Removed Features](#removed-features)).

### LoanService
```python
class LoanService:
    def get_amortization_schedule(loan_id) -> list[dict]
    def simulate_prepayment(loan_id, amount_paise, mode) -> dict
    def simulate_floating_rate(loan_id, new_rate_bps, effective_date) -> dict
    def quote_foreclosure(loan_id, closure_date) -> dict
    def analyze_loan(loan_id) -> dict
    def get_dti_ratio(user_id) -> float
    def get_liability_ratio(user_id) -> float
    def record_payment(loan_id, payment_data) -> LoanPayment
```

---

## Performance

- **Caching strategy** — Amortization schedules cached by `(loan_id, schedule_version)`; invalidated on prepayment or rate reset. Foreclosure/analysis results cached per request.
- **Schedule validation** — Regenerated schedules are validated: `Σ principal_paise == original principal`, final `balance_paise == 0` within 1 paise, EMI reconciles. Validation failure aborts before persist.
- **Benchmarks** — 360-row (30y) schedule generation and prepayment simulation are timed in `test_loan_engine_performance.py` and regression-gated.
- **Indexes** — `loan_payments(loan_id)`, `loan_scenarios(loan_id)`, `loans(user_id)` for fast list/lookup paths.

---

## Testing Strategy

### Unit Tests
- EMI calculation for all interest types (fixed + floating)
- Amortization schedule generation and reconciliation
- Prepayment impact math (reduce-tenure / reduce-EMI)
- Floating-rate reset and foreclosure payoff math
- Loan analysis metrics (DTI, liability ratio, affordability, interest saved)

### Integration Tests
- Schedule generation across tenures
- Prepayment → schedule regeneration
- Missed payment → penalty calculation
- DTI across multiple loans

### Acceptance Criteria
- [x] Floating rate reset works
- [x] Recurring prepayment supported
- [x] Foreclosure payoff accurate
- [x] Loan analysis metrics computed
- [x] Schedule validation invariants hold

---

## Future Enhancements

Ideas for later consideration (NOT current requirements; NOT in scope):

- Multi-currency loan support
- Hybrid / teaser-rate full tracking
- Co-borrower split modeling
- Restructuring / moratorium extension workflows
- Bulk prepayment optimizer across a portfolio

These are deferred until product sign-off and must not be treated as missing or incomplete work.
