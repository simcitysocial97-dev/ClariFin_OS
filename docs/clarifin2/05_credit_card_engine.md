# Credit Card Intelligence Engine - ClariFinOS 2.0

*Minimize costs and maximize rewards*

---

## Purpose

Treat credit cards as liability instruments requiring active management. Users should optimize payment timing, avoid interest charges, and maximize reward value.

---

## Credit Card Lifecycle

### States
```
ACTIVE → OVERDUE → DELINQUENT → CLOSED
    ↘
     REINSTATED (after overdue)
```

### Billing Cycle
- **Statement Date**: Account snapshot for billing
- **Due Date**: Payment deadline (typically 15-21 days after)
- **Interest-Free Period**: 15-50 days between purchase and due date

---

## Core Concepts

### Outstanding Calculation
```
Outstanding = Σ(uncategorized_spend) + Σ(EMI_conversion) + Σ(fee_charges) - Σ(payments_made)
```

### Available Credit
```
Available = Credit_Limit - Outstanding
Utilization = Outstanding / Credit_Limit × 100
```

### Interest Calculation
```
Daily_Rate = Annual_Rate / 365 / 100
Interest_for_day = Outstanding × Daily_Rate
Monthly_Interest = Σ(daily_interest) for days in billing cycle
```

---

## Payment Optimization

### Optimal Payment Strategy
```
Goal: Minimize interest while maximizing rewards

Strategy:
- Pay full outstanding before due date (avoid interest)
- OR pay minimum if cash flow constrained (avoid penalty)
- OR partial payment if optimizing utilization (for credit score)
```

### Payment Scenarios

#### Scenario 1: Full Payment
- **Payment**: Full outstanding amount
- **Interest**: ₹0
- **Credit Score Impact**: Positive (0% utilization)
- **Rewards**: Maximum (all spends eligible)

#### Scenario 2: Minimum Payment
- **Payment**: Minimum due amount
- **Interest**: Applied to remaining balance
- **Credit Score Impact**: Neutral if <30% utilization
- **Rewards**: All spends eligible (not converted to EMI)

#### Scenario 3: Partial Payment
- **Payment**: Custom amount
- **Interest**: On unpaid portion
- **Credit Score Impact**: Depends on post-payment utilization
- **Rewards**: All spends eligible

---

## Credit Utilization Intelligence

### Utilization Tiers
| Tier | Utilization | Impact |
|------|-------------|--------|
| **Excellent** | 0-10% | Perfect credit score boost |
| **Good** | 10-30% | Neutral to positive |
| **Caution** | 30-50% | Potential negative impact |
| **Risky** | 50-75% | Significant negative impact |
| **Critical** | 75-100% | Credit score danger |

### Optimization Strategy
```
For credit score: Maintain <30% utilization on all cards
For rewards: Maximize spends on high-reward cards
For interest: Minimize revolving balance
```

---

## Reward Points & Cashback

### Reward Categories
```
Category | Rate | Typical Examples
---------|------|-----------------
Groceries | 5% | BigBasket, Grofers
Dining | 4% | Zomato, Swiggy
Travel | 3% | MakeMyTrip, Ola
Fuel | 2% | Petrol pumps
Shopping | 1% | Amazon, Flipkart
Other | 0.5% | Everything else
```

### Cashback Tracking
- **Card-level**: Total cashback earned
- **Merchant-level**: Best cashback merchants
- **Category-level**: Where rewards concentrate

### Annual Summary
```
Total_Point_Value = Σ(Points × Redemption_Rate)
Redemption_Options:
- Statement credit (1 point = ₹0.5)
- Gift cards (1 point = ₹0.75)
- Voucher (1 point = ₹1.0)
```

---

## EMI Conversion

### Criteria
- Merchant EMI option selected
- Amount ≥ threshold (typically ₹2,500)
- Tenure chosen (3, 6, 9, 12, 18, 24 months)

### Interest Component
```
EMI_Interest_Rate = 12-24% p.a. (higher than personal loan)
EMI = P × r × (1+r)^n / ((1+r)^n - 1)
```

### Tracking
- EMI amount separated from regular spending
- Interest calculated separately
- Payment allocated to EMI first

---

## Subscription Detection

### Detection Logic
```
Recurring merchant = Same merchant, same amount, regular interval
Confidence levels:
- WEEKLY: Every 7±1 days
- MONTHLY: Every 30±3 days
- QUARTERLY: Every 90±5 days
- ANNUAL: Every 365±10 days
```

### Flags
- **High-risk subscriptions**: Gambling, gaming, premium apps
- **Unused subscriptions**: No recent activity beyond charge
- **Duplicate subscriptions**: Multiple cards with same service

---

## Credit Health Score

### Formula
```
Health_Score = 0.3 × Utilization_Score + 0.3 × Payment_Score + 0.2 × Reward_Score + 0.2 × Risk_Score

Where:
- Utilization_Score = max(0, (50 - Utilization) / 50) × 100 (if <50%)
- Payment_Score = On-time payment % × 100
- Reward_Score = Points_earned / Points_target × 100
- Risk_Score = 100 - (risk_transactions / total_transactions) × 100
```

---

## Credit Score Impact Modeling

### Factors (based on CIBIL/Experian)
| Factor | Weight | Description |
|--------|--------|-------------|
| Payment History | 35% | On-time payments |
| Credit Utilization | 30% | <30% ideal |
| Credit Age | 15% | Older cards better |
| Credit Mix | 10% | Variety of products |
| New Credit | 10% | Recent inquiries |

### Score Prediction
```
Score_change = Payment_impact + Utilization_impact + Age_impact + Mix_impact

Where each factor computed deterministically based on user data
```

---

## Merchant Analysis

### High-Interest Merchants
- Educational institutions (high fees)
- Medical facilities (no dispute)
- Cash advances (immediate interest)

### Reward Optimization
- Track spending by merchant category
- Recommend payment card by category
- Alert on missed bonus category

---

## Database Schema

### credit_cards table
```sql
CREATE TABLE credit_cards (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    name TEXT NOT NULL,
    bank TEXT NOT NULL,
    card_last4 TEXT,
    credit_limit_paise INTEGER NOT NULL,
    annual_fee_paise INTEGER DEFAULT 0,
    interest_rate_pa REAL,
    billing_day INTEGER,  -- 1-31
    due_day_offset INTEGER DEFAULT 21,  -- days after statement
    reward_type TEXT,  -- POINTS/CASHBACK/MILES
    reward_rate TEXT,  -- JSON with category rates
    is_active INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### credit_card_statements table
```sql
CREATE TABLE credit_card_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL REFERENCES credit_cards(id),
    statement_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    total_outstanding_paise INTEGER NOT NULL,
    minimum_due_paise INTEGER NOT NULL,
    payment_date TEXT,
    payment_amount_paise INTEGER,
    interest_charged_paise INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(card_id, statement_date)
);
```

### credit_card_subscriptions table
```sql
CREATE TABLE credit_card_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL REFERENCES credit_cards(id),
    merchant_pattern TEXT NOT NULL,
    amount_paise INTEGER,
    frequency TEXT CHECK(frequency IN ('weekly','monthly','quarterly','annual')),
    confidence REAL,  -- 0.0-1.0
    first_detected TEXT,
    last_charged TEXT,
    is_active INTEGER DEFAULT 1
);
```

---

## Required APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/credit-cards` | GET | List all cards with utilization |
| `/api/v1/credit-cards` | POST | Add new card |
| `/api/v1/credit-cards/{id}` | GET | Card details |
| `/api/v1/credit-cards/{id}/statements` | GET | Statement history |
| `/api/v1/credit-cards/{id}/utilization` | GET | Utilization timeline |
| `/api/v1/credit-cards/{id}/rewards` | GET | Rewards earned |
| `/api/v1/credit-cards/{id}/optimize-payment` | POST | Payment recommendation |
| `/api/v1/credit-cards/subscriptions` | GET | Detected subscriptions |
| `/api/v1/credit-cards/health` | GET | Credit health score |

---

## Services Required

### CreditCardService
```python
class CreditCardService:
    def calculate_utilization(card_id) -> float
    def get_payment_recommendation(card_id, amount_available) -> dict
    def track_rewards(card_id) -> dict
    def detect_subscriptions(card_id) -> list[CreditCardSubscription]
    def compute_health_score(card_id) -> float
    def project_interest(card_id, days) -> int
```

### RewardOptimizationService
```python
class RewardOptimizationService:
    def get_best_card_for_category(category) -> CreditCard
    def calculate_annual_rewards(user_id) -> dict
    def recommend_category_allocation(user_id) -> list[dict]
```

---

## Testing Strategy

### Unit Tests
- Utilization calculation edge cases
- Interest computation for partial period
- Reward value conversions
- Subscription detection thresholds

### Integration Tests
- Payment optimization scenarios
- Credit score impact modeling
- Multi-card reward aggregation
- Statement generation accuracy

### Acceptance Criteria
- [ ] Utilization calculated daily
- [ ] Payment recommendation accurate
- [ ] Subscriptions detected within 2 cycles
- [ ] Rewards valued correctly
- [ ] Health score reflects real risk