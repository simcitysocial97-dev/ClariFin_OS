# Active Context

## Current Sprint: Cashflow Explanation Pipeline (2026-07-18)

### Completed
- Added `CashflowResponse` Pydantic model with `ExplanationMixin` to `backend/src/models/explanation.py`
- Added `calculate_with_explanation()` method to `CashflowService` in `backend/src/services/cashflow_service.py`
- Updated `/api/cashflow/monthly` router with `response_model=CashflowResponse`
- Created `frontend/lib/contracts/api/cashflow.ts` with Zod schema re-exporting shared explanation types
- Updated `frontend/lib/models/cashflow.ts` to include `explanation` field
- Updated `frontend/lib/mappers/cashflow.ts` to preserve explanation in DTO mapping
- Updated `frontend/lib/hooks/use-cashflow.ts` to use new schema
- Regenerated OpenAPI schemas via backend startup
- Backend validation passed (ruff, mypy)
- Frontend type-check and build passed

### Next Steps
- Add cashflow explanation UI components to display evidence and calculation steps
- Write integration tests for cashflow explanation endpoint
- Consider adding cashflow to capability registry if not already present