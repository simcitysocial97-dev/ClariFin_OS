# Dependency Map

## Major Module Imports

### Routers Import Patterns

Routers import primarily from:
- Services (their corresponding service)
- Models (for request/response DTOs)
- FastAPI internals

```
routers/accounts.py → account_service, account models, AccountDTO
routers/cashflow.py → cashflow_service
routers/credit_cards.py → credit_card_service, credit_card models
routers/reconciliation.py → reconciliation_service
routers/banks.py → bank_repository (via service), institution_repository
routers/import_router.py → statement_service
```

### Services Import Patterns

Services import:
- Engines (for business logic)
- Repositories (for data access)
- Models (for data structures)

```
account_service.py → AccountRepository
cashflow_service.py → CashflowRepository, cashflow_engine, financial_events_service
credit_card_service.py → CreditCardRepository, credit_card_engine
reconciliation_service.py → ReconciliationRepository, reconciliation_engine
behaviour_service.py → BehaviourRepository, behaviour_engine
financial_events_service.py → FinancialEventRepository, transaction_intelligence_service
```

### Engines Import Patterns

Engines should be pure and only import:
- Models (for data structures)
- Standard library / typing

Currently some engines violate this by importing sqlite3 directly.

## Circular Dependency Risks

| Risk Area | Description | Status |
|-----------|-------------|--------|
| `financial_events_service.py` → `transaction_intelligence_service.py` | Cross-service dependency | Potential risk |
| `cashflow_service.py` → `financial_events_service.py` | Cashflow depends on events service | Potential risk |
| `services/behavior_service.py` ↔ `engines/behaviour_engine/` | Legacy ↔ canonical | Duplicate code, cleanup needed |

## Repository Boundary Rule

**Enforced:** Only `src/repositories/` may import `FinanceDB`.

Violations detected:
- Some engines call `sqlite3.connect()` directly (purity violation)
- Need to refactor engines to accept data via parameters instead of direct DB access

## Key Dependency Chains (Verified)

### Transaction Reconciliation Flow
```
routers/reconciliation.py
  → services/reconciliation_service.py
    → engines/reconciliation_engine.py (Hungarian algorithm)
      → repositories/reconciliation_repository.py
        → FinanceDB
```

### Loan Analysis Flow
```
routers/loans.py
  → services/loan_analysis_service.py
    → engines/loan_engine/
      → repositories/loan_repository.py
        → FinanceDB
```

### Behaviour Score Flow
```
routers/behaviour.py
  → services/behaviour_service.py
    → engines/behaviour_engine/
      → repositories/behaviour_repository.py
        → FinanceDB
```

## Clean Architecture Compliance

| Layer | Complies | Notes |
|-------|-----------|-------|
| Routers | ✅ Mostly | Only import services/models |
| Services | ✅ Mostly | Some SQL in reconciliation_service (needs check) |
| Engines | ⚠️ Partial | Some call sqlite3.connect() directly |
| Repositories | ✅ Yes | All extend BaseRepository |