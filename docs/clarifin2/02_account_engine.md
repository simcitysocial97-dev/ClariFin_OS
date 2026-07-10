# Account Intelligence Engine - ClariFinOS 2.0

*Complete account lifecycle and intelligence*

---

## Purpose

Transform raw bank accounts into actionable financial intelligence. Users should understand how each account contributes to their overall financial health and optimize accordingly.

---

## Account Types Architecture

| Type | Description | Intelligence |
|------|-------------|------------|
| **Salary** | Primary income account | Income patterns, salary volatility |
| **Savings** | General savings | Interest earned, dormancy risk |
| **Current/Checking** | Daily transactions | Cash flow rate, overdraft risk |
| **Credit Card** | Revolving credit | Utilization, payment optimization |
| **Loan Account** | Borrowed funds | Outstanding, EMI tracking |
| **Wallet** | Digital wallets (PhonePe, Paytm) | UPI patterns, micro-spend |
| **Fixed Deposit** | Term deposits | Maturity tracking, premature withdrawal cost |
| **Recurring Deposit** | SIP-style deposits | Discipline score, target achievement |
| **Demat/Trading** | Investment accounts | Gains/losses, turnover |
| **UPI** | Virtual payment address | Transaction volume, merchant patterns |

---

## Account Lifecycle

### States
```
ACTIVE → DORMANT → CLOSED
    ↘     ↗
   REACTIVATED
```

### Transitions
- **Dormant Detection**: No transactions for 12+ months
- **Reactivation**: Any transaction after dormant
- **Closed**: Manual or automatic (zero balance + dormant > 24 months)

### Triggers
- Monthly balance snapshots
- Quarterly health score recalculation
- Annual fee optimization

---

## Institution Metadata

Each account links to institution record:

| Field | Type | Purpose |
|-------|------|---------|
| `institution_id` | TEXT | Unique identifier |
| `name` | TEXT | Bank/wallet name |
| `type` | TEXT | BANK/WALLET/BROKER |
| `interest_rate_pa` | REAL | Savings interest rate |
| `fd_rates` | JSON | Slab rates for fixed deposits |
| `features` | JSON | Supported: UPI, IMPS, NEFT, RTGS |
| `last_api_sync` | TEXT | For future bank sync |
| `sync_status` | TEXT | SUCCESS/PENDING/ERROR |

---

## Account Health Score

### Formula
```
Health Score = 0.3 * Activity + 0.3 * Balance + 0.2 * Fees + 0.2 * Relationship
```

### Components

#### 1. Activity Score (0-100)
- Transaction frequency (expected: 5+/month)
- Days since last activity
- Seasonal patterns

#### 2. Balance Score (0-100)
- Minimum balance maintenance
- Growth trend (30-day comparison)
- Absolute thresholds (tiered scoring)

#### 3. Fees Score (0-100)
- Avoided penalty fees
- ATM fee count
- Account maintenance fee optimization

#### 4. Relationship Score (0-100)
- Number of linked accounts
- Primary vs secondary designation
- Product bundling benefits

---

## Balance History & Trends

### Database Schema
```sql
CREATE TABLE account_balances_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    balance_paise INTEGER NOT NULL,
    date_iso TEXT NOT NULL,
    source TEXT CHECK(source IN ('actual', 'projected', 'adjusted')),
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(account_id, date_iso)
);
```

### Trend Analysis
- **Direction**: Improving, Stable, Deteriorating
- **Velocity**: Rate of change (paise/day)
- **Seasonality**: Month-over-month patterns
- **Forecast**: Statistical projection

---

## Cash Flow Per Account

### Calculation
```
Net Flow = Σ(credits) - Σ(debits) for period
Flow Rate = Net Flow / days_in_period
Velocity = Balance change / average_balance
```

### Metrics
- Daily average flow
- Weekly patterns
- Monthly consistency
- Anomaly detection (2σ threshold)

---

## Cross-Account Analytics

### Money Flow Graph
```
Account A → Account B (Transfer)
Account A → Merchant X (Spending)
Account B → Account A (Transfer)
```

#### Key Queries
- Which accounts fund which others?
- Where is spending concentrated?
- What's the income allocation pattern?
- How do transfers flow through the ecosystem?

### Account Relationships
- **Primary Account**: Salary or main checking
- **Backup Account**: Secondary funding source
- **Goal Account**: Dedicated savings
- **Credit Account**: Linked to specific purpose

---

## Required APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/accounts` | GET | List all accounts with health scores |
| `/api/v1/accounts` | POST | Create new account |
| `/api/v1/accounts/{id}` | GET | Single account details |
| `/api/v1/accounts/{id}` | PUT | Update account metadata |
| `/api/v1/accounts/{id}` | DELETE | Close account (soft) |
| `/api/v1/accounts/{id}/balance-history` | GET | Historical balances |
| `/api/v1/accounts/{id}/cash-flow` | GET | Flow analysis |
| `/api/v1/accounts/{id}/health` | GET | Detailed health breakdown |

---

## Required Services

### AccountService
```python
class AccountService:
    def get_account_health(account_id) -> dict
    def calculate_balance_trend(account_id) -> dict
    def get_cash_flow_rate(account_id, days=30) -> int  # paise/day
    def detect_dormant_status(account_id) -> bool
    def link_accounts(primary_id, linked_id) -> None
    def unlink_accounts(account_id) -> None
```

### AccountHealthService
```python
class AccountHealthService:
    def compute_activity_score(account_id) -> float
    def compute_balance_score(account_id) -> float
    def compute_fee_score(account_id) -> float
    def compute_relationship_score(account_id) -> float
    def get_health_breakdown(account_id) -> dict
```

---

## Required Repositories

### AccountRepository (extend existing)
```python
class AccountRepository(BaseRepository):
    def get_balance_history(self, account_id: str, limit: int = 90) -> list[dict]
    def insert_balance_snapshot(self, account_id: str, balance_paise: int, date_iso: str) -> int
    def get_account_health(self, account_id: str) -> dict
    def get_linked_accounts(self, account_id: str) -> list[str]
    def link_accounts(self, primary_id: str, linked_id: str) -> None
```

---

## Analytics Requirements

### 1. Dormant Account Detection
- Criteria: 12 months with ≤2 transactions
- Alert: 11 months before dormancy

### 2. Interest Optimization
- Compare savings rates across accounts
- Suggest optimal fund allocation

### 3. Fee Minimization
- Track avoided fees
- Recommend account changes

---

## UI Data Contracts

### AccountCard Component
```typescript
interface AccountCardData {
  id: string;
  name: string;
  bank: string;
  type: 'salary' | 'savings' | 'checking' | 'credit_card';
  balance_paise: number;
  health_score: number;  // 0-100
  trend: 'up' | 'down' | 'stable';
  flow_paise_per_day: number;
  last_activity: string;  // ISO date
}
```

### AccountHealthPanel Component
```typescript
interface AccountHealthData {
  score: number;
  components: {
    activity: { score: number; weight: 0.3 };
    balance: { score: number; weight: 0.3 };
    fees: { score: number; weight: 0.2 };
    relationship: { score: number; weight: 0.2 };
  };
  recommendations: string[];
  risk_flags: string[];
}
```

---

## Test Strategy

### Unit Tests
- Health score calculations (all edge cases)
- Dormant detection thresholds
- Balance trend algorithms
- Cash flow velocity math

### Integration Tests
- Account creation with institution metadata
- Balance history insertion/query
- Link/unlink operations
- Health score after transaction import

### Acceptance Criteria
- [ ] All account types distinguished
- [ ] Health score updates daily
- [ ] Balance history keeps 365 days
- [ ] Dormant detection accurate to month
- [ ] Linked account flow tracked