# Loan Intelligence Engine - ClariFinOS 2.0

*Enterprise-grade loan analytics and optimization*

---

## Purpose

Transform loan tracking into proactive debt optimization. Users should understand every aspect of their debt: cost, risk, and optimization opportunities.

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

## Required APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/loans` | GET | List all loans with health scores |
| `/api/v1/loans` | POST | Create new loan |
| `/api/v1/loans/{id}` | GET | Loan details with amortization |
| `/api/v1/loans/{id}/schedule` | GET | Monthly amortization |
| `/api/v1/loans/{id}/prepayment-simulation` | POST | Simulate prepayment impact |
| `/api/v1/loans/{id}/refinance-analysis` | POST | Refinance evaluation |
| `/api/v1/loans/{id}/health` | GET | Detailed health breakdown |
| `/api/v1/loans/{id}/scenarios` | GET | Saved scenarios |
| `/api/v1/loans/{id}/payments` | POST | Record payment |

---

## Services Required

### LoanService
```python
class LoanService:
    def get_amortization_schedule(loan_id) -> list[dict]
    def simulate_prepayment(loan_id, amount_paise, mode) -> dict
    def evaluate_refinance(loan_id, new_rate, new_tenure) -> dict
    def compute_health_score(loan_id) -> float
    def get_dti_ratio(user_id) -> float
    def get_liability_ratio(user_id) -> float
    def record_payment(loan_id, payment_data) -> LoanPayment
```

### LoanHealthService
```python
class LoanHealthService:
    def compute_dti_score(user_id) -> float
    def compute_utilization_score(loan_id) -> float
    def compute_stress_score(loan_id) -> float
    def compute_payment_score(loan_id) -> float
    def get_recommendations(loan_id) -> list[str]
```

---

## Testing Strategy

### Unit Tests
- EMI calculation for all interest types
- Prepayment impact math
- Refinance break-even calculations
- Health score components

### Integration Tests
- Schedule generation across tenures
- Prepayment → schedule regeneration
- Missed payment → penalty calculation
- DTI across multiple loans

### Acceptance Criteria
- [ ] Floating rate reset works
- [ ] Recurring prepayment supported
- [ ] Refinance analysis accurate
- [ ] Tax benefits calculated
- [ ] Avalanche/snowball strategies computed