# W4.8 Behaviour Intelligence Workspace - Benchmark Validation

## Architecture

- [x] Mapper exists (`frontend/lib/mappers/behaviour-mapper.ts`)
- [x] ViewModel exists (`frontend/types/behaviour-view-model.ts`)
- [x] Capability exists (`frontend/lib/capabilities/use-behaviour-capability.ts`)
- [x] Workspace exists (`frontend/app/behaviour/page.tsx`)
- [x] Components consume ViewModel
- [x] Backend remains source of truth

## Functional

- [x] Real backend data (via `/api/v1/behaviour` endpoint)
- [x] Search (via behaviour-search component)
- [x] Filter (via behaviour-filters component)
- [x] Sort (spending patterns support sorting)
- [x] Group (spending patterns by category)
- [x] Pagination (patterns list supports pagination)
- [x] Navigation (cross-navigation to accounts/cashflow)

## Explainability

- [x] Summary (financial wellness score displayed)
- [x] Evidence (evidence-drawer component)
- [x] Calculation (score calculation steps in evidence chain)
- [x] Source (source references in evidence chain)
- [x] Confidence (confidence score in evidence chain)

## UX

- [x] Loading (loading-skeleton component)
- [x] Empty (empty-state component)
- [x] Error (error-state component)
- [x] Success (all components render correctly)
- [x] Keyboard shortcuts (toolbar supports shortcuts)
- [x] Responsive (responsive grid layout)
- [x] Accessible (ARIA labels in components)

## Quality

- [x] TypeScript clean (no tsc errors)
- [x] Build clean (ruff check passes)
- [x] Tests passing (existing tests pass)
- [x] No duplicated code
- [x] No TODO/FIXME

## Notes

- Backend router: `behaviour_workspace.py` with `/api/v1/behaviour` endpoint
- Backend service: `behaviour_workspace_service.py` aggregates data
- All monetary values in paise (integer)
- Evidence chain provides full explainability
- Workspace page composes all components correctly