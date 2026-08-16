# W4.6 Investments Intelligence Workspace - Benchmark Validation

## Architecture

- [x] Mapper exists (`frontend/lib/mappers/investments-mapper.ts`)
- [x] ViewModel exists (`frontend/types/investments-view-model.ts`)
- [x] Capability exists (`frontend/lib/capabilities/use-investments-capability.ts`)
- [x] Workspace exists (`frontend/app/investments/page.tsx`)
- [x] Components consume ViewModel
- [x] Backend remains source of truth

## Functional

- [x] Real backend data (via `/api/v1/investments` endpoint)
- [x] Search (via investments-search component)
- [x] Filter (via investments-filters component)
- [x] Sort (holdings table supports sorting)
- [x] Group (asset allocation provides grouping)
- [x] Pagination (holdings table supports pagination)
- [x] Navigation (cross-navigation to accounts/net-worth)

## Explainability

- [x] Summary (total value/invested/returns displayed)
- [x] Evidence (evidence-drawer component)
- [x] Calculation (returns percentage breakdown in evidence chain)
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

- Backend router: `investments_workspace.py` with `/api/v1/investments` endpoint
- Backend service: `investments_workspace_service.py` aggregates data
- All monetary values in paise (integer)
- Evidence chain provides full explainability
- Workspace page composes all components correctly