# Dependency Graph - ClariFinOS 2.0

*Feature and data flow dependencies*

---

## Core Data Flow

```
Transactions (Source of Truth)
        │
        ▼
Reconciliation Engine
        │
        ▼
Account/Budget/Behaviour Updates
        │
        ▼
Financial Intelligence Aggregation
        │
        ▼
Dashboard + Recommendations
        │
        ▼
LLM-Assisted Explanations
```

---

## Transaction Layer Dependencies

### Transaction Creation → All Other Layers
```
transactions table
    ↓
All engines depend on:
- Account Engine: Updates balance history
- Reconciliation Engine: Checks for matches
- Loan Engine: Records payments if loan_id set
- Credit Card Engine: Updates utilization if card_id set
- Behaviour Engine: Updates patterns and scores
```

### Transaction Immutability
```
transactions (immutable)
        │
        ▼
computed views (never modify original data)
        │
        ▼
audit trail records (append-only)
```

---

## Feature Dependencies

### Core Features (P0)
```
Bank Sync
    ├── Transaction Import
    ├── Account Update
    └── Automatic Categorization

Budget Module
    ├── Category System
    ├── Transaction Linking
    └── Alert Generation

Goal Tracking
    ├── Net Worth Integration
    ├── Account Linking
    └── Progress Calculation
```

### Engine Dependencies

#### Account Engine
```
Depends On:
- Transaction Repository (reads transactions)
- Institution Metadata (optional)

Feeds:
- Behaviour Engine (for account health)
- Reconciliation Engine (for balance verification)
- Dashboard (for account summaries)
```

#### Reconciliation Engine
```
Depends On:
- Transaction Repository (reads all transactions)
- Account Repository (for account metadata)

Feeds:
- Account Engine (confirmed transfers update balances)
- Loan Engine (EMI payments detected)
- Credit Card Engine (bill payments detected)
- Behaviour Engine (accuracy metrics)
- Dashboard (money flow graph)
```

#### Loan Engine
```
Depends On:
- Transaction Repository (for income/expenses)
- Account Repository (for funding sources)
- Loan Repository (for loan data)

Feeds:
- Behaviour Engine (DTI, liability ratios)
- Dashboard (loan summaries)
- Forecast Engine (payoff projections)
```

#### Credit Card Engine
```
Depends On:
- Transaction Repository (card transactions)
- Account Repository (linked checking account)

Feeds:
- Behaviour Engine (utilization metrics)
- Reconciliation Engine (payment matching)
- Dashboard (credit health)
```

#### Behaviour Engine
```
Depends On:
- Transaction Repository (all spending patterns)
- Account Engine (account health scores)
- Loan Engine (debt ratios)
- Credit Card Engine (credit metrics)

Feeds:
- Recommendation Engine
- Alert System
- Dashboard (wellness score)
- LLM Layer (explanation inputs)
```

---

## API Dependency Map

```
/api/v1/transactions
    ├── GET /transactions/analytics → Dashboard
    ├── GET /transactions/categories → Budget
    └── POST /transactions (import) → All Engines

/api/v1/accounts/{id}/balance
    ├── Account Engine
    └── Reconciliation Engine

/api/v1/reconciliation/scan
    ├── Transaction Repository
    └── Reconciliation Engine

/api/v1/loans/{id}/prepayment-simulation
    ├── Loan Engine
    └── Forecast Engine

/api/v1/credit-cards/{id}/optimize-payment
    ├── Credit Card Engine
    └── Account Engine

/api/v1/behaviour/score
    ├── Behaviour Engine
    └── All other engines (aggregated)
```

---

## Database Relationship Diagram

```
┌─────────────┐         ┌──────────────┐
│ institutions│◄────────│   accounts   │
└─────────────┘  type   └──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────┐   ┌──────────────┐    ┌──────────────┐
│  credit_    │   │   loans      │    │  investments │
│  cards      │   └──────────────┘    └──────────────┘
└──────┬──────┘           │                   │
       │                  ▼                   ▼
       │          ┌──────────────┐   ┌──────────────┐
       │          │ loan_payments│   │  (existing)  │
       │          └──────────────┘   └──────────────┘
       │
       ▼
┌──────────────┐
│credit_card_  │
│statements    │
└──────┬──────┘
       │
       ▼
┌──────────────┐
│credit_card_  │
│subscriptions │
└──────────────┘

┌──────────────┐
│transactions  │◄─ All financial actions
└──────┬──────┘
       │
       ▼
┌──────────────┐
│reconciliations│◄─ Transfer matching
└──────────────┘

┌──────────────┐
│behaviour_    │
│snapshots    │
└──────────────┘

┌──────────────┐
│budgets      │
└──────────────┘

┌──────────────┐
│goals        │
└──────────────┘

┌──────────────┐
│forecasts    │
└──────────────┘
```

---

## Calculation Dependencies

### Health Score Dependencies
```
Account Health Score
├── Transaction Activity
├── Balance Trend
└── Fee Transaction Detection

Loan Health Score
├── EMI Payment History (loan_payments)
├── DTI Ratio (requires income from transactions)
└── Utilization (requires sanction amount)

Credit Health Score
├── Utilization History (credit_card_transactions)
├── Payment History (statements)
└── Risk Transaction Detection

Overall Wellness Score
├── Account Health (average)
├── Loan Health (weighted)
├── Credit Health (weighted)
├── Savings Discipline
├── Cashflow Stability
└── Resilience Index
```

### Reconciliation Coverage
```
Coverage = Matched_Count / Total_Count

Where:
- Matched_Count = Confirmed reconciliations
- Total_Count = Transactions with account_id
- Confidence threshold = 0.7 for auto-match
- Manual matches = user confirmed
```

---

## Forecast Dependencies

### Cashflow Prediction
```
Requires:
- 6+ months of transaction history
- Seasonal decomposition (monthly patterns)
- Category-level forecasts
- Budget adherence data
```

### Net Worth Projection
```
Requires:
- Current net worth (accounts + investments - loans)
- Future cashflow forecast
- Investment growth assumptions
- Loan payoff schedule
```

---

## Testing Dependencies

### Unit Test Requirements
```
Account Engine: Mock transactions, test health score
Loan Engine: Mock loan data, test EMI formulas
Credit Card: Mock utilization, test payment optimization
Reconciliation: Mock transaction pairs, test matching
Behaviour: Mock transaction patterns, test scoring
```

### Integration Test Requirements
```
Full Pipeline:
1. Import transactions
2. Run reconciliation
3. Update account balances
4. Compute health scores
5. Generate alerts
6. Verify all engines updated
```

---

## Migration Dependencies

### Phase 1: Schema Extension
- Transactions: Add columns (nullable)
- Accounts: Add columns
- Loans: Add columns

### Phase 2: New Tables
- Credit cards (no FKs)
- Credit card statements (FK to cards)
- Loan payments (FK to loans)

### Phase 3: Foreign Keys & Constraints
- Enable all FK constraints
- Add NOT NULL where needed
- Add unique constraints

---

## Risk Dependencies

### Single Point of Failure
```
Transaction Repository Down
→ All engines fail
→ No dashboard data
→ No alerts generated

Mitigation:
- Read replicas for queries
- Graceful degradation
- Local cache for recent data
```

### Data Integrity Risk
```
Reconciliation mismatch
→ Account balances wrong
→ Loan calculations wrong
→ Health scores wrong

Mitigation:
- Hash signatures on all critical data
- Reconciliation audit trail
- Monthly reconciliation reports
```

---

## Acceptance Criteria Dependencies

Each feature requires:
1. **Deterministic calculation works**
2. **Test passes for formula**
3. **API returns correct format**
4. **UI displays correctly**
5. **LLM explanation generated (where applicable)**