# Active Context

## Current Sprint: Stage 3.3-3.5 Explanation Pipeline (2026-07-18)

### Completed
- **Stage 3.3 - Debt Management (Loans)**
  - Added `LoansResponse` and `LoansResponse` Pydantic models to `backend/src/models/explanation.py`
  - Added `calculate_with_explanation()` method to `LoanService` in `backend/src/services/loan_service.py`
  - Updated `/api/loans` router with `response_model=LoansResponse`
  - Created `frontend/lib/contracts/api/loans.ts` with Zod schema
  - Created `frontend/lib/models/loans.ts` with `LoansModel` including explanation field
  - Created `frontend/lib/mappers/loans.ts` to preserve explanation in DTO mapping
  - Updated `frontend/lib/hooks/use-loans.ts` to use new schema and mapper
  - Updated `frontend/app/loans/page.tsx` to use new model types
  - Updated `frontend/components/dashboard/widgets/borrowing-widget.tsx` to use new model types

- **Stage 3.4 - Credit Cards**
  - Added `CreditCardSummary` and `CreditCardsResponse` Pydantic models to `backend/src/models/explanation.py`
  - Added `calculate_with_explanation()` method to `CreditCardService` in `backend/src/services/credit_card_service.py`
  - Updated `/api/v1/credit-cards` router with `response_model=CreditCardsResponse`
  - Created `frontend/lib/contracts/api/cards.ts` with Zod schema
  - Created `frontend/lib/models/cards.ts` with `CreditCardsModel` including explanation field
  - Created `frontend/lib/mappers/cards.ts` to preserve explanation in DTO mapping
  - Updated `frontend/lib/hooks/use-cards.ts` to use new schema and mapper
  - Updated `frontend/app/cards/page.tsx` to use new model types
  - Updated `frontend/components/cards/card-portfolio-header.tsx` to use new model types
  - Updated `frontend/components/cards/credit-card-tile.tsx` to use new model types
  - Updated `frontend/components/cards/statement-history-drawer.tsx` to use new model types

- **Stage 3.5 - Investments**
  - Added `InvestmentSummary` and `InvestmentsResponse` Pydantic models to `backend/src/models/explanation.py`
  - Updated `/api/investments` router with `response_model=InvestmentsResponse`
  - Created `frontend/lib/contracts/api/investments.ts` with Zod schema
  - Created `frontend/lib/models/investments.ts` with `InvestmentsModel` including explanation field
  - Created `frontend/lib/mappers/investments.ts` to preserve explanation in DTO mapping
  - Updated `frontend/lib/hooks/use-investments.ts` to use new schema and mapper
  - Updated `frontend/app/investments/page.tsx` to use new model types

### Next Steps
- Regenerate OpenAPI schemas (`clarifin_openapi.json`, `api_types.ts`, `types/api-generated.ts`)
- Run full test suite to verify all changes
- Add capability-specific explainability UI (if needed)