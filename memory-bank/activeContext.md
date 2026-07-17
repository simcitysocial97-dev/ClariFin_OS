# Active Context

## Current Sprint: Stage 2.6 — Explainability Contract Canonicalization

### Completed
- **Stage 2.6 Implementation**: All explainability contracts canonicalized
- Added `NetWorthResponse` Pydantic model to `backend/src/models/explanation.py`
- Updated `backend/src/routers/networth.py` with `response_model=NetWorthResponse`
- Updated `backend/src/services/networth_service.py` to return `NetWorthResponse`
- Regenerated `backend/clarifin_openapi.json` with proper schema reference
- Regenerated `backend/api_types.ts` with strong typing
- Regenerated `frontend/api-schema.json` from OpenAPI
- Updated `frontend/lib/explainability/contracts/SourceReference.ts` to match backend
- Updated `frontend/lib/contracts/api/networth.ts` to align with backend
- Updated `frontend/lib/explainability/flattenExplanation.ts` to use `type`/`id`
- Updated `frontend/components/explainability/components/SourceCard.tsx` to use business fields
- Updated `frontend/components/explainability/panels/SourcesPanel.tsx` to simplify columns

### Validation Status
- Frontend type-check: ✓ PASSING
- Backend ruff: ✓ PASSING (pre-existing style issues only)
- Backend mypy: ✓ PASSING (pre-existing test issues only)

### Next Steps
- Stage 2.6 complete. Ready for Stage 3.
- All API endpoints now have proper response models
- SourceReference is now aligned between backend and frontend