# Intelligence Engines Audit

## Behaviour Engine

### Health Intelligence

#### Wellness Scoring
**Function**: `compute_wellness_score()`
**Purpose**: Compute composite financial wellness score (0-100) based on multiple behavioral dimensions
**Inputs**:
- `cashflow_stability`: Decimal from `compute_cashflow_stability_index()` (0-1)
- `debt_cycle_score`: Integer from `compute_debt_cycle_score()` (0-100)
- `savings_rate`: Decimal from `compute_true_savings_rate()` (-1 to 1)
- `resilience_index`: Decimal from `compute_resilience_index()` (0-1)
- `lifestyle_inflation`: Decimal from `compute_lifestyle_inflation()` (-1 to ∞)
- `credit_revolver_ratio`: Decimal from `compute_credit_revolver_ratio()` (0-1)
- `foir`: Decimal from `compute_foir()` (0-∞)

**Outputs**:
- Decimal wellness score between 0 and 100

**Formula**:
```
Weighted sum of normalized component scores:
- 30% Cashflow Health: cashflow_stability
- 20% Debt Health: (1 - (debt_cycle_score / 100))
- 15% Savings Behaviour: max(0, savings_rate)
- 20% Resilience: resilience_index
- 10% Lifestyle Control: 1 - min(max(lifestyle_inflation, 0), 1)
- 5% Credit Behaviour: 0.5*(1-revolver_ratio) + 0.5*(1 - min(foir,1))
```

**Evidence**:
- Component scores from various behavior metrics
- Weighted contribution of each dimension

**Confidence**: High (deterministic calculation from validated inputs)

**Dependencies**:
- Cashflow stability calculation
- Debt cycle scoring
- Savings rate calculation
- Resilience index calculation
- Lifestyle inflation calculation
- Credit revolver ratio calculation
- FOIR calculation

**Classification Function**: `classify_wellness_band()`
**Purpose**: Classify wellness score into bands
**Bands**:
- 90-100: "Excellent"
- 75-89: "Healthy"
- 50-74: "Developing"
- 25-49: "Risk"
- <25: "Critical"

---

#### Resilience Metrics
**Function**: `compute_liquidity_months()`
**Purpose**: Compute number of months of essential expenses covered by liquid assets
**Inputs**:
- `liquid_assets_paise`: Total liquid assets (savings accounts, cash) in paise
- `essential_monthly_expenses_paise`: Monthly essential expenses in paise

**Outputs**:
- Integer number of months of coverage

**Formula**: `liquid_assets / essential_monthly_expenses`

**Evidence**:
- Liquid asset amount
- Essential expense amount

**Confidence**: High (deterministic calculation)

**Dependencies**: None

---

**Function**: `compute_resilience_index()`
**Purpose**: Compute composite resilience index (0-1)
**Inputs**:
- `liquid_assets_paise`: Total liquid assets in paise
- `essential_monthly_expenses_paise`: Monthly essential expenses in paise
- `total_income_paise`: Total income for the period in paise
- `monthly_incomes_paise`: List of monthly income values

**Outputs**:
- Decimal resilience score between 0 and 1

**Formula**: `0.6 * min(liquidity_months, 12) / 12 + 0.4 * income_stability`

**Evidence**:
- Liquidity component (capped at 12 months)
- Income stability component

**Confidence**: High (deterministic calculation)

**Dependencies**:
- `compute_liquidity_months()`
- `compute_income_stability()`

---

### Behavior Intelligence

#### Savings Metrics
**Function**: `compute_true_savings_rate()`
**Purpose**: Compute true savings rate as a decimal value
**Inputs**:
- `income_paise`: Total income for the period
- `actual_expenses_paise`: Total expenses excluding transfers
- `financial_fees_paise`: Mandatory financial outflows

**Outputs**:
- Decimal savings rate (can be negative)

**Formula**: `(income - actual_expenses - financial_fees) / income`

**Evidence**:
- Income amount
- Expense amount
- Financial fee amount

**Confidence**: High (deterministic calculation)

**Dependencies**: None

---

**Function**: `compute_borrowed_lifestyle_ratio()`
**Purpose**: Compute ratio of credit-funded expenses to total expenses
**Inputs**:
- `credit_funded_paise`: Total expenses funded by credit
- `total_expenses_paise`: Total expenses for the period

**Outputs**:
- Decimal ratio between 0 and 1+

**Formula**: `credit_funded_expenses / total_expenses`

**Evidence**:
- Credit-funded expense amount
- Total expense amount

**Confidence**: High (deterministic calculation)

**Dependencies**: None

---

**Function**: `compute_monthly_surplus()`
**Purpose**: Compute monthly surplus in paise
**Inputs**:
- `income_paise`: Total income for the period
- `total_expenses_paise`: Total expenses for the period
- `fees_paise`: Optional financial fees

**Outputs**:
- Integer surplus in paise (can be negative)

**Formula**: `income - total_expenses - fees`

**Evidence**:
- Income amount
- Expense amount
- Fee amount

**Confidence**: High (deterministic calculation)

**Dependencies**: None

---

#### Cashflow Stability
**Function**: `compute_income_stability()`
**Purpose**: Compute income stability score (0-1)
**Inputs**:
- `monthly_incomes_paise`: List of monthly income values

**Outputs**:
- Decimal stability score between 0 and 1

**Formula**: `1 - min(1, coefficient_of_variation)`

**Evidence**:
- Monthly income values
- Variance and mean of income

**Confidence**: Medium (depends on data quality and sample size)

**Dependencies**:
- `_coefficient_of_variation()` utility function

---

**Function**: `compute_expense_stability()`
**Purpose**: Compute expense stability score (0-1)
**Inputs**:
- `monthly_expenses_paise`: List of monthly expense values

**Outputs**:
- Decimal stability score between 0 and 1

**Formula**: `1 - min(1, coefficient_of_variation)`

**Evidence**:
- Monthly expense values
- Variance and mean of expenses

**Confidence**: Medium (depends on data quality and sample size)

**Dependencies**:
- `_coefficient_of_variation()` utility function

---

**Function**: `compute_cashflow_stability_index()`
**Purpose**: Compute overall cashflow stability index (0-1)
**Inputs**:
- `monthly_incomes_paise`: List of monthly income values
- `monthly_expenses_paise`: List of monthly expense values

**Outputs**:
- Decimal stability index between 0 and 1

**Formula**: `(income_stability + expense_stability) / 2`

**Evidence**:
- Income stability score
- Expense stability score

**Confidence**: Medium (composite of two stability scores)

**Dependencies**:
- `compute_income_stability()`
- `compute_expense_stability()`

---

#### Income Intelligence
**Function**: `classify_income_source()`
**Purpose**: Classify income transaction source based on description keywords
**Inputs**:
- `transaction`: Dict with 'description' key

**Outputs**:
- Tuple of (category: str, confidence: float)

**Categories**:
- "salary": Employment income
- "business": Business/freelance income
- "investment": Investment returns
- "transfer": Internal transfers
- "refund": Refunds/cashbacks
- "borrowing": Loans/advances
- "unknown": No matching keywords

**Confidence**:
- 1.0: Exact whole-word match
- 0.8: Partial word match

**Evidence**:
- Transaction description
- Keyword matching

**Confidence**: Medium (depends on description quality)

**Dependencies**: None

---

**Function**: `compute_salary_dependence_ratio()`
**Purpose**: Compute ratio of salary income to true income
**Inputs**:
- `salary_income_paise`: Total salary income in paise
- `true_income_paise`: Total true income in paise

**Outputs**:
- Decimal ratio between 0 and 1+

**Formula**: `salary_income / true_income`

**Evidence**:
- Salary income amount
- True income amount

**Confidence**: High (deterministic calculation)

**Dependencies**: None

---

**Function**: `compute_income_diversification_score()`
**Purpose**: Compute income diversification score (0-1)
**Inputs**:
- `income_transactions`: List of income transaction dicts

**Outputs**:
- Decimal score between 0 and 1

**Formula**: `min(unique_sources / 3, 1.0)`

**Evidence**:
- Unique true income sources (salary, business, investment)
- Count of unique sources

**Confidence**: Medium (depends on transaction classification)

**Dependencies**:
- `classify_income_source()`
- `filter_true_income()`

---

### Risk Intelligence

#### Debt Intelligence
**Function**: `compute_credit_dependency_ratio()`
**Purpose**: Compute ratio of credit-funded expenses to total expenses
**Inputs**:
- `credit_funded_expenses_paise`: Total expenses funded by credit
- `total_expenses_paise`: Total expenses for the period

**Outputs**:
- Decimal ratio between 0 and 1+

**Formula**: `credit_funded_expenses / total_expenses`

**Evidence**:
- Credit-funded expense amount
- Total expense amount

**Confidence**: High (deterministic calculation)

**Dependencies**: `compute_borrowed_lifestyle_ratio()` (semantically equivalent)

---

**Function**: `compute_debt_cycle_score()`
**Purpose**: Compute debt cycle score (0-100) based on credit behavior indicators
**Inputs**:
- `credit_advances_count`: Number of credit advances in last 6 months
- `revolving_months`: Number of months with revolving credit usage
- `debt_increase_trend`: Decimal trend value from -1 to 1

**Outputs**:
- Integer score from 0 to 100

**Formula**: `0.3 * advance_score + 0.3 * revolve_score + 0.4 * trend_score`

**Scoring Bands**:
- Credit advances (last 6 months):
  - 0 advances → 0
  - 1 advance → 10
  - 2-3 advances → 30
  - 4-5 advances → 60
  - >=6 advances → 90
- Revolving months (out of last 6):
  - 0 months → 0
  - 1-2 months → 20
  - 3-4 months → 50
  - 5-6 months → 80
- Debt increase trend (-1 to 1):
  - Negative → 0
  - 0 to 0.1 → 5
  - 0.1 to 0.3 → 20
  - 0.3 to 0.6 → 50
  - 0.6+ → 80

**Evidence**:
- Credit advance count
- Revolving month count
- Debt trend

**Confidence**: Medium (heuristic scoring)

**Dependencies**: None

---

**Function**: `compute_foir()`
**Purpose**: Compute Fixed Obligation to Income Ratio (FOIR)
**Inputs**:
- `loan_emi_paise`: Total monthly loan EMI obligations in paise
- `credit_card_min_due_paise`: Total minimum credit card dues in paise
- `monthly_income_paise`: Monthly income in paise

**Outputs**:
- Tuple of (Decimal ratio, band string)

**Formula**: `(loan_emi + minimum_credit_due) / monthly_income`

**Bands**:
- <30% → "HEALTHY"
- 30-50% → "MODERATE"
- 50-60% → "WARNING"
- >=60% → "CRITICAL"

**Evidence**:
- Loan EMI amount
- Credit card minimum due
- Monthly income

**Confidence**: High (deterministic calculation)

**Dependencies**: None

---

**Function**: `compute_credit_revolver_ratio()`
**Purpose**: Compute credit revolver ratio
**Inputs**:
- `months_partial_payment`: Number of months with partial credit payments
- `active_credit_months`: Number of months with active credit card usage

**Outputs**:
- Decimal ratio between 0 and 1

**Formula**: `months_partial_payment / active_credit_months`

**Evidence**:
- Partial payment months
- Active credit months

**Confidence**: High (deterministic calculation)

**Dependencies**: None

---

## Credit Card Engine

### Metrics Intelligence
**Function**: `compute_utilization()`
**Purpose**: Compute credit utilization as basis points
**Inputs**:
- `outstanding_paise`: Current outstanding balance in paise
- `credit_limit_paise`: Total credit limit in paise

**Outputs**:
- Utilization in basis points (e.g., 2500 = 25%)

**Formula**: `(outstanding / credit_limit) × 10000`

**Evidence**:
- Outstanding balance
- Credit limit

**Confidence**: High (deterministic calculation)

**Dependencies**: None

---

**Function**: `compute_available_credit()`
**Purpose**: Compute available credit
**Inputs**:
- `credit_limit_paise`: Total credit limit in paise
- `outstanding_paise`: Current outstanding balance in paise

**Outputs**:
- Available credit in paise (non-negative)

**Formula**: `max(0, credit_limit - outstanding)`

**Evidence**:
- Credit limit
- Outstanding balance

**Confidence**: High (deterministic calculation)

**Dependencies**: None

---

**Function**: `compute_financial_metrics()`
**Purpose**: Compute core financial metrics for a credit card
**Inputs**:
- `outstanding_paise`: Current outstanding balance in paise
- `credit_limit_paise`: Total credit limit in paise
- `annual_rate_bps`: Annual interest rate in basis points
- `total_interest_paid_paise`: Total interest paid to date (optional)

**Outputs**:
- Dict with:
  - `utilization_bps`: Credit utilization in basis points
  - `available_credit_paise`: Available credit in paise
  - `annual_rate_bps`: Effective annual rate (pass-through)
  - `total_interest_paid_paise`: Total interest paid (pass-through)

**Evidence**:
- Outstanding balance
- Credit limit
- Interest rate
- Interest paid

**Confidence**: High (deterministic calculation)

**Dependencies**:
- `compute_utilization()`
- `compute_available_credit()`

---

### Interest Intelligence
**Function**: `compute_daily_interest()`
**Purpose**: Compute interest accrued for one day
**Inputs**:
- `outstanding_paise`: Outstanding balance for the day in paise
- `annual_rate_bps`: Annual interest rate in basis points

**Outputs**:
- Daily interest in paise

**Formula**: `outstanding × daily_rate`

**Evidence**:
- Outstanding balance
- Daily interest rate

**Confidence**: High (deterministic calculation)

**Dependencies**:
- `bps_to_daily_rate()`

---

**Function**: `compute_monthly_interest_charge()`
**Purpose**: Compute total interest charge for a billing cycle
**Inputs**:
- `daily_balances`: List of (date_string, balance_paise) for each day
- `annual_rate_bps`: Annual interest rate in basis points

**Outputs**:
- Total interest charge in paise

**Formula**: `sum(compute_daily_interest(balance, annual_rate_bps) for each day)`

**Evidence**:
- Daily balances
- Interest rate

**Confidence**: High (deterministic calculation)

**Dependencies**:
- `compute_daily_interest()`

---

### Billing Intelligence
**Function**: `compute_due_date()`
**Purpose**: Compute payment due date
**Inputs**:
- `statement_date`: The statement date (date object)
- `due_day_offset`: Number of days after statement date

**Outputs**:
- Due date as a date object

**Evidence**:
- Statement date
- Due day offset

**Confidence**: High (deterministic calculation)

**Dependencies**: None

---

**Function**: `compute_next_statement_date()`
**Purpose**: Determine next statement date
**Inputs**:
- `billing_day`: Day of month for statement generation (1-31)
- `reference_date`: Current date
- `last_statement_date`: Previous statement date (optional)

**Outputs**:
- Next statement date as a date object

**Evidence**:
- Billing day
- Reference date
- Last statement date

**Confidence**: High (deterministic calculation)

**Dependencies**:
- `_add_months()` from loan engine

---

**Function**: `compute_minimum_due()`
**Purpose**: Compute minimum payment due
**Inputs**:
- `total_outstanding_paise`: Total outstanding balance in paise
- `min_due_pct_bps`: Minimum due percentage in basis points (default 500 = 5%)
- `floor_paise`: Minimum absolute floor in paise (default 10000 = ₹100)

**Outputs**:
- Minimum due amount in paise

**Formula**: `max(floor, total_outstanding * min_due_pct / 10000)`

**Evidence**:
- Outstanding balance
- Minimum due percentage
- Floor amount

**Confidence**: High (deterministic calculation)

**Dependencies**: None

---

### EMI Intelligence
**Function**: `compute_emi_conversion()`
**Purpose**: Compute EMI for a credit card conversion
**Inputs**:
- `amount_paise`: Amount being converted to EMI in paise
- `annual_rate_bps`: Annual interest rate in basis points
- `tenure_months`: EMI tenure in months

**Outputs**:
- Dict with:
  - `emi_paise`: Monthly EMI amount
  - `total_interest_paise`: Total interest over tenure
  - `total_repayment_paise`: Total amount to repay
  - `monthly_interest_paise`: Interest component of first EMI

**Evidence**:
- Conversion amount
- Interest rate
- Tenure

**Confidence**: High (deterministic calculation)

**Dependencies**:
- `compute_emi_fixed()` from loan engine
- `compute_monthly_interest()` from loan engine

---

## Loan Engine

### Amortization Intelligence
**Function**: `generate_schedule()`
**Purpose**: Generate full amortization schedule
**Inputs**:
- `principal_paise`: Loan principal in paise
- `annual_rate_bps`: Annual interest rate in basis points
- `tenure_months`: Tenure in months
- `start_date`: Start date as ISO string
- `emi_paise`: Optional EMI amount

**Outputs**:
- List of `AmortizationRow` objects

**Evidence**:
- Principal amount
- Interest rate
- Tenure
- Start date

**Confidence**: High (deterministic calculation)

**Dependencies**:
- `compute_emi_fixed()`
- `compute_principal_component()`
- `_add_months()`

---

**Function**: `validate_schedule()`
**Purpose**: Validate amortization schedule invariants
**Invariants Checked**:
1. Balance never negative
2. Principal paid never exceeds original principal
3. Final balance reaches zero
4. Sum(principal payments) == principal amount
5. EMI consistency maintained
6. Cumulative interest is monotonic non-decreasing
7. Month numbers are sequential

**Evidence**:
- Schedule data
- Original principal
- Original tenure

**Confidence**: High (deterministic validation)

**Dependencies**: None

---

### EMI Intelligence
**Function**: `compute_emi_fixed()`
**Purpose**: Compute EMI for fixed-rate loan
**Inputs**:
- `principal_paise`: Principal in paise
- `annual_rate_bps`: Annual interest rate in basis points
- `tenure_months`: Tenure in months

**Outputs**:
- EMI in paise

**Formula**: `P × r × (1+r)^n / ((1+r)^n - 1)`

**Evidence**:
- Principal amount
- Interest rate
- Tenure

**Confidence**: High (deterministic calculation)

**Dependencies**:
- `bps_to_monthly_rate()`

---

**Function**: `compute_monthly_interest()`
**Purpose**: Compute interest component for one month
**Inputs**:
- `outstanding_paise`: Outstanding balance in paise
- `annual_rate_bps`: Annual interest rate in basis points

**Outputs**:
- Interest in paise

**Formula**: `Outstanding × Monthly_Rate`

**Evidence**:
- Outstanding balance
- Monthly interest rate

**Confidence**: High (deterministic calculation)

**Dependencies**:
- `bps_to_monthly_rate()`

---

### Prepayment Intelligence
**Function**: `apply_prepayment()`
**Purpose**: Simulate impact of a prepayment
**Inputs**:
- `outstanding_paise`: Current loan outstanding in paise
- `annual_rate_bps`: Annual interest rate in basis points
- `remaining_months`: Months left on loan
- `prepayment_paise`: Prepayment amount in paise
- `mode`: "reduce_tenure" or "reduce_emi"
- `start_date`: Optional ISO date string
- `prepayment_penalty_bps`: Optional prepayment penalty in basis points
- `existing_schedule`: Optional pre-generated schedule

**Outputs**:
- `PrepaymentResult` with comparison of before/after scenarios

**Evidence**:
- Prepayment amount
- Prepayment mode
- Original schedule
- New schedule

**Confidence**: High (deterministic calculation)

**Dependencies**:
- `apply_prepayment_at_month()`
- `generate_schedule()`

---

**Function**: `apply_prepayment_at_month()`
**Purpose**: Apply prepayment at a specific month
**Inputs**:
- `schedule`: Amortization schedule
- `prepayment_month`: Month to apply prepayment
- `prepayment_paise`: Prepayment amount in paise
- `annual_rate_bps`: Annual interest rate in basis points
- `prepayment_penalty_bps`: Optional prepayment penalty in basis points
- `mode`: "reduce_tenure" or "reduce_emi"
- `start_date`: Optional ISO date string

**Outputs**:
- Tuple of (new_schedule, `PrepaymentResult`)

**Evidence**:
- Prepayment month
- Prepayment amount
- Original schedule
- New schedule

**Confidence**: High (deterministic calculation)

**Dependencies**:
- `regenerate_schedule()`

---

### Floating Rate Intelligence
**Function**: `apply_floating_rate_change()`
**Purpose**: Apply floating rate change to a schedule
**Inputs**:
- `schedule`: Amortization schedule
- `change_month`: Month to apply rate change
- `new_rate_bps`: New annual interest rate in basis points
- `mode`: "adjust_emi" or "adjust_tenure"
- `start_date`: Optional ISO date string

**Outputs**:
- New amortization schedule

**Evidence**:
- Change month
- New interest rate
- Change mode
- Original schedule

**Confidence**: High (deterministic calculation)

**Dependencies**:
- `regenerate_schedule()`

---

### Foreclosure Intelligence
**Function**: `compute_foreclosure_amount()`
**Purpose**: Calculate foreclosure amount
**Inputs**:
- `outstanding_paise`: Current outstanding principal in paise
- `annual_rate_bps`: Annual interest rate in basis points
- `remaining_months`: Remaining tenure in months
- `months_paid`: Months already paid
- `prepayment_penalty_bps`: Prepayment penalty rate in basis points

**Outputs**:
- `ForeclosureResult` with breakdown of costs

**Evidence**:
- Outstanding balance
- Interest rate
- Remaining months
- Penalty rate

**Confidence**: High (deterministic calculation)

**Dependencies**:
- `generate_schedule()`
- `total_interest_paise()`

---

### Metrics Intelligence
**Function**: `calculate_interest_saved()`
**Purpose**: Calculate interest saved from prepayment
**Inputs**:
- `original_schedule`: Original amortization schedule
- `new_schedule`: New amortization schedule after prepayment

**Outputs**:
- Interest saved in paise

**Evidence**:
- Original schedule
- New schedule

**Confidence**: High (deterministic calculation)

**Dependencies**:
- `total_interest_paise()`

---

**Function**: `calculate_tenure_saved()`
**Purpose**: Calculate tenure saved from prepayment
**Inputs**:
- `original_schedule`: Original amortization schedule
- `new_schedule`: New amortization schedule after prepayment

**Outputs**:
- Tenure saved in months

**Evidence**:
- Original schedule
- New schedule

**Confidence**: High (deterministic calculation)

**Dependencies**: None

---

## Recommendation Engine

### Debt Intelligence
**Function**: `check_debt_dependency()`
**Purpose**: Generate recommendation if debt dependency ratio exceeds 20%
**Inputs**:
- `borrowed_lifestyle_ratio`: Ratio of credit-funded expenses to total expenses (0-1+)

**Outputs**:
- `Recommendation` if ratio > 0.20, None otherwise

**Threshold**: 20% (0.20)

**Recommendation**:
- Title: "Lifestyle Debt Alert"
- Reason: "Your lifestyle is partly funded by borrowed money"
- Severity: "HIGH"
- Suggested Action: "Create a debt repayment plan and reduce credit-funded spending to build financial stability"

**Evidence**:
- Debt dependency ratio
- Percentage of credit-funded expenses

**Confidence**: High (deterministic threshold check)

**Dependencies**: None

---

### FOIR Intelligence
**Function**: `check_foir()`
**Purpose**: Generate recommendation if FOIR exceeds 50%
**Inputs**:
- `foir_ratio`: Fixed Obligation to Income Ratio (0-1+)

**Outputs**:
- `Recommendation` if ratio > 0.50, None otherwise

**Threshold**: 50% (0.50)

**Recommendation**:
- Title: "High Fixed Obligations"
- Reason: "Fixed obligations are high"
- Severity: "CRITICAL" if ratio >= 0.6, "HIGH" otherwise
- Suggested Action: "Review and renegotiate loan terms, consider prepayment options to reduce monthly obligations"

**Evidence**:
- FOIR ratio
- Percentage of income going to fixed obligations

**Confidence**: High (deterministic threshold check)

**Dependencies**: None

---

### Liquidity Intelligence
**Function**: `check_liquidity()`
**Purpose**: Generate recommendation if liquidity months is below 3
**Inputs**:
- `liquidity_months`: Number of months of essential expenses covered

**Outputs**:
- `Recommendation` if months < 3, None otherwise

**Threshold**: 3 months

**Recommendation**:
- Title: "Emergency Fund Needed"
- Reason: "Emergency fund required"
- Severity: "HIGH" if months < 1, "MEDIUM" otherwise
- Suggested Action: "Build an emergency fund covering 3-6 months of essential expenses before taking on new debt"

**Evidence**:
- Liquidity months
- Months of expense coverage

**Confidence**: High (deterministic threshold check)

**Dependencies**: None

---

### Subscription Intelligence
**Function**: `detect_subscription_growth()`
**Purpose**: Detect subscription growth between periods
**Inputs**:
- `current_subscriptions`: List of current subscription patterns
- `previous_subscriptions`: Optional list of previous subscription patterns

**Outputs**:
- `Recommendation` if subscription growth detected, None otherwise

**Thresholds**:
- 3+ subscriptions without historical context
- 2+ new subscriptions
- 25%+ growth in subscription spending

**Recommendation**:
- Title: "Review Subscriptions"
- Reason: Varies by detection type
- Severity: "MEDIUM" or "LOW"
- Suggested Action: Varies by detection type

**Evidence**:
- Current subscription count
- Previous subscription count
- Subscription spending growth

**Confidence**: Medium (heuristic detection)

**Dependencies**: None

---

**Function**: `compute_recommendations()`
**Purpose**: Compute all recommendations based on financial behaviour metrics
**Inputs**:
- `borrowed_lifestyle_ratio`: Ratio of credit-funded expenses
- `foir`: Fixed Obligation to Income Ratio
- `liquidity_months`: Number of months of essential expenses covered
- `current_subscriptions`: Current subscription patterns
- `previous_subscriptions`: Optional previous subscription patterns

**Outputs**:
- List of triggered recommendations sorted by severity

**Evidence**:
- All input metrics
- Triggered recommendations

**Confidence**: High (deterministic rule application)

**Dependencies**:
- `check_debt_dependency()`
- `check_foir()`
- `check_liquidity()`
- `detect_subscription_growth()`

---