# W4.2 — Cashflow Truth Workspace

## Overview
Real cashflow tracking across all accounts. Shows income vs expenses over time with categorization, trends, and explainability. Every transaction is traceable to its source.

---

## Capability 1: Cashflow ViewModel

### Goal
Define the canonical ViewModel for cashflow display with full explainability support.

### Dependencies
None (foundational type)

### Required Files
- `frontend/types/cashflow-view-model.ts`

### Files to Modify
- `frontend/types/index.ts` (add export)

### Validation Criteria
- All monetary fields in paise (integer)
- Income/expense breakdown typed correctly
- Evidence chain, calculation steps, source references present
- Monthly aggregation typed correctly

### Definition of Done
- ViewModel compiles with strict TypeScript
- All monetary fields use `number` (paise)
- Evidence, calculation, source, confidence fields present
- Exported from types index

### Rollback Strategy
Revert file creation. No consumers exist yet.

### Atomic TODOs
1. Create `CashflowViewModel` type with total_income_paise, total_expenses_paise, net_cashflow_paise
2. Add `CashflowMonthlySummary` type with month, income_paise, expenses_paise, net_paise, transaction_count
3. Add `CashflowCategoryBreakdown` type with category_id, category_name, amount_paise, percentage, transaction_count
4. Add `CashflowTrend` type with direction, percentage_change, period, volatility_score
5. Add `CashflowTransaction` type with id, date, description, amount_paise, category, merchant
6. Add `EvidenceChain` type with summary, evidence array, calculation steps, source references
7. Add `ConfidenceScore` type with score (0-100), factors array
8. Add `CashflowInsight` type with type, severity, message, action_url
9. Add `CashflowFilters` type with date_range, categories, merchants, amount_range
10. Add JSDoc comments for all fields
11. Create unit tests verifying type structure
12. Export from `frontend/types/index.ts`
13. Validate against backend DTO structure
14. Add invariant tests (income - expenses = net_cashflow)

---

## Capability 2: Cashflow Mapper

### Goal
Transform backend DTO to CashflowViewModel with full evidence mapping.

### Dependencies
Capability 1 (CashflowViewModel)

### Required Files
- `frontend/lib/mappers/cashflow-mapper.ts`

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
- Performance: map 1000 transactions under 50ms

### Rollback Strategy
Remove mapper file and index export.

### Atomic TODOs
1. Create `mapCashflowDTO` function signature
2. Implement monthly summary mapping
3. Implement category breakdown mapping
4. Implement trend calculation mapping
5. Implement transaction mapping
6. Implement evidence chain mapping
7. Implement confidence score mapping
8. Implement insight mapping
9. Add null/empty handling for all fields
10. Add date formatting for monthly summaries
11. Add amount formatting (paise to display)
12. Create unit tests for all mapping functions
13. Add performance test (1000 transactions under 50ms)
14. Add integration test with mock API response
15. Export from mappers index

---

## Capability 3: Cashflow Capability Hook

### Goal
Provide cashflow data, filters, and actions to workspace components.

### Dependencies
Capability 1, Capability 2

### Required Files
- `frontend/lib/capabilities/use-cashflow-capability.ts`
- `frontend/lib/capabilities/cashflow-context.tsx`

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
1. Create `CashflowContext` with state and actions
2. Create `CashflowProvider` component
3. Implement `useCashflowCapability` hook
4. Add `fetchCashflowSummary` action with React Query
5. Add `fetchMonthlyBreakdown` action
6. Add `fetchCategoryBreakdown` action
7. Add `filterByDateRange` action
8. Add `filterByCategory` action
9. Add `filterByMerchant` action
10. Add `filterByAmountRange` action
11. Add `toggleEvidenceDrawer` action
12. Add `refreshCashflow` action
13. Add loading state management
14. Add error state management
15. Add retry action for failed operations
16. Add React Query cache configuration
17. Add query key constants
18. Create unit tests for all actions
19. Export from capabilities index

---

## Capability 4: Cashflow Summary Card

### Goal
Display current period cashflow with income vs expenses comparison.

### Dependencies
Capability 3

### Required Files
- `frontend/components/cashflow/cashflow-summary.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows total income, expenses, net cashflow
- Color-coded (green for positive, red for negative)
- Period comparison
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
2. Add income amount display with green indicator
3. Add expenses amount display with red indicator
4. Add net cashflow display with color coding
5. Add period comparison text
6. Add loading skeleton state
7. Add error state with retry button
8. Add responsive styling
9. Add dark mode support
10. Add ARIA labels
11. Add keyboard navigation
12. Create unit tests
13. Add accessibility tests

---

## Capability 5: Cashflow Monthly Trend Chart

### Goal
Visualize income vs expenses over time as bar/line chart.

### Dependencies
Capability 3

### Required Files
- `frontend/components/cashflow/monthly-trend.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Grouped bar chart showing income and expenses per month
- Net cashflow line overlay
- Date range selector
- Interactive tooltips
- Loading/empty/error states

### Definition of Done
- Chart renders with monthly data
- Date range switching works
- Tooltips show values
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create monthly trend chart layout
2. Add grouped bars for income and expenses
3. Add net cashflow line overlay
4. Add month labels on x-axis
5. Add date range selector (3M, 6M, 1Y, ALL)
6. Add interactive tooltips with values
7. Add loading skeleton state
8. Add empty state (no data)
9. Add error state
10. Add responsive sizing
11. Add dark mode support
12. Add ARIA labels
13. Create unit tests
14. Add accessibility tests

---

## Capability 6: Cashflow Category Breakdown

### Goal
Show spending breakdown by category with percentages.

### Dependencies
Capability 3

### Required Files
- `frontend/components/cashflow/category-breakdown.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Horizontal bar chart of categories by amount
- Percentage labels
- Color-coded categories
- Clickable to filter
- Loading/empty/error states

### Definition of Done
- Chart renders with category data
- Click to filter works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create category breakdown layout
2. Add horizontal bars for each category
3. Add category name labels
4. Add amount labels
5. Add percentage labels
6. Add color coding by category
7. Add click handler to filter by category
8. Add loading skeleton state
9. Add empty state (no categories)
10. Add error state
11. Add responsive layout
12. Add dark mode support
13. Add ARIA labels
14. Create unit tests
15. Add accessibility tests

---

## Capability 7: Cashflow Transaction List

### Goal
Show detailed transaction list for selected period.

### Dependencies
Capability 3

### Required Files
- `frontend/components/cashflow/transaction-list.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Table with date, description, category, amount
- Sortable by any column
- Clickable rows open evidence
- Pagination
- Loading/empty/error states

### Definition of Done
- Table renders with transactions
- Sorting works
- Pagination works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create transaction list layout
2. Add columns: date, description, category, merchant, amount
3. Add sort controls for each column
4. Add click handler for evidence drawer
5. Add pagination controls
6. Add loading skeleton rows
7. Add empty state (no transactions)
8. Add error state
9. Add responsive horizontal scroll
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 8: Cashflow Filters

### Goal
Filter cashflow view by date range, category, merchant, and amount.

### Dependencies
Capability 3

### Required Files
- `frontend/components/cashflow/cashflow-filters.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Date range filter
- Category multi-select
- Merchant search/select
- Amount range filter
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
2. Add date range picker
3. Add category multi-select with checkboxes
4. Add merchant search/select
5. Add amount range (min/max) inputs
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

## Capability 9: Cashflow Search

### Goal
Search transactions within cashflow view.

### Dependencies
Capability 3

### Required Files
- `frontend/components/cashflow/cashflow-search.tsx`

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

## Capability 10: Cashflow Evidence Drawer

### Goal
Show explainability evidence for cashflow calculations.

### Dependencies
Capability 3

### Required Files
- `frontend/components/cashflow/evidence-drawer.tsx`

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

## Capability 11: Cashflow Insights Panel

### Goal
Display actionable insights about cashflow patterns.

### Dependencies
Capability 3

### Required Files
- `frontend/components/cashflow/insights-panel.tsx`

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

## Capability 12: Cashflow Toolbar

### Goal
Provide toolbar with actions for cashflow workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/cashflow/cashflow-toolbar.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Refresh button
- Filter toggle
- Export button
- Period selector
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
5. Add period quick selector (this month, last month, custom)
6. Add active filter count badge
7. Add responsive collapse menu on mobile
8. Add dark mode support
9. Add ARIA labels
10. Add keyboard shortcuts
11. Create unit tests
12. Add accessibility tests

---

## Capability 13: Cashflow Workspace Page

### Goal
Compose all cashflow components into a complete workspace page.

### Dependencies
Capabilities 1-12

### Required Files
- `frontend/app/cashflow/page.tsx`

### Files to Modify
- `frontend/lib/config/navigation.ts` (add route)

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
Remove page file and revert navigation config.

### Atomic TODOs
1. Create workspace page layout
2. Add CashflowProvider at page level
3. Add toolbar region
4. Add summary card region
5. Add monthly trend chart region
6. Add category breakdown region
7. Add transaction list region
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
20. Add navigation route to config

---

## Capability 14: Cashflow Loading States

### Goal
Handle all loading states for cashflow workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/cashflow/loading-skeleton.tsx`

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
2. Create monthly trend chart skeleton
3. Create category breakdown skeleton
4. Create table skeleton rows
5. Add pulse animation
6. Add responsive sizing
7. Add dark mode support
8. Create unit tests

---

## Capability 15: Cashflow Error States

### Goal
Handle all error states for cashflow workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/cashflow/error-state.tsx`

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

## Capability 16: Cashflow Empty States

### Goal
Handle empty states for cashflow workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/cashflow/empty-state.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Empty message displayed
- Action button to import transactions
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
4. Add action button (import transactions)
5. Add help text with instructions
6. Add responsive layout
7. Add dark mode support
8. Add ARIA labels
9. Create unit tests

---

## Capability 17: Cashflow Cross-Navigation

### Goal
Enable navigation from cashflow to related workspaces.

### Dependencies
Capability 3

### Required Files
- `frontend/lib/navigation/cashflow-navigation.ts`

### Files to Modify
- `frontend/lib/navigation/index.ts` (add export)

### Validation Criteria
- Click category navigates to filtered transaction view
- Click merchant navigates to merchant view
- Click account navigates to Accounts workspace
- Deep links preserve context

### Definition of Done
- All navigation paths work
- Deep links preserve filter context
- Tested

### Rollback Strategy
Remove navigation file and revert index.

### Atomic TODOs
1. Create navigation to filtered transaction view by category
2. Create navigation to filtered transaction view by merchant
3. Create navigation to Accounts workspace
4. Add deep link context preservation
5. Add navigation breadcrumb
6. Add back button
7. Add keyboard shortcuts for navigation
8. Create unit tests
9. Export from navigation index

---

## Capability 18: Cashflow Backend DTO

### Goal
Define backend DTO for cashflow API response.

### Dependencies
None (backend)

### Required Files
- `backend/src/core/dtos/cashflow_dto.py`

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
1. Create `CashflowSummaryDTO` with total_income_paise, total_expenses_paise, net_cashflow_paise
2. Add `CashflowMonthlyDTO` with month, income_paise, expenses_paise, net_paise
3. Add `CashflowCategoryDTO` with category breakdown
4. Add `CashflowTrendDTO` with direction and percentage
5. Add `CashflowInsightDTO` with type and severity
6. Add Pydantic validators for paise fields
7. Add optional field handling
8. Add field descriptions
9. Create unit tests
10. Export from DTOs __init__

---

## Capability 19: Cashflow Backend Router

### Goal
Create API endpoints for cashflow data.

### Dependencies
Capability 18

### Required Files
- `backend/src/routers/cashflow_router.py`

### Files to Modify
- `backend/src/api.py` (register router)

### Validation Criteria
- GET /api/v1/cashflow/summary returns current period summary
- GET /api/v1/cashflow/monthly returns monthly breakdown
- GET /api/v1/cashflow/categories returns category breakdown
- GET /api/v1/cashflow/transactions returns transaction list
- Query parameters for filtering
- Proper error responses

### Definition of Done
- All endpoints return correct data
- Error handling works
- Tests pass
- mypy strict passes

### Rollback Strategy
Remove router file and revert api.py.

### Atomic TODOs
1. Create router with /api/v1 prefix
2. Add GET /cashflow/summary endpoint
3. Add GET /cashflow/monthly endpoint
4. Add GET /cashflow/categories endpoint
5. Add GET /cashflow/transactions endpoint
6. Add query parameter handling (date_range, categories, merchants)
7. Add error handling for missing data
8. Add response models
9. Add tags and metadata
10. Create unit tests
11. Register router in api.py

---

## Capability 20: Cashflow Backend Service

### Goal
Implement business logic for cashflow calculations.

### Dependencies
Capability 18, Capability 19

### Required Files
- `backend/src/services/cashflow_service.py`

### Files to Modify
None (new file)

### Validation Criteria
- Aggregates income and expenses from transactions
- Computes monthly summaries
- Computes category breakdowns
- Generates insights
- Handles empty transaction state

### Definition of Done
- Service returns correct calculations
- Edge cases handled
- Tests pass
- mypy strict passes

### Rollback Strategy
Remove service file.

### Atomic TODOs
1. Create `CashflowService` class
2. Implement `get_summary` method
3. Implement `get_monthly_breakdown` method
4. Implement `get_category_breakdown` method
5. Implement `get_transactions` method
6. Implement `get_trend` method
7. Implement `get_insights` method
8. Add income/expense classification logic
9. Add empty state handling
10. Add error handling
11. Create unit tests
12. Add integration tests

---

## Capability 21: Cashflow Benchmark Validation

### Goal
Validate cashflow workspace against Stage 4 benchmark.

### Dependencies
All capabilities 1-20

### Required Files
- `docs/stage-4/benchmarks/cashflow-benchmark.md`

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