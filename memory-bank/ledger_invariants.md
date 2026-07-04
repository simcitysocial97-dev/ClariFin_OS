# Ledger Invariants

> Core invariants governing the immutable ledger design.
> These invariants are non-negotiable and enforced by database triggers.

## Statement Commit Invariants

### 1. Atomic Statement Commit
A statement is committed to the immutable ledger **only if** reconciliation passes.

```
IF reconciliation_passes(statement):
    COMMIT all transactions atomically
ELSE:
    REJECT entire statement (no partial commits)
```

**Enforcement**: Application-level validation before DB insert.

### 2. No Partial Statement Commit
All transactions from a single statement must be committed together or not at all.

```python
# Correct: Atomic insert
try:
    for txn in statement_transactions:
        db.insert_transaction(txn)  # Within single transaction context
    db.commit()
except ValidationError:
    db.rollback()  # No partial commits
```

**Enforcement**: SQLite transaction wrapper in `FinanceDB.transaction()`.

## Immutability Invariants

### 3. Immutable Facts vs Mutable Interpretations

| Type | Examples | Mutability |
|------|----------|------------|
| **Facts** (Immutable) | `date`, `amount_paise`, `debit`, `credit`, `hash_signature` | NEVER modified |
| **Interpretations** (Mutable) | `category`, `subcategory`, `member` | Can be updated |

**Principle**: Raw transaction data (facts) is append-only. Annotations/categories (interpretations) can be updated separately without altering the underlying fact.

### 4. Transaction Immutability
Transactions in the ledger can never be updated or deleted.

**Database Enforcement**:
```sql
-- Prevents any UPDATE on transactions
CREATE TRIGGER prevent_transaction_update
BEFORE UPDATE ON transactions
BEGIN
    SELECT RAISE(ABORT, 'Transactions are immutable. Cannot update.');
END;

-- Prevents any DELETE on transactions
CREATE TRIGGER prevent_transaction_delete
BEFORE DELETE ON transactions
BEGIN
    SELECT RAISE(ABORT, 'Transactions are immutable. Cannot delete.');
END;
```

### 5. Correction Via Offset
Errors are corrected by creating offsetting transactions, not by editing existing ones.

```
Original:    -₹1000 (incorrect category)
Correction:  +₹1000 (reversal entry)
             -₹1000 (correct category)
```

## Validation Invariants

### 6. Deterministic Delta Calculation
Statement validation must use integer-only arithmetic:

```python
delta_paise = (opening_balance_paise 
               + sum(credits_paise) 
               - sum(debits_paise) 
               - closing_balance_paise)

# delta_paise == 0: Statement is balanced
# delta_paise != 0: Statement has discrepancy
```

**Requirements**:
- Integer paise values only (no floating-point)
- Pure function (no side effects)
- Deterministic (same inputs → same output)

### 7. Reconciliation Metadata-Only
Cross-account reconciliations are metadata-only; they never mutate transaction records.

```python
# CORRECT: Update reconciliation status only
db.confirm_reconciliation(rec_id)  # Updates reconciliations.status

# INCORRECT: Never modify the underlying transactions
db.update_transaction(...)  # NEVER do this
```

**Enforcement**: Reconciliation engine uses separate `reconciliations` table.

## Hash Invariants

### 8. Deterministic Hash Signatures
Each transaction has a unique hash computed from immutable fields:

```
hash = SHA256(account_id | date_iso | description | debit | credit)
```

**Properties**:
- Same transaction data → same hash (deterministic)
- Different transaction data → different hash (collision-resistant)
- Hash changes if any fact changes (tamper-evident)

### 9. Hash-Based Deduplication
Duplicate transactions are prevented via `INSERT OR IGNORE` on hash_signature.

```sql
CREATE UNIQUE INDEX idx_transaction_hash ON transactions(hash_signature);

INSERT OR IGNORE INTO transactions (... hash_signature ...) VALUES (...);
```

## Event Ledger Invariants

### 10. Immutable Events (Append-Only)
The `financial_events` table contains the authoritative log of all event-sourced activities (transactions, loans, adjustments, corrections, reconciliations). 
Once inserted, these events are strictly immutable:
- No `UPDATE` or `DELETE` statements may ever execute on `financial_events`.
- Corrections are modeled by appending new events with compensating/offsetting amounts, rather than editing previous entries.

## Summary

| Invariant | Enforcement |
|-----------|-------------|
| Atomic statement commit | Application logic + transactions |
| No partial commits | SQLite transaction wrapper |
| Facts immutable | Database triggers |
| Interpretations mutable | Direct UPDATE allowed |
| Correction via offset | Business logic pattern |
| Integer delta calculation | validation_engine.py |
| Metadata-only reconciliation | Separate reconciliations table |
| Deterministic hashes | SHA256 formula |
| Hash deduplication | UNIQUE index + INSERT OR IGNORE |
| Immutable Events | Append-only financial_events logic |
