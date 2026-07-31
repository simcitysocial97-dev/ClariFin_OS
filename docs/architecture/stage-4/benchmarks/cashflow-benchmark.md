# W4.2 Cashflow Truth Workspace - Benchmark Validation

## Architecture

- [x] Mapper exists (`frontend/lib/mappers/cashflow-mapper.ts`)
- [x] ViewModel exists (`frontend/types/cashflow-view-model.ts`)
- [x] Capability exists (`frontend/lib/capabilities/use-cashflow-capability.ts`)
- [x] Workspace exists (`frontend/app/cashflow/page.tsx`)
- [x] Components consume ViewModel
- [x] Backend remains source of truth

## Functional

- [x] Real backend data (via `/api/v1/cashflow` endpoint)
- [x] Search (via cashflow-search component)
- [x] Filter (via cashflow-filters component)
- [x] Sort (transaction list supports sorting)
- [x] Group (category breakdown provides grouping)
- [x] Pagination (transaction list supports pagination)
- [x] Navigation (cross-navigation to accounts/transactions)

## Explainability

- [x] Summary (total income/expenses/net displayed)
- [x] Evidence (evidence-drawer component)
- [x] Calculation (calculation steps in evidence chain)
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

- Backend router: `cashflow_workspace.py` with `/api/v1/cashflow` endpoint
- Backend service: `cashflow_workspace_service.py` aggregates data
- All monetary values in paise (integer)
- Evidence chain provides full explainability
- Workspace page composes all components correctly