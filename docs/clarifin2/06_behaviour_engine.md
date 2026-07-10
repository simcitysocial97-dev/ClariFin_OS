# Behavioural Intelligence Engine - ClariFinOS 2.0

*Deterministic pattern detection and early warning*

---

## Purpose

The foundation for proactive financial intelligence. All calculations are deterministic statistical models, not machine learning predictions. Users receive early warnings and personalized insights based on observable patterns.

---

## Core Behavioural Metrics

### 1. Savings Discipline Score

**Formula**:
```
Monthly_Savings = Σ(credits) - Σ(essential_debits)
Essential_Categories = ['Rent', 'Groceries', 'Utilities', 'EMI', 'Insurance']

Discipline_Rate = Monthly_Savings / Monthly_Net_Income
Discipline_Score = Discipline_Rate × 100 (capped at 100)

Score_Bands:
- 0-20: Poor (spending exceeds income)
- 20-40: Inconsistent (irregular saving)
- 40-60: Developing (saving when possible)
- 60-80: Good (consistent surplus)
- 80-100: Excellent (systematic saving)
```

### 2. Cashflow Stability Index

**Formula**:
```
Expected_Income = Median of last 6 months income
Actual_Income = Current month income

Income_Variance = |Actual - Expected| / Expected
Stability_Score = max(0, (1 - Income_Variance)) × 100

For expenses:
Expense_Variance = Standard_deviation_of_monthly_expenses / Average_monthly_expense
Expense_Stability_Score = max(0, (1 - Expense_Variance)) × 100

Cashflow_Stability = 0.6 × Income_Stability + 0.4 × Expense_Stability
```

### 3. Salary Dependence Ratio

**Formula**:
```
Primary_Source_Income = Income from primary employer (detected via pattern)
Total_Income = Σ(all income sources)

Dependence_Ratio = Primary_Source_Income / Total_Income × 100

Risk Levels:
- > 80%: High risk (job loss impact)
- 50-80%: Moderate
- 20-50%: Healthy diversification
- < 20%: Very low dependence (multiple income)
```

### 4. Lifestyle Inflation

**Formula**:
```
Non_essential_growth = (Current_non_essential - Previous_non_essential) / Previous_non_essential

Where:
Non_essential = Σ(debits except essential categories)

Inflation_Rate = Non_essential_growth × 100

Threshold: > 10% year-over-year indicates lifestyle inflation
```

### 5. Subscription Burn Rate

**Formula**:
```
Subscription_Spend = Σ(recurring_merchant_charges)
Monthly_Burn = Subscription_Spend / Active_Subscriptions

Burn_Rate_Score = (Subscription_Spend / Net_Income) × 1000

Healthy threshold: Burn_Rate < 50 (i.e., <5% of income)
```

### 6. Financial Resilience Index

**Formula**:
```
Emergency_Buffer_Months = Emergency_Fund_Current / (Monthly_Expenses / 3)
Buffer_Score = min(1, Emergency_Buffer_Months / 6) × 100  # 6 months target

Income_Diversity_Score = Unique_income_sources / 4 × 100  # 4 sources ideal

Asset_Diversity_Score = Unique_asset_types / 5 × 100  # 5 types ideal

Resilience_Index = 0.5 × Buffer_Score + 0.3 × Income_Diversity + 0.2 × Asset_Diversity
```

---

## Pattern Detection Algorithms

### Overspending Detection
```
Category_Overspend = Current_month_category_spend > (3 × Average_last_6_months)

If Category_Overspend:
    Alert: "Unusual spending in {category}: ₹{amount} (3x normal)"
```

### Impulse Purchase Detection
```
Impulse_Pattern:
- Time: 8 PM - 2 AM
- Day: Friday, Saturday, Sunday
- Amount: > ₹500 and < monthly average
- Category: Entertainment, Shopping, Food Delivery

Impulse_Score = Count_impulse_txns / Month_total_txns × 100
```

### Weekend/Night Spending
```
Weekend_Spend = Σ(debits where day_of_week in [sat, sun])
Night_Spend = Σ(debits where hour >= 20)

Pattern_Score = (Weekend_Spend + Night_Spend) / Total_Spend × 100
```

---

## Early Warning System

### Warning Triggers

| Warning | Trigger Condition | Priority |
|---------|-------------------|----------|
| **Low Balance** | Account balance < 2 weeks expenses | HIGH |
| **High Utilization** | Credit card > 75% | MEDIUM |
| **Missed Income** | No income for 5+ days past expected | HIGH |
| **Lifestyle Inflation** | Non-essential > 10% YoY | MEDIUM |
| **Subscription Creep** | New subscription + existing over budget | LOW |
| **Cash Flow Dip** | 3 consecutive days negative net flow | MEDIUM |

### Alert Generation
```
Generate alerts daily at 6 AM (user's timezone)
Aggregate multiple warnings into single notification
Prioritize by severity and financial impact
```

---

## Monthly Comparisons

### Trend Analysis
```
Metric_This_Month vs Metric_Previous_Month
Metric_3_Month_Average vs Metric_This_Month

Trend indicators:
- UP: Current > 1.2 × Previous
- DOWN: Current < 0.8 × Previous
- STABLE: Within 20% of previous
```

### Peer Comparison (Internal Percentiles)
```
User_X_Spending = ₹50,000/month
Percentile vs internal user base = 65%

Meaning: User spends more than 65% of users (lower is better for control)
```

---

## Financial Wellness Score

**Composite Score Formula**:
```
Wellness_Score = 0.20 × Savings_Discipline
              + 0.15 × Cashflow_Stability
              + 0.15 × Resilience_Index
              + 0.15 × Salary_Diversification
              + 0.10 × Lifestyle_Control
              + 0.15 × Account_Health
              + 0.10 × Credit_Health

Where:
- Savings_Discipline (0-100)
- Cashflow_Stability (0-100)
- Resilience_Index (0-100)
- Salary_Diversification = min(100, Unique_sources × 25)
- Lifestyle_Control = 100 - Impulse_Score
- Account_Health = Average of all account health scores
- Credit_Health = Average of all credit card health scores
```

### Score Interpretation
- **90-100**: Financially Fit - Excellent control
- **75-89**: Healthy - Minor improvements needed
- **50-74**: Developing - Focus on consistency
- **25-49**: At Risk - Immediate action needed
- **< 25**: Critical - Major financial stress

---

## Recommendation Engine

### Deterministic Rules

| Condition | Recommendation |
|-----------|----------------|
| Savings_Score < 40 AND Income > Expenses | "Increase savings by reducing discretionary spend" |
| Credit_Utilization > 75% | "Pay credit card before due date to avoid interest" |
| Subscription_Burn > 50 | "Review subscriptions - spending ₹{amount}/month on unknown services" |
| Resilience < 30 | "Build emergency fund - target {months} months of expenses" |
| Lifestyle_Inflation > 10% | "Non-essential spending up {percent}% - consider budget limits" |

---

## Database Schema

### behaviour_snapshots table
```sql
CREATE TABLE behaviour_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    savings_discipline_score REAL,
    cashflow_stability_score REAL,
    salary_dependence_ratio REAL,
    lifestyle_inflation_rate REAL,
    subscription_burn_rate REAL,
    resilience_index REAL,
    wellness_score REAL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(snapshot_date)
);
```

### behaviour_patterns table
```sql
CREATE TABLE behaviour_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL,  -- IMPULSE, SUBSCRIPTION, NIGHT_SPEND, WEEKEND_SPEND
    pattern_key TEXT NOT NULL,   -- merchant or time pattern
    strength REAL,               -- 0.0-1.0 confidence
    first_observed TEXT,
    last_observed TEXT,
    transaction_ids TEXT         -- JSON array of txn IDs
);
```

### recommendations table
```sql
CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_type TEXT NOT NULL,
    priority INTEGER,  -- 1=HIGH, 2=MEDIUM, 3=LOW
    title TEXT NOT NULL,
    description TEXT,
    action_url TEXT,
    is_acknowledged INTEGER DEFAULT 0,
    acknowledged_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

---

## Required Services

### BehaviourService
```python
class BehaviourService:
    def compute_savings_discipline() -> float
    def compute_cashflow_stability() -> float
    def compute_salary_dependence() -> float
    def detect_lifestyle_inflation() -> float
    def compute_subscription_burn_rate() -> float
    def compute_resilience_index() -> float
    def get_wellness_score() -> float
    def generate_recommendations() -> list[dict]
    def detect_patterns() -> list[dict]
```

### PatternDetector
```python
class PatternDetector:
    def detect_impulse_purchases(transactions) -> list[dict]
    def detect_weekend_spending(transactions) -> float
    def detect_night_spending(transactions) -> float
    def detect_recurring_merchants(transactions) -> list[dict]
```

---

## API Contracts

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/behaviour/score` | GET | Current wellness score |
| `/api/v1/behaviour/monthly-trends` | GET | Month-over-month trends |
| `/api/v1/behaviour/patterns` | GET | Detected patterns |
| `/api/v1/behaviour/recommendations` | GET | Current recommendations |
| `/api/v1/behaviour/alerts` | GET | Active warnings |
| `/api/v1/behaviour/subscription-analysis` | GET | Subscription breakdown |

---

## Testing Strategy

### Unit Tests
- Savings discipline calculation (all band edges)
- Cashflow stability with variance
- Salary dependence ratios
- Lifestyle inflation detection
- Impulse pattern thresholds

### Integration Tests
- Monthly trend comparison
- Recommendation generation
- Alert triggering
- Pattern detection accuracy

### Acceptance Criteria
- [ ] Wellness score updates daily
- [ ] Patterns detected within 3 transactions
- [ ] Recommendations actionable
- [ ] Alerts trigger at correct thresholds
- [ ] All metrics deterministic and reproducible