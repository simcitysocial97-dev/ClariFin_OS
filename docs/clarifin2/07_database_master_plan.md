# Database Master Plan - ClariFinOS 2.0

*Complete schema evolution for all five engines*

---

## Current Schema Analysis

The existing schema in `backend/src/db.py` provides a solid foundation but requires extensions for ClariFinOS 2.0.

### Current Tables (Sufficient)
- `statements` - Bank statement metadata (no changes needed)
- `transactions` - Core transaction table with `hash_signature`, `amount_paise` (extend)
- `reconciliations` - Matching metadata (extend)

### Current Tables (Need Extension)
- `accounts` - Missing types, health scores, institution metadata
- `loans` - Missing floating rate, payment history, prepayment schedules
- `investments` - Missing dividend history, sector classification

### Missing Tables
- `credit_cards` - Dedicated credit card management
- `credit_card_statements` - Billing cycle tracking
- `credit_card_subscriptions` - Recurring merchant tracking
- `behaviour_snapshots` - Historical behavior scores
- `behaviour_patterns` - Detected patterns storage
- `recommendations` - User recommendations
- `account_balances_history` - Balance trends
- `loan_payments` - Payment history
- `loan_scenarios` - What-if simulations
- `budgets` - Budget module
- `goals` - Goal tracking
- `forecasts` - Prediction storage
- `institutions` - Bank/wallet metadata

---

## Required Schema Changes

### Extend transactions table
```sql
ALTER TABLE transactions ADD COLUMN is_reconciled INTEGER DEFAULT 0;
ALTER TABLE transactions ADD COLUMN reconciliation_group TEXT;
ALTER TABLE transactions ADD COLUMN merchant_canonical TEXT;
ALTER TABLE transactions ADD COLUMN recurring_id INTEGER;
```

### Extend accounts table
```sql
ALTER TABLE accounts ADD COLUMN account_type TEXT DEFAULT 'savings';  -- salary/savings/checking/credit/wallet/fixed_deposit
ALTER TABLE accounts ADD COLUMN institution_id TEXT;
ALTER TABLE accounts ADD COLUMN interest_rate_pa REAL;
ALTER TABLE accounts ADD COLUMN credit_limit_paise INTEGER;
ALTER TABLE accounts ADD COLUMN billing_day INTEGER;
ALTER TABLE accounts ADD COLUMN health_score REAL;
ALTER TABLE accounts ADD COLUMN last_scored_at TEXT;
```

### Extend loans table
```sql
ALTER TABLE loans ADD COLUMN interest_type TEXT DEFAULT 'fixed';  -- fixed/floating/hybrid
ALTER TABLE loans ADD COLUMN floating_baselined_rate REAL;
ALTER TABLE loans ADD COLUMN last_rate_reset_date TEXT;
ALTER TABLE loans ADD COLUMN prepayment_mode TEXT DEFAULT 'reduce_tenure';
ALTER TABLE loans ADD COLUMN health_score REAL;
ALTER TABLE loans ADD COLUMN next_emi_date TEXT;
ALTER TABLE loans ADD COLUMN payment_history_json TEXT;
```

---

## New Tables Required

### institutions
```sql
CREATE TABLE institutions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('BANK', 'WALLET', 'BROKER', 'NBFC')),
    support_transfer_types TEXT,  -- JSON: ["UPI", "NEFT", "RTGS", "IMPS"]
    interest_rate_savings REAL,
    interest_rate_fd_json TEXT,  -- JSON slab rates
    api_available INTEGER DEFAULT 0,
    api_type TEXT,  -- PLAID/FINBOX/YODLEE/NONE
    created_at TEXT DEFAULT (datetime('now'))
);
```

### account_balances_history
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

### credit_cards
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
    billing_day INTEGER,
    due_day_offset INTEGER DEFAULT 21,
    reward_type TEXT,
    reward_rate_json TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### credit_card_statements
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

### credit_card_subscriptions
```sql
CREATE TABLE credit_card_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL REFERENCES credit_cards(id),
    merchant_pattern TEXT NOT NULL,
    amount_paise INTEGER,
    frequency TEXT CHECK(frequency IN ('weekly','monthly','quarterly','annual')),
    confidence REAL,
    first_detected TEXT,
    last_charged TEXT,
    is_active INTEGER DEFAULT 1
);
```

### loan_payments
```sql
CREATE TABLE loan_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id TEXT NOT NULL REFERENCES loans(id),
    payment_date TEXT NOT NULL,
    amount_paise INTEGER NOT NULL,
    principal_paise INTEGER NOT NULL,
    interest_paise INTEGER NOT NULL,
    late_fee_paise INTEGER DEFAULT 0,
    source_account_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(loan_id, payment_date)
);
```

### loan_scenarios
```sql
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

### behaviour_snapshots
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

### behaviour_patterns
```sql
CREATE TABLE behaviour_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL,
    pattern_key TEXT NOT NULL,
    strength REAL,
    first_observed TEXT,
    last_observed TEXT,
    transaction_ids_json TEXT
);
```

### recommendations
```sql
CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_type TEXT NOT NULL,
    priority INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    action_url TEXT,
    is_acknowledged INTEGER DEFAULT 0,
    acknowledged_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

### budgets
```sql
CREATE TABLE budgets (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    amount_paise INTEGER NOT NULL,
    period TEXT CHECK(period IN ('monthly', 'weekly', 'yearly')) DEFAULT 'monthly',
    start_date TEXT,
    end_date TEXT,
    rollover_enabled INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
```

### goals
```sql
CREATE TABLE goals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    target_amount_paise INTEGER NOT NULL,
    current_amount_paise INTEGER NOT NULL DEFAULT 0,
    target_date TEXT,
    linked_account_id TEXT,
    linked_investment_id TEXT,
    priority INTEGER,
    is_completed INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
```

### forecasts
```sql
CREATE TABLE forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    forecast_date TEXT NOT NULL,
    forecast_type TEXT CHECK(forecast_type IN ('cashflow', 'net_worth', 'expense')),
    account_id TEXT,
    amount_paise INTEGER NOT NULL,
    confidence REAL,
    methodology TEXT,  -- ARIMA/EXPONENTIAL_SMOOTHING
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(forecast_date, forecast_type, account_id)
);
```

---

## Relationships & Constraints

### Foreign Keys
- `transactions.account_id` → `accounts.id`
- `transactions.loan_id` → `loans.id` (optional)
- `transactions.investment_id` → `investments.id` (optional)
- `credit_cards.account_id` → `accounts.id` (one-to-one)
- `credit_card_statements.card_id` → `credit_cards.id`
- `loan_payments.loan_id` → `loans.id`
- `loan_scenarios.loan_id` → `loans.id`
- `budgets` → linked to categories
- `goals` → linked to accounts/investments

### Indexes Required
```sql
-- Transaction performance
CREATE INDEX idx_txn_account_date ON transactions(account_id, date_iso);
CREATE INDEX idx_txn_reconciled ON transactions(is_reconciled);
CREATE INDEX idx_txn_merchant ON transactions(merchant_canonical);

-- Credit card performance
CREATE INDEX idx_cc_stmt_card_date ON credit_card_statements(card_id, statement_date);
CREATE INDEX idx_cc_utilization ON credit_cards(credit_limit_paise, outstanding_paise);

-- Loan performance
CREATE INDEX idx_loan_emi_date ON loan_payments(loan_id, payment_date);
CREATE INDEX idx_loan_active ON loans(is_active, next_emi_date);

-- Behaviour trends
CREATE INDEX idx_behaviour_date ON behaviour_snapshots(snapshot_date);
CREATE INDEX idx_patterns_type ON behaviour_patterns(pattern_type);
```

---

## Migration Strategy

### Phase 1: Non-Breaking Additions
- Add nullable columns to existing tables
- Create new tables (no FKs yet)
- Backfill data where possible

### Phase 2: Constraint Enforcement
- Add foreign key constraints
- Add NOT NULL where business logic requires
- Add unique constraints for determinism

### Phase 3: Performance Optimization
- Add indexes
- Add generated columns for aggregates
- Add triggers for auto-calculations

---

## Data Integrity Rules

### Trigger: Prevent Transaction Mutation
```sql
CREATE TRIGGER prevent_transaction_update
BEFORE UPDATE ON transactions
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Transactions immutable');
END;
```

### Trigger: Auto-Balance Snapshot
```sql
CREATE TRIGGER auto_balance_snapshot
AFTER INSERT ON transactions
FOR EACH ROW
WHEN NEW.account_id IS NOT NULL
BEGIN
    INSERT OR REPLACE INTO account_balances_history
    (account_id, balance_paise, date_iso, source)
    VALUES (
        NEW.account_id,
        -- Recalculate balance from transactions
        (SELECT Σ(credits) - Σ(debits) FROM transactions 
         WHERE account_id = NEW.account_id 
         AND date_iso <= NEW.date_iso),
        NEW.date_iso,
        'actual'
    );
END;
```

---

## Test Data Requirements

### Sample Dataset
- 2 years of transactions across 5 accounts
- 3 credit cards with 12 statements each
- 2 loans (home + personal) with 24 EMIs
- 5 budget categories with variance
- 3 financial goals in progress

### Test Queries
- Cross-account reconciliation (100+ transactions)
- Loan prepayment simulation
- Credit card utilization trends
- Behaviour pattern detection
- Forecast accuracy validation