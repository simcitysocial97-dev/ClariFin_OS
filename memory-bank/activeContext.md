# ClariFin Loan Engine - Active Context

## Summary of Recent Changes (2026-11-07)

### Phase 5 Complete: API Integration and Backend Contract Completion

#### Router Changes (`backend/src/routers/loans.py`)
- Removed inline DTOs, now imports from `models.loan` and `models.loan_simulation`
- `GET /api/loans` returns array directly (not wrapped in object)
- `GET /api/loans/{loan_id}` uses `LoanResponse` model with `rate_bps`
- All simulation endpoints use request bodies instead of query params
- Added `GET /api/loans/{loan_id}` endpoint for individual loan retrieval

#### Models Created/Updated
- **`loan.py`**: Added `LoanCreateRequest`, `LoanUpdateRequest`, `LoanResponse`, `ScheduleRow`, `ScheduleResponse`
- **`loan_simulation.py`** (new): Added `PrepaymentSimulationRequest`, `PrepaymentSimulationResponse`, `ForeclosureSimulationResponse`, `RateChangeSimulationRequest`, `RateChangeSimulationResponse`, `PaymentRequest`, `PaymentResponse`
- **`errors.py`**: Added standardized error constants (`LOAN_NOT_FOUND`, `INVALID_REQUEST`, `VALIDATION_ERROR`, `AMOUNT_INVALID`, `RATE_INVALID`, `TENURE_INVALID`)

#### Service Layer Updates
- **`loan_service.py`**: `get_schedule()` returns spec-compliant format with `emi_paise`, `total_interest_paise`, `schedule`
- **`loan_simulation_service.py`**: All simulation methods return spec formats with proper field names

#### Tests Added (`tests/test_loan_routers.py`)
- 11 tests covering CRUD, schedule, simulation, payment, and analysis endpoints
- Full prepayment closure test
- No database mutation verification for simulations
- Schedule invariant validation

#### API Schema
- Updated `frontend/api-schema.json` with new loan endpoints

## Acceptance Criteria Status
- ✅ Routers only call services
- ✅ No FinanceDB access outside repositories
- ✅ All loan operations have validated APIs (`rate_bps: 0-5000`, `tenure_months: 1-360`, `principal_paise > 0`)
- ✅ Simulation endpoints do not mutate data
- ✅ Error responses are consistent (via NotFoundError)
- ✅ API contracts ready for frontend integration

## Next Steps
- Phase 6: Frontend integration with OpenAPI schema
- Monitor performance for large schedules (consider pagination if needed)

## Financial Invariants Maintained
- All monetary values in paise (integer)
- All interest rates in basis points (integer, stored as `rate_bps`: 0-5000)
- Banker's rounding (ROUND_HALF_EVEN)
- Immutable schedules (never modified in-place)
- ISO 8601 date format