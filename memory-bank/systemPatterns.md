# System Patterns

## Architecture Overview

ClariFin_OS uses a **Modular Monolith** architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  (Next.js 16 + React 19 + TypeScript + Tailwind + shadcn)   │
└─────────────────────────────────────────────────────────────┘
                               │
                               │ HTTP/REST
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        Backend                               │
│                    (FastAPI + SQLite)                        │
├─────────────────────────────────────────────────────────────┤
│  Routers (18)  →  Engines (15)  →  Database Layer (db.py)  │
│                                                              │
│  • accounts        • balance        • SQLite + WAL          │
│  • cards           • behavior       • Immutable ledger      │
│  • transactions    • cashflow       • Hash signatures       │
│  • dashboard       • loan           • Triggers              │
│  • categories      • networth                               │
│  • upload          • projection                             │
│  • behavior        • reconciliation                         │
│  • loans           • recurring                              │
│  • investments     • snapshot                               │
│  • income_sources  • insight                                │
│  • recurring       • nudge                                  │
│  • snapshots       • audit                                  │
│  • projections                                               │
│  • export                                                    │
│  • reconciliation                                            │
│  • audit                                                     │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Patterns

### 1. Immutable Ledger Pattern

**Principle**: Transactions are append-only, never modified or deleted.

**Implementation**:
```sql
-- Database triggers enforce immutability
CREATE TRIGGER prevent_transaction_update
BEFORE UPDATE ON transactions
BEGIN
    SELECT RAISE(ABORT, 'Transactions are immutable. Cannot update.');
END;

CREATE TRIGGER prevent_transaction_delete
BEFORE DELETE ON transactions
BEGIN
    SELECT RAISE(ABORT, 'Transactions are immutable. Cannot delete.');
END;
```

**Benefits**:
- Complete audit trail
- Deterministic replay possible
- No data loss
- Simplified caching

**Trade-offs**:
- Cannot correct errors (must create offsetting transactions)
- Storage grows indefinitely
- No true "updates" to categorization (workaround: category column is mutable)

### 2. Deterministic Computation Pattern

**Principle**: Same inputs always produce same outputs.

**Implementation**:
```python
# Engines are pure functions
def compute_running_balance(
    db: "FinanceDB",
    account_id: Optional[str] = None,
    starting_balance_paise: int = 0,
) -> List[Dict]:
    # Always returns same result for same inputs
    # No randomness, no external calls
    # SQL ORDER BY ensures deterministic ordering
```

**Requirements**:
- No random number generation
- No external API calls
- No time-based logic (except for "now" as explicit parameter)
- SQL queries must have deterministic ORDER BY

### 3. Integer Paise Pattern

**Principle**: All monetary values stored as INTEGER paise (1 rupee = 100 paise).

**Implementation**:
```python
# Amount stored as integer
amount_paise: int = 100_500  # ₹1,005.00

# Conversion from float input uses Decimal for exactness
from decimal import Decimal, ROUND_HALF_UP
def parse_amount_to_paise(amount) -> int:
    if isinstance(amount, float):
        return int((Decimal(str(amount)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

# Arithmetic is pure integer math
total_paise = sum(row['debit'] for row in txs)
avg_paise = total_paise // len(txs)
```

**Schema**:
- Primary: `transactions.amount_paise INTEGER DEFAULT 0`
- Primary: `transactions.debit INTEGER DEFAULT 0`
- Primary: `transactions.credit INTEGER DEFAULT 0`
- Migration: `statements.*_paise INTEGER DEFAULT 0` (6 columns added)
- Migration: `reconciliations.amount_paise INTEGER DEFAULT 0`
- Legacy: `statements.amount REAL` (DEPRECATED, preserved for backward compat)

**Benefits**:
- Zero rounding errors in arithmetic
- Exact financial calculations
- No floating-point precision loss

### 4. Hash Chain Pattern

**Principle**: Every transaction has a SHA-256 hash signature for deduplication and integrity.

**Implementation**:
```sql
hash_signature = LOWER(HEX(SHA256(
    COALESCE(bank, '') || '|' ||
    COALESCE(date_iso, '') || '|' ||
    COALESCE(description, '') || '|' ||
    COALESCE(debit, 0) || '|' ||
    COALESCE(credit, 0)
)))
```

**Benefits**:
- Idempotent imports (skip duplicates)
- Ledger integrity verification
- Audit trail

### 5. Repository Pattern

**Principle**: Database operations encapsulated in repository classes.

**Implementation**:
```python
# Repository class pattern (used by cashflow_engine, networth_engine, loan_engine)
class FinanceDB:
    def get_transactions(self, account_id: str) -> List[Dict]: ...
    def insert_transactions(self, txns: List[Dict]): ...
    def get_accounts(self) -> List[Dict]: ...

# Usage
db = FinanceDB(db_path)
txns = db.get_transactions(account_id)
```

**Note**: Some engines (7 of 15) use `db_path: str` instead of FinanceDB. This inconsistency is documented in `SECOND_PASS_AUDIT_PRIORITIZED_ROADMAP.md` as P2 refactor.

### 6. Job Queue Pattern

**Principle**: Long-running operations (PDF imports) use background jobs.

**Implementation**:
```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    payload_json TEXT NOT NULL DEFAULT '{}',
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
```

**Staging Pipeline**:
```
statement_imports → statement_pages → staged_transactions → transactions
                         ↓
                    auto_heal_events (balance reconciliation)
```

**Note**: Quarantine feature deprecated. quarantine_pages table removed.

---

## Module Inventory

### Routers (18)
1. accounts.py — Account management CRUD
2. admin.py — Admin operations
3. analytics.py — Analytics endpoints
4. audit.py — Audit log queries
5. behavior.py — Behavioral indices
6. cards.py — Credit card management
7. categories.py — Category management
8. dashboard.py — Dashboard aggregations
9. export.py — Data export (JSON/CSV)
10. health.py — Health check
11. imports.py — PDF import staging
12. income_sources.py — Income source CRUD
13. insights.py — Insight generation
14. loans.py — Loan management
15. members.py — Member management
16. networth.py — Net worth queries
17. projections.py — Projection queries
18. reconciliation.py — Transfer matching
19. recurring.py — Recurring transaction CRUD
20. settings.py — Settings management
21. snapshots.py — Monthly snapshot queries
22. transactions.py — Transaction queries
23. upload.py — PDF upload endpoint

**Total: 101 endpoints across 18 routers**

### Engines (15)
1. balance_engine — Running balance computation
2. behavior_engine — Behavioral pattern analysis (experimental)
3. cashflow_engine — Monthly cash flow metrics
4. insight_generator — Evidence-based insights
5. job_engine — Background job processing
6. ledger_audit_engine — Hash chain validation
7. loan_engine — EMI, amortization, projections
8. networth_engine — Net worth computation
9. nudge_engine — Behavioral nudges
10. projection_engine — Future value projections
11. reconciliation_engine — Transfer matching
12. recurring_engine — Recurring pattern detection
13. snapshot_engine — Monthly snapshot generation
14. statement_validator — Staging → commit orchestration
15. validation_engine — Balance delta validation

### Database Tables (19)
1. statements — PDF statement metadata
2. transactions — Immutable transaction ledger
3. accounts — Managed accounts
4. cards — Credit/debit cards
5. members — Family members
6. import_mappings — CSV import configurations
7. reconciliations — Transfer matches
8. income_sources — Regular income tracking
9. loans — Loan records and schedules
10. loan_payments — EMI payment history
11. investments — Investment holdings
12. monthly_snapshots — Monthly financial summaries
13. recurring_transactions — Auto-detected patterns
14. statement_imports — PDF import staging
15. statement_pages — Per-page extraction results
16. staged_transactions — Pre-commit transaction staging
17. auto_heal_events — Balance reconciliation events
18. layout_templates — PDF layout fingerprints
19. jobs — Background job queue

---

## Consistency Rules

### Monetary Storage Rule
- **ALWAYS** use `_paise` INTEGER columns for currency
- **NEVER** use REAL/FLOAT for financial totals
- **ALWAYS** convert via `Decimal(str(value))` for string-to-integer parsing
- **NEVER** store monetary values as Python float

### Determinism Rule
- **ALWAYS** add `ORDER BY` to SQL queries returning multiple rows
- **NEVER** use `datetime.now()` inside engine calculations
- **ALWAYS** pass explicit dates to engines, never derive internally

### Immutability Rule
- **NEVER** UPDATE or DELETE from `transactions` table
- **ALWAYS** INSERT new transactions for corrections
- **ONLY** `category` and `subcategory` columns are mutable