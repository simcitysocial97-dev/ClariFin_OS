# Behaviour Engine Architecture - ClariFinOS 2.0

## Overview

The Behaviour Engine provides deterministic behavioural intelligence for financial analysis. It consumes data from repositories and exposes behavioral metrics through service layer APIs.

---

## Input Data Sources

### Transaction Repository
- **Method**: `get_all_transactions(filters: dict)`
- **Key Fields**: 
  - `type` — "credit" (income) or "debit" (expense)
  - `amount_paise` — Canonical monetary storage (₹1.00 = 100 paise)
  - `date_iso` — ISO 8601 date string (YYYY-MM-DD)
  - `category` — Primary classification
  - `subcategory` — Secondary classification
  - `account_id` — Account linkage
- **Filters**: `date_from`, `date_to`, `bank`, `category`, `type`, `member`

### Account Repository
- **Method**: `get_all_accounts()`
- **Key Fields**:
  - `balance_paise` — Current account balance
  - `account_type` — savings, current, credit_card, loan, investment, other
  - `bank` — Institution identifier

### Loan Repository
- **Method**: `list_loans()` (filters active loans via `is_active = 1`)
- **Key Fields**:
  - `principal_paise` — Original loan amount
  - `outstanding_paise` — Remaining principal
  - `emi_paise` — Monthly payment
  - `interest_rate_bps` — Annual rate in basis points

### Credit Card Repository
- **Method**: `list_cards(account_id: str | None)` (filters active cards)
- **Key Fields**:
  - `credit_limit_paise` — Total credit limit
  - `annual_fee_paise` — Yearly fee
  - `interest_rate_bps` — APR in basis points

### Reconciliation Repository
- **Method**: `get_confirmed_transfer_ids()`
- **Purpose**: Identify and exclude internal transfers from spending analysis

### Cashflow Repository
- **Method**: `get_monthly_cashflow()`
- **Key Fields**:
  - `income_paise` — Sum of credits per month
  - `expense_paise` — Sum of debits per month

---

## Future Financial Event Compatibility

The Behaviour Engine will evolve to accept `FinancialEvent` DTOs that consolidate raw transactions with reconciliation metadata.

### Event Types (StrEnum)
```python
from enum import StrEnum

class EventType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    LIABILITY_INCREASE = "liability_increase"
    LIABILITY_DECREASE = "liability_decrease"
    CASH_ADVANCE = "cash_advance"
```

### Why Events Matter
1. **Transfers** — Own-account transfers must be excluded from income/expense calculations
2. **Liability Changes** — Credit card payments are liability decreases, not expenses
3. **Cash Advances** — Cash advance repayments vs spending require distinction
4. **Confidence Tracking** — Events carry `confidence` score from reconciliation matching

### FinancialEvent DTO
See `backend/src/models/financial_event.py` for full definition.

---

## Service Boundaries

```
Routers → BehaviourService → BehaviourEngine → Repositories
```

### Engine Layer (`src/engines/behaviour_engine.py`)
- **Pure functions only** — No database imports
- Accepts data via parameters: `transactions: list[dict]`, `loans: list[dict]`, etc.
- Returns deterministic metrics dictionaries
- No side effects (no DB writes)

### Service Layer (to be created: `src/services/behaviour_service.py`)
- Orchestrates repository calls
- Transforms raw data to engine-ready format
- Calls engine functions
- Persists computed scores (if needed)
- Handles `household_id`/`owner_id` scoping

### Repository Layer (`src/repositories/`)
- Persistence operations only
- Returns raw dicts or domain models
- No financial calculations

---

## Repository Dependencies

| Repository | Used By | Purpose |
|------------|---------|---------|
| `TransactionRepository` | BehaviourService | Income/expense aggregation, category analysis |
| `AccountRepository` | BehaviourService | Balance trend analysis, account health |
| `LoanRepository` | BehaviourService | Liability health, DTI calculation |
| `CreditCardRepository` | BehaviourService | Utilization impact, credit health |
| `ReconciliationRepository` | BehaviourService | Transfer exclusion |
| `CashflowRepository` | BehaviourService | Monthly net flow |

---

## Engine Responsibilities

### Phase 1 Metrics (Currently Implemented)

| Metric | Function | Description |
|--------|----------|-------------|
| Loss Aversion Index | `_compute_loss_aversion_index()` | Post-income spend velocity (72h window) |
| Impulsivity Score | `_compute_impulsivity_score()` | Micro-transaction ratio (<₹200) |
| Habit Stability Score | `_compute_habit_stability_score()` | Category coefficient of variation |
| Financial Stress Index | `_compute_financial_stress_index()` | Buffer days, overspend ratio |
| Savings Discipline Score | `_compute_savings_discipline_score()` | Monthly savings rate trend |

### Phase 2 Metrics (Planned)

| Metric | Description |
|--------|-------------|
| Net Cash Flow | `(income_paise - expense_paise)` excluding transfers |
| Debt-to-Income Ratio | `total_emi / monthly_income` |
| Emergency Fund Adequacy | `emergency_fund / (monthly_expenses / 3)` |
| Credit Utilization Impact | `used_limit / credit_limit` trend |
| Lifestyle Inflation Rate | Non-essential YoY growth |

---

## Data Contracts

### FinancialEvent (Future)
- Consolidates transaction + reconciliation data
- Enables proper classification of financial flows
- Fields: `event_id`, `transaction_ids`, `event_type`, `amount_paise`, `date_iso`, `account_id`, `confidence`, `household_id`, `owner_id`

### BehaviourInput (Interface)
```python
class BehaviourInput(BaseModel):
    transactions: list[dict[str, Any]]
    accounts: list[dict[str, Any]]
    loans: list[dict[str, Any]]
    credit_cards: list[dict[str, Any]]
    reconciliations: list[tuple[int, int]]
    household_id: str | None = None
```

---

## Testing Strategy

- Unit tests for each metric function
- Deterministic tests (same input = same output)
- Edge case tests (empty data, single transaction)
- Paise-based monetary validation

---

## Validation Commands

```bash
# Backend validation
cd backend && ./venv/bin/python3 -m ruff check .
cd backend && ./venv/bin/python3 -m mypy .