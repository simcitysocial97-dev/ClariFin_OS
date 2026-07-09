# Financial Models - ClariFinOS 2.0

*Deterministic formulas for all financial calculations*

---

## Core Principle: Integer Paise Arithmetic

All monetary values are stored and calculated as **integer paise** (₹1.00 = 100 paise).

### Conversion Functions
```python
def rupees_to_paise(rupees: Union[int, float, str]) -> int:
    """Convert rupees to integer paise using Decimal quantization."""
    if isinstance(rupees, int):
        return rupees * 100
    paise = Decimal(str(rupees)) * Decimal('100')
    return int(paise.quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def paise_to_rupees(paise: int) -> float:
    """Convert paise to rupees for display."""
    return paise / 100.0
```

---

## Account Financial Models

### Interest Earned (Savings Account)
```
Formula: Simple interest for daily balances

Daily_Interest = (Average_Daily_Balance × Annual_Rate) / 365 / 100

Where:
- Average_Daily_Balance calculated from daily snapshots
- Annual_Rate from institution metadata (e.g., 3.5 for 3.5%)
- Result in paise, rounded to nearest integer

Edge Cases:
- Negative balance: Interest = 0
- Account dormant: Interest may differ (check bank rules)
```

### Account Health Score
```
Health_Score = 0.3 × Activity_Score + 0.3 × Balance_Score + 0.2 × Fee_Score + 0.2 × Relationship_Score

Activity_Score = min(1, Transactions_Per_Month / 5) × 100
Balance_Score = If positive and growing: 100; If negative: 50; If dormant: 0
Fee_Score = 100 - (Penalties_Count × 10)
Relationship_Score = min(1, Linked_Accounts_Count / 3) × 100
```

---

## Loan Financial Models

### EMI Calculation (Reducing Balance)
```
EMI = P × r × (1+r)^n / ((1+r)^n - 1)

Where:
- P = Principal outstanding (paise)
- r = Monthly interest rate = Annual_Rate / (12 × 100)
- n = Remaining tenure in months
- Result = EMI in paise, rounded

Special Cases:
- If Annual_Rate = 0: EMI = P / n
- If EMI <= Interest: Not viable (negative amortization)
```

### Amortization Schedule
```
For each month m from 1 to n:
    Interest_m = Outstanding_(m-1) × r
    Principal_m = EMI - Interest_m
    Outstanding_m = Outstanding_(m-1) - Principal_m

Final month adjustment:
    Principal_n = Outstanding_(n-1)
    Interest_n = Outstanding_(n-1) × r
    EMI_n = Principal_n + Interest_n
    Outstanding_n = 0
```

### Prepayment Impact
```
Scenario 1: Reduce Tenure
    New_Principal = Outstanding - Prepayment
    New_Tenure = Months to closure at same EMI
    Interest_Saved = Original_Total_Interest - New_Total_Interest

Scenario 2: Reduce EMI
    New_Tenure = Remaining tenure unchanged
    New_EMI = EMI for New_Principal over remaining tenure
    Monthly_Savings = Original_EMI - New_EMI
```

### Refinance Break-Even
```
Monthly_Savings = Old_EMI - New_EMI
One_Time_Cost = (New_Loan_Amount - Old_Outstanding) + Processing_Fees

Break_Even_Months = One_Time_Cost / Monthly_Savings

If Break_Even_Months < Remaining_Months: Refinance recommended
```

### Debt-to-Income Ratio
```
DTI = (Total_Monthly_EMI × 100) / Monthly_Income

Where:
- Total_Monthly_EMI = Σ(EMI for all active loans)
- Monthly_Income = Median of last 6 months credits

Thresholds:
- DTI < 20%: Excellent
- DTI 20-30%: Good
- DTI 30-40%: Caution
- DTI > 40%: Risky
```

---

## Credit Card Financial Models

### Credit Utilization
```
Utilization_Rate = Outstanding / Credit_Limit × 100

Where:
- Outstanding = Current billing cycle spend not paid
- Credit_Limit from card metadata

Impact:
- 0-30%: Neutral to positive
- 30-75%: Caution for credit score
- > 75%: Negative credit score impact
```

### Interest on Revolving Balance
```
Daily_Rate = Annual_Interest / 365 / 100
Daily_Interest = Outstanding_Balance × Daily_Rate
Monthly_Interest = Σ(Daily_Interest) for billing days

Minimum_Interest_Charge = ₹100 (if applicable)
```

### Payment Optimization
```
Scenario 1: Full Payment
    Amount = Outstanding
    Interest_Avoided = Monthly_Interest

Scenario 2: Minimum Payment
    Amount = Minimum_Due
    Interest_On_Remaining = Outstanding × Daily_Rate × Days_Revolving

Optimal_Choice = if Cash_Available >= Outstanding: Full Payment else: Minimum Payment
```

---

## Behavioural Statistical Models

### Savings Discipline Score
```
Monthly_Surplus = Σ(credits) - Σ(essential_debits)
Savings_Rate = Monthly_Surplus / Σ(credits) × 100

Discipline_Score = Savings_Rate × 2 (capped at 100)

Bands:
- 0-40: Needs improvement
- 40-70: Developing
- 70-100: Strong discipline
```

### Cashflow Stability Index
```
Income_Stability = 1 - (StdDev_Income / Average_Income)
Expense_Stability = 1 - (StdDev_Expense / Average_Expense)

Stability_Index = 0.6 × Income_Stability + 0.4 × Expense_Stability

Scaled to 0-100.
```

### Lifestyle Inflation
```
Non_Essential_Current = Σ(Current_Month_Non_Essential)
Non_Essential_Previous = Σ(Same_Month_Last_Year_Non_Essential)

Inflation_Rate = (Non_Essential_Current - Non_Essential_Previous) / Non_Essential_Previous × 100

Flag if Inflation_Rate > 10%.
```

### Impulse Score
```
Impulse_Count = Σ(Transactions where:
    Time between 20:00-02:00 AND
    Day in [Saturday, Sunday] AND
    Amount between 500-5000 paise AND
    Category in ['Entertainment', 'Shopping', 'Food'])

Impulse_Score = Impulse_Count / Total_Transactions × 100

Risk threshold: Impulse_Score > 20.
```

---

## Reconciliation Financial Models

### Confidence Score
```
confidence = amount_match_score + date_match_score + description_similarity

amount_match_score:
- Exact match: 0.4
- Within ₹1 tolerance: 0.3
- No match: 0.0

date_match_score:
- Same day: 0.4
- 1 day diff: 0.3
- 2-3 days diff: 0.2
- > 3 days: 0.0

description_similarity:
- Both contain same transfer keyword: 0.2
- Otherwise: 0.0

Result capped at 1.0, rounded to 4 decimals.
```

---

## Forecast Models

### Cashflow Prediction (Exponential Smoothing)
```
Forecast_t = α × Actual_(t-1) + (1-α) × Forecast_(t-1)

Where:
- α = Smoothing parameter (0.2-0.4)
- Calculated separately for income and expenses

Confidence_Interval = ± (2 × StdDev of residuals)
```

### Net Worth Projection
```
Future_NW = Current_NW + Σ(Forecasted_Cashflow) - Σ(Projected_Expenses)

Conservative estimate uses 0.8 multiplier on cashflows.
Optimistic estimate uses 1.2 multiplier.
```

---

## Tax Models (India)

### Capital Gains (Equity)
```
Short_Term_CG = Σ(Sale_Value - Buy_Value) where holding < 12 months
Long_Term_CG = Σ(Sale_Value - Buy_Value - indexation_benefit)

STCG_Rate = 15% (for equity)
LTCG_Rate = 10% (above ₹1 lakh/year)
```

### Home Loan Tax Benefit
```
Section_24_Deduction = min(Interest_Paid, ₹2,00,000)
Section_80C_Deduction = min(Principal_Repayment, ₹1,50,000)

Tax_Savings = (Section_24_Benefit + Section_80C_Benefit) × Tax_Rate

Where Tax_Rate typically 20% or 30% based on income slab.
```

---

## Validation Examples

### Test Case: EMI Calculation
```
Input:
- Principal = ₹10,00,000 (10000000 paise)
- Annual_Rate = 8.5%
- Tenure = 240 months (20 years)

Expected Output:
- EMI = ₹87,996 (8799600 paise) per month

Verification:
- Total_Payment = ₹87,996 × 240 = ₹2,11,19,040
- Total_Interest = ₹1,11,19,040
- Verify with online EMI calculator
```

### Test Case: Credit Utilization
```
Input:
- Credit_Limit = ₹5,00,000 (50000000 paise)
- Outstanding = ₹3,75,000 (37500000 paise)

Expected Output:
- Utilization = 75%
- Credit_Score_Impact = Negative (threshold crossed)
```

### Test Case: DTI Ratio
```
Input:
- Home_Loan_EMI = ₹50,000
- Personal_Loan_EMI = ₹15,000
- Monthly_Income = ₹1,00,000

Expected Output:
- DTI = (₹65,000 / ₹1,00,000) × 100 = 65%
- Risk level: High (>50%)
```

---

## Industry References

| Model | Source | Formula Reference |
|-------|--------|-------------------|
| EMI | Indian Banking Association | Standard reducing balance formula |
| XIRR | Excel/Actuarial Standards | Newton-Raphson iteration |
| Credit Score Factors | CIBIL/Experian | Standard industry weights |
| Tax Calculations | Income Tax Act 1961 | Section 80C, 24, capital gains rules |
| Forecast Models | ARIMA literature | Exponential smoothing standard |
| Risk Metrics | Basel III banking | Coefficient of variation, volatility |

---

## Precision Requirements

### All Monetary Values
- Storage: `INTEGER` (paise)
- Intermediate: `Decimal` with 4 decimal places
- Display: Round to 2 decimal places (rupees)

### All Rates
- Storage: `REAL` (2 decimal places for %)
- Computation: Convert to decimal for precision

### Date Calculations
- All dates ISO format (YYYY-MM-DD)
- Date arithmetic in days
- Month arithmetic using calendar logic