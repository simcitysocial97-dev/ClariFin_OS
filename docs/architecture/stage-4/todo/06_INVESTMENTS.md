# W4.6 — Investments Intelligence Workspace

## Overview
Real-time investment tracking across all portfolios. Shows holdings, performance, returns, and diversification with full explainability.

---

## Capability 1: Investments ViewModel

### Goal
Define the canonical ViewModel for investments display with full explainability support.

### Dependencies
None (foundational type)

### Required Files
- `frontend/types/investments-view-model.ts`

### Files to Modify
- `frontend/types/index.ts` (add export)

### Validation Criteria
- All monetary fields in paise (integer)
- Holdings, performance, returns, diversification typed correctly
- Evidence chain, calculation steps, source references present

### Definition of Done
- ViewModel compiles with strict TypeScript
- All monetary fields use `number` (paise)
- Evidence, calculation, source, confidence fields present
- Exported from types index

### Rollback Strategy
Revert file creation. No consumers exist yet.

### Atomic TODOs
1. Create `InvestmentsViewModel` type with total_value_paise, total_return_paise, return_percentage, holdings_count
2. Add `HoldingDetail` type with id, scheme_name, asset_class, quantity, nav_paise, value_paise, return_paise, return_percentage
3. Add `PortfolioPerformance` type with date, value_paise, benchmark_value_paise, daily_change_paise
4. Add `AssetAllocation` type with asset_class, value_paise, percentage, count
5. Add `EvidenceChain` type with summary, evidence array, calculation steps, source references
6. Add `ConfidenceScore` type with score (0-100), factors array
7. Add `InvestmentInsight` type with type, severity, message, action_url
8. Add `InvestmentFilters` type with asset_classes, scheme_types, date_range, performance_range
9. Add JSDoc comments for all fields
10. Create unit tests verifying type structure
11. Export from `frontend/types/index.ts`
12. Validate against backend DTO structure
13. Add invariant tests (sum of holding values = total_value)

---

## Capability 2: Investments Mapper

### Goal
Transform backend DTO to InvestmentsViewModel with full evidence mapping.

### Dependencies
Capability 1 (InvestmentsViewModel)

### Required Files
- `frontend/lib/mappers/investments-mapper.ts`

### Files to Modify
- `frontend/lib/mappers/index.ts` (add export)

### Validation Criteria
- All DTO fields mapped to ViewModel
- Monetary values converted to paise
- Evidence chain preserved
- Empty/null handling for missing data

### Definition of Done
- Mapper compiles with strict TypeScript
- All transformation functions tested
- Edge cases handled (null, empty, partial data)
- Performance: map 1000 holdings under 50ms

### Rollback Strategy
Remove mapper file and index export.

### Atomic TODOs
1. Create `mapInvestmentsDTO` function signature
2. Implement portfolio summary mapping
3. Implement holding detail mapping
4. Implement performance history mapping
5. Implement asset allocation mapping
6. Implement evidence chain mapping
7. Implement confidence score mapping
8. Implement insight mapping
9. Add null/empty handling for all fields
10. Add date formatting for performance history
11. Add amount formatting (paise to display)
12. Create unit tests for all mapping functions
13. Add performance test (1000 holdings under 50ms)
14. Add integration test with mock API response
15. Export from mappers index

---

## Capability 3: Investments Capability Hook

### Goal
Provide investments data, filters, and actions to workspace components.

### Dependencies
Capability 1, Capability 2

### Required Files
- `frontend/lib/capabilities/use-investments-capability.ts`
- `frontend/lib/capabilities/investments-context.tsx`

### Files to Modify
- `frontend/lib/capabilities/index.ts` (add export)

### Validation Criteria
- Hook returns ViewModel, loading, error, filters, actions
- React Query integration for caching
- Filter/sort/group actions work correctly
- Evidence drawer toggle works

### Definition of Done
- Hook compiles with strict TypeScript
- All actions tested
- Loading/error states managed
- React Query cache configured

### Rollback Strategy
Remove capability files and index export.

### Atomic TODOs
1. Create `InvestmentsContext` with state and actions
2. Create `InvestmentsProvider` component
3. Implement `useInvestmentsCapability` hook
4. Add `fetchPortfolio` action with React Query
5. Add `fetchHoldings` action
6. Add `fetchPerformance` action
7. Add `fetchAssetAllocation` action
8. Add `filterByAssetClass` action
9. Add `filterBySchemeType` action
10. Add `filterByDateRange` action
11. Add `filterByPerformanceRange` action
12. Add `selectHolding` action
13. Add `toggleEvidenceDrawer` action
14. Add `refreshInvestments` action
15. Add loading state management
16. Add error state management
17. Add retry action for failed operations
18. Add React Query cache configuration
19. Add query key constants
20. Create unit tests for all actions
21. Export from capabilities index

---

## Capability 4: Investments Summary Card

### Goal
Display portfolio summary with total value, returns, and holdings count.

### Dependencies
Capability 3

### Required Files
- `frontend/components/investments/investments-summary.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows total portfolio value
- Shows total return with percentage
- Shows day change
- Shows number of holdings
- Loading/error states

### Definition of Done
- Component renders all states correctly
- Responsive layout
- Dark mode support
- Accessibility (ARIA labels)
- Unit tests pass

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create summary card layout
2. Add total portfolio value display
3. Add total return with percentage and color coding
4. Add day change indicator
5. Add holdings count
6. Add loading skeleton state
7. Add error state with retry button
8. Add responsive styling
9. Add dark mode support
10. Add ARIA labels
11. Add keyboard navigation
12. Create unit tests
13. Add accessibility tests

---

## Capability 5: Investments Portfolio Performance Chart

### Goal
Visualize portfolio value over time with benchmark comparison.

### Dependencies
Capability 3

### Required Files
- `frontend/components/investments/performance-chart.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Line chart showing portfolio value over time
- Benchmark comparison line
- Date range selector
- Interactive tooltips
- Loading/empty/error states

### Definition of Done
- Chart renders with performance data
- Benchmark comparison works
- Date range switching works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create performance chart layout
2. Add line chart for portfolio value
3. Add benchmark comparison line
4. Add date range selector (1M, 3M, 6M, 1Y, ALL)
5. Add interactive tooltips with date and value
6. Add loading skeleton state
7. Add empty state (no performance data)
8. Add error state
9. Add responsive sizing
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 6: Investments Asset Allocation Chart

### Goal
Show portfolio allocation by asset class.

### Dependencies
Capability 3

### Required Files
- `frontend/components/investments/asset-allocation.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Pie or treemap chart by asset class
- Value and percentage labels
- Interactive legend
- Clickable to filter
- Loading/empty/error states

### Definition of Done
- Chart renders with allocation data
- Click to filter works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create asset allocation layout
2. Add chart (pie or treemap) for asset classes
3. Add asset class name labels
4. Add value labels
5. Add percentage labels
6. Add interactive legend
7. Add click handler to filter by asset class
8. Add loading skeleton state
9. Add empty state (no holdings)
10. Add error state
11. Add responsive layout
12. Add dark mode support
13. Add ARIA labels
14. Create unit tests
15. Add accessibility tests

---

## Capability 7: Investments Holdings Table

### Goal
Show detailed holdings list with performance metrics.

### Dependencies
Capability 3

### Required Files
- `frontend/components/investments/holdings-table.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Table with scheme name, asset class, quantity, NAV, value, return %
- Sortable by any column
- Clickable rows open evidence
- Pagination
- Loading/empty/error states

### Definition of Done
- Table renders with holdings
- Sorting works
- Pagination works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create holdings table layout
2. Add columns: scheme, asset class, quantity, NAV, value, return %
3. Add sort controls for each column
4. Add click handler for evidence drawer
5. Add pagination controls
6. Add loading skeleton rows
7. Add empty state (no holdings)
8. Add error state
9. Add responsive horizontal scroll
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 8: Investments Filters

### Goal
Filter investments view by asset class, scheme type, and date range.

### Dependencies
Capability 3

### Required Files
- `frontend/components/investments/investments-filters.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Asset class multi-select
- Scheme type filter
- Date range filter
- Performance range filter
- Active filter count badge

### Definition of Done
- All filters functional
- Filter state persists
- Responsive layout
- Accessible

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create filter panel layout
2. Add asset class multi-select with checkboxes
3. Add scheme type filter
4. Add date range picker
5. Add performance range (min/max) inputs
6. Add active filter count badge
7. Add clear all filters button
8. Add filter state persistence to URL
9. Add responsive collapse on mobile
10. Add dark mode support
11. Add ARIA labels
12. Add keyboard navigation
13. Create unit tests
14. Add accessibility tests

---

## Capability 9: Investments Search

### Goal
Search holdings and schemes within investments view.

### Dependencies
Capability 3

### Required Files
- `frontend/components/investments/investments-search.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Search input with debounce
- Results highlight matching text
- Clear button
- Keyboard shortcut (Ctrl+K)

### Definition of Done
- Search functional
- Debounce working
- Empty/loading states handled
- Accessible

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create search input component
2. Add 300ms debounce
3. Add search results highlighting
4. Add clear button
5. Add keyboard shortcut (Ctrl+K)
6. Add empty results state
7. Add loading state
8. Add error state
9. Add responsive full-width on mobile
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 10: Investments Evidence Drawer

### Goal
Show explainability evidence for investment valuations and returns.

### Dependencies
Capability 3

### Required Files
- `frontend/components/investments/evidence-drawer.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Drawer slides in from right
- Shows summary, evidence list, calculation chain, source references
- Confidence score displayed
- Close button and keyboard (Escape)

### Definition of Done
- Drawer opens/closes correctly
- All evidence sections populated
- Responsive (full-width on mobile)
- Accessible

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create evidence drawer layout
2. Add summary section at top
3. Add evidence list with icons
4. Add calculation chain view
5. Add source reference links
6. Add confidence score display
7. Add close button
8. Add Escape key handler
9. Add responsive full-width on mobile
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 11: Investments Insights Panel

### Goal
Display actionable insights about investments.

### Dependencies
Capability 3

### Required Files
- `frontend/components/investments/insights-panel.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows insights with severity indicators
- Each insight has message and optional action
- Loading/empty/error states

### Definition of Done
- Insights render correctly
- All states handled
- Responsive
- Accessible

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create insights panel layout
2. Add insight card component with severity icon
3. Add insight message display
4. Add action button for actionable insights
5. Add loading skeleton state
6. Add empty state (no insights)
7. Add error state
8. Add responsive layout
9. Add dark mode support
10. Add ARIA labels
11. Create unit tests
12. Add accessibility tests

---

## Capability 12: Investments Toolbar

### Goal
Provide toolbar with actions for investments workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/investments/investments-toolbar.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Refresh button
- Filter toggle
- Export button
- View toggle (table/chart)
- Active filter count

### Definition of Done
- All toolbar buttons functional
- Responsive (collapses on mobile)
- Accessible

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create toolbar layout
2. Add refresh button with loading spinner
3. Add filter toggle button
4. Add export CSV button
5. Add view toggle (table/chart)
6. Add active filter count badge
7. Add responsive collapse menu on mobile
8. Add dark mode support
9. Add ARIA labels
10. Add keyboard shortcuts
11. Create unit tests
12. Add accessibility tests

---

## Capability 13: Investments Workspace Page

### Goal
Compose all investments components into a complete workspace page.

### Dependencies
Capabilities 1-12

### Required Files
- `frontend/app/investments/page.tsx` (modify existing)

### Files to Modify
- `frontend/lib/config/navigation.ts` (ensure route)

### Validation Criteria
- All regions composed correctly
- Loading/empty/error states for workspace
- URL state persistence
- Responsive layout
- Keyboard navigation

### Definition of Done
- Page renders all components
- All states handled
- URL state persists filters
- Responsive
- Accessible
- All benchmark checks pass

### Rollback Strategy
Revert page to previous version.

### Atomic TODOs
1. Refactor workspace page layout
2. Add InvestmentsProvider at page level
3. Add toolbar region
4. Add summary card region
5. Add performance chart region
6. Add asset allocation region
7. Add holdings table region
8. Add insights panel region
9. Add evidence drawer region
10. Add workspace loading state
11. Add workspace error state
12. Add workspace empty state
13. Add URL state persistence for filters
14. Add responsive layout
15. Add dark mode support
16. Add keyboard navigation
17. Add ARIA landmarks
18. Create workspace integration tests
19. Create accessibility tests
20. Ensure navigation route in config

---

## Capability 14: Investments Loading States

### Goal
Handle all loading states for investments workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/investments/loading-skeleton.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Skeleton matches final layout
- Summary card skeleton
- Chart skeleton
- Table skeleton
- Animation

### Definition of Done
- All skeletons render correctly
- Animation smooth
- Responsive

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create summary card skeleton
2. Create performance chart skeleton
3. Create asset allocation skeleton
4. Create table skeleton rows
5. Add pulse animation
6. Add responsive sizing
7. Add dark mode support
8. Create unit tests

---

## Capability 15: Investments Error States

### Goal
Handle all error states for investments workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/investments/error-state.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Error message displayed
- Retry button functional
- Error details expandable
- Recovery suggestions

### Definition of Done
- Error state renders correctly
- Retry works
- Responsive
- Accessible

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create error state layout
2. Add error icon
3. Add error message display
4. Add retry button
5. Add error details expandable section
6. Add recovery suggestions
7. Add responsive layout
8. Add dark mode support
9. Add ARIA labels
10. Create unit tests

---

## Capability 16: Investments Empty States

### Goal
Handle empty states for investments workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/investments/empty-state.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Empty message displayed
- Action button to add investments
- Illustration or icon
- Help text

### Definition of Done
- Empty state renders correctly
- Action button navigates correctly
- Responsive
- Accessible

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create empty state layout
2. Add empty state icon/illustration
3. Add empty message text
4. Add action button (add investments)
5. Add help text with instructions
6. Add responsive layout
7. Add dark mode support
8. Add ARIA labels
9. Create unit tests

---

## Capability 17: Investments Cross-Navigation

### Goal
Enable navigation from investments to related workspaces.

### Dependencies
Capability 3

### Required Files
- `frontend/lib/navigation/investments-navigation.ts`

### Files to Modify
- `frontend/lib/navigation/index.ts` (add export)

### Validation Criteria
- Click holding navigates to Net Worth workspace
- Click account navigates to Accounts workspace
- Deep links preserve context

### Definition of Done
- All navigation paths work
- Deep links preserve filter context
- Tested

### Rollback Strategy
Remove navigation file and revert index.

### Atomic TODOs
1. Create navigation to Net Worth workspace
2. Create navigation to Accounts workspace
3. Add deep link context preservation
4. Add navigation breadcrumb
5. Add back button
6. Add keyboard shortcuts for navigation
7. Create unit tests
8. Export from navigation index

---

## Capability 18: Investments Backend DTO

### Goal
Define backend DTO for investments API response.

### Dependencies
None (backend)

### Required Files
- `backend/src/core/dtos/investments_dto.py`

### Files to Modify
- `backend/src/core/dtos/__init__.py` (add export)

### Validation Criteria
- DTO includes all required fields
- Monetary values in paise (integer)
- Pydantic validation
- Optional fields handled

### Definition of Done
- DTO compiles with mypy strict
- Pydantic validation works
- All fields typed correctly

### Rollback Strategy
Remove DTO file and revert __init__.py.

### Atomic TODOs
1. Create `PortfolioSummaryDTO` with total_value_paise, total_return_paise, return_percentage
2. Add `HoldingDetailDTO` with scheme_name, asset_class, quantity, nav_paise, value_paise
3. Add `PerformanceHistoryDTO` with date, value_paise, benchmark_value_paise
4. Add `AssetAllocationDTO` with asset_class, value_paise, percentage
5. Add `InvestmentInsightDTO` with type and severity
6. Add Pydantic validators for paise fields
7. Add optional field handling
8. Add field descriptions
9. Create unit tests
10. Export from DTOs __init__

---

## Capability 19: Investments Backend Router

### Goal
Create API endpoints for investments data.

### Dependencies
Capability 18

### Required Files
- `backend/src/routers/investments_router.py` (modify existing)

### Files to Modify
- `backend/src/api.py` (ensure registration)

### Validation Criteria
- GET /api/v1/investments/portfolio returns portfolio summary
- GET /api/v1/investments/holdings returns holdings list
- GET /api/v1/investments/performance returns performance history
- GET /api/v1/investments/allocation returns asset allocation
- Query parameters for filtering
- Proper error responses

### Definition of Done
- All endpoints return correct data
- Error handling works
- Tests pass
- mypy strict passes

### Rollback Strategy
Revert router to previous version.

### Atomic TODOs
1. Ensure router with /api/v1 prefix
2. Add GET /investments/portfolio endpoint
3. Add GET /investments/holdings endpoint
4. Add GET /investments/performance endpoint
5. Add GET /investments/allocation endpoint
6. Add query parameter handling (asset_class, date_range)
7. Add error handling for missing data
8. Add response models
9. Add tags and metadata
10. Create unit tests
11. Ensure registered in api.py

---

## Capability 20: Investments Backend Service

### Goal
Implement business logic for investments calculations.

### Dependencies
Capability 18, Capability 19

### Required Files
- `backend/src/services/investments_service.py`

### Files to Modify
None (new file)

### Validation Criteria
- Aggregates portfolio value from holdings
- Computes performance history
- Computes asset allocation
- Generates insights
- Handles empty portfolio state

### Definition of Done
- Service returns correct calculations
- Edge cases handled
- Tests pass
- mypy strict passes

### Rollback Strategy
Remove service file.

### Atomic TODOs
1. Create `InvestmentsService` class
2. Implement `get_portfolio_summary` method
3. Implement `get_holdings` method
4. Implement `get_performance_history` method
5. Implement `get_asset_allocation` method
6. Implement `get_insights` method
7. Add portfolio aggregation logic
8. Add return calculation logic
9. Add empty state handling
10. Add error handling
11. Create unit tests
12. Add integration tests

---

## Capability 21: Investments Benchmark Validation

### Goal
Validate investments workspace against Stage 4 benchmark.

### Dependencies
All capabilities 1-20

### Required Files
- `docs/stage-4/benchmarks/investments-benchmark.md`

### Files to Modify
None (new file)

### Validation Criteria
- All benchmark items checked
- Architecture compliance verified
- Functional requirements met
- Explainability requirements met
- UX requirements met
- Quality requirements met

### Definition of Done
- All benchmark items pass
- No violations found
- Documentation complete

### Rollback Strategy
Remove benchmark file.

### Atomic TODOs
1. Verify Mapper exists
2. Verify ViewModel exists
3. Verify Capability exists
4. Verify Workspace exists
5. Verify Components consume ViewModel
6. Verify Backend remains source of truth
7. Verify Real backend data
8. Verify Search works
9. Verify Filter works
10. Verify Sort works
11. Verify Group works
12. Verify Pagination works
13. Verify Navigation works
14. Verify Summary displayed
15. Verify Evidence displayed
16. Verify Calculation shown
17. Verify Source referenced
18. Verify Confidence shown
19. Verify Loading state
20. Verify Empty state
21. Verify Error state
22. Verify Keyboard shortcuts
23. Verify Responsive design
24. Verify Accessibility
25. Verify TypeScript clean
26. Verify Build clean
27. Verify Tests passing
28. Verify No duplicated code
29. Verify No TODO/FIXME