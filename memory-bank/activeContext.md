# ClariFin Loan Engine - Active Context

## Summary of Recent Changes (2026-11-07)

### Phase 3 Complete: Repository Layer Refactoring
- **LoanRepository**: Refactored with clean persistence-only API
  - New methods: `create_loan()`, `get_loan()`, `list_loans()`, `update_loan()`, `delete_loan()`
  - New methods: `add_prepayment()`, `list_prepayments()`, `remove_prepayment()`
  - New methods: `add_rate_change()`, `list_rate_changes()`, `remove_rate_change()`
  - Legacy methods preserved for backward compatibility: `create()`, `get_by_id()`, `get_all()`, `update()`, `delete()`

- **LoanPaymentRepository**: Refactored with renamed methods
  - New methods: `create_payment()`, `list_payments()`, `get_latest_payment()`
  - Removed: `get_total_paid()` (moved to service layer as financial aggregation)
  - Loan ID now uses INTEGER type to match schema

- **LoanScenarioRepository**: Removed (scenarios are temporary calculations, not persisted)

- **Database Schema (`db.py`)**: Updated in `_run_migrations()`
  - Loans table: `id INTEGER PRIMARY KEY AUTOINCREMENT` (fixed from TEXT)
  - Added: `loan_payments`, `loan_prepayments`, `loan_rate_changes` tables
  - All loan-related tables use INTEGER foreign keys

- **Dependency Boundaries Verified**:
  - ✅ Only repositories import FinanceDB
  - ✅ Engines never import repositories
  - ✅ Services use repositories only
  - ✅ Routers use services only

- **Tests**: All 13 repository smoke tests pass

## Next Steps: Phase 4
- Verify all existing functionality works
- Run full test suite

## Financial Invariants Maintained
- All monetary values in paise (integer)
- All interest rates in basis points (integer)
- Banker's rounding (ROUND_HALF_EVEN)
- Immutable schedules (never modified in-place)
- ISO 8601 date format