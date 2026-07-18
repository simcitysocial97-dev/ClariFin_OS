# Active Context

## Current Sprint: Stage 3 Batch B Explanation Pipeline (2026-07-18)

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

- **Stage 3.6 - Batch B: Account Management, Transaction Intelligence, Financial Events**
  - Added `AccountSummary` and `AccountsResponse` Pydantic models to `backend/src/models/explanation.py`
  - Added `calculate_with_explanation()` method to `AccountService` in `backend/src/services/account_service.py`
  - Added `/api/v1/accounts/summary` endpoint to `backend/src/routers/accounts.py`
  - Updated `frontend/lib/capabilities/accounts/contracts/api.ts` with Zod schema
  - Updated `frontend/lib/capabilities/accounts/models/model.ts` with `AccountModel` including explanation field
  - Updated `frontend/lib/capabilities/accounts/mappers/mapper.ts` to preserve explanation in DTO mapping
  - Updated `frontend/lib/capabilities/accounts/services/api.ts` to use new endpoint
  - Added `OverviewResponse` Pydantic model to `backend/src/models/explanation.py`
  - Created `frontend/lib/capabilities/overview/contracts/api.ts` with Zod schema
  - Created `frontend/lib/capabilities/overview/models/model.ts` with `OverviewModel` including explanation field
  - Created `frontend/lib/capabilities/overview/mappers/mapper.ts` to preserve explanation in DTO mapping
  - Created `frontend/lib/capabilities/overview/services/api.ts` to fetch overview
  - Created `frontend/lib/capabilities/overview/hooks/useOverview.ts` to use new schema and mapper
  - Added `FinancialEventSummary` and `EventsResponse` Pydantic models to `backend/src/models/explanation.py`
  - Added `calculate_with_explanation()` method to `FinancialEventsService` in `backend/src/services/financial_events_service.py`
  - Added `/api/v1/financial-intelligence/events` endpoint to `backend/src/routers/financial_intelligence.py`

- **Stage 3.7 - Batch C: Financial Health, Forecasting, Recommendations, Pattern Analysis**
  - Added `WellnessComponent` and updated `WellnessScoreResponse` in `backend/src/models/behaviour.py` with explanation field
  - Added `calculate_with_explanation()` method to `BehaviourService` in `backend/src/services/behaviour_service.py`
  - Added `calculate_with_explanation()` method to `FinancialIntelligenceService` in `backend/src/services/financial_intelligence_service.py`
  - Updated `/api/v1/behaviour/wellness-score` router with `response_model=WellnessScoreResponse`
  - Updated `/api/v1/behaviour/patterns` router with `response_model=PatternsResponse`
  - Updated `/api/v1/behaviour/recommendations` router with `response_model=RecommendationsResponse`
  - Updated `/api/v1/financial-intelligence/outlook` router with `response_model=ForecastingResponse`
  - Created `frontend/lib/contracts/api/behavior.ts` with Zod schemas
  - Created `frontend/lib/models/behavior.ts` with `WellnessScoreModel`, `PatternsModel`, `RecommendationsModel`
  - Created `frontend/lib/mappers/behavior.ts` to preserve explanation in DTO mapping
  - Created `frontend/lib/contracts/api/forecasting.ts` with Zod schema
  - Created `frontend/lib/models/forecasting.ts` with `ForecastingModel`
  - Created `frontend/lib/mappers/forecasting.ts` to preserve explanation in DTO mapping

### Stage 3.9 - Explainability Consolidation (COMPLETED)
- Verified all capabilities follow frozen reference implementation
- Fixed Stage 3 regression: moved investments explanation building from router to service
- Fixed test mocks to use canonical SourceReference fields
- Generated `docs/STAGE3_EXPLAINABILITY_AUDIT.md` with full verification report
- All 94 frontend tests pass, no new backend errors introduced

### Next Steps
