# W4.1 — Net Worth Intelligence Workspace

## Overview
Real-time net worth tracking across all financial accounts. Aggregates assets (accounts, investments) and liabilities (loans, credit cards) into a single net worth figure with historical trend, composition breakdown, and explainability.

---

## Capability 1: Net Worth ViewModel

### Goal
Define the canonical ViewModel for net worth display with full explainability support.

### Dependencies
None (foundational type)

### Required Files
- `frontend/types/net-worth-view-model.ts`

### Files to Modify
- `frontend/types/index.ts` (add export)

### Validation Criteria
- All fields typed with paise (integer) for monetary values
- Evidence chain, calculation steps, source references present
- Historical snapshot array typed correctly

### Definition of Done
- ViewModel compiles with strict TypeScript
- All monetary fields use `number` (paise)
- Evidence, calculation, source, confidence fields present
- Exported from types index

### Rollback Strategy
Revert file creation. No consumers exist yet.

### Atomic TODOs
1. Create `NetWorthViewModel` type with total_net_worth_paise, total_assets_paise, total_liabilities_paise
2. Add `NetWorthComposition` type with asset_breakdown and liability_breakdown arrays
3. Add `NetWorthHistoricalSnapshot` type with date, net_worth_paise, assets_paise, liabilities_paise
4. Add `NetWorthTrend` type with direction, percentage_change, period
5. Add `EvidenceChain` type with summary, evidence array, calculation steps, source references
6. Add `ConfidenceScore` type with score (0-100), factors array
7. Add `NetWorthInsight` type with type, severity, message, action_url
8. Add `NetWorthFilters` type with date_range, account_types, period
9. Add `NetWorthNavigation` type with deep_link, cross_references
10. Add JSDoc comments for all fields
11. Create unit tests verifying type structure
12. Export from `frontend/types/index.ts`
13. Validate against backend DTO structure
14. Add invariant tests (assets - liabilities = net_worth)

---

## Capability 2: Net Worth Mapper

### Goal
Transform backend DTO to NetWorthViewModel with full evidence mapping.

### Dependencies
Capability 1 (NetWorthViewModel)

### Required Files
- `frontend/lib/mappers/net-worth-mapper.ts`

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
- Performance: map 1000 snapshots under 50ms

### Rollback Strategy
Remove mapper file and index export. No consumers yet.

### Atomic TODOs
1. Create `mapNetWorthDTO` function signature
2. Implement total net worth calculation mapping
3. Implement composition breakdown mapping
4. Implement historical snapshot mapping
5. Implement trend calculation mapping
6. Implement evidence chain mapping
7. Implement confidence score mapping
8. Implement insight mapping
9. Add null/empty handling for all fields
10. Add date formatting for snapshots
11. Add amount formatting (paise to display)
12. Create unit tests for all mapping functions
13. Add performance test (1000 snapshots under 50ms)
14. Add integration test with mock API response
15. Export from mappers index

---

## Capability 3: Net Worth Capability Hook

### Goal
Provide net worth data, filters, and actions to workspace components.

### Dependencies
Capability 1, Capability 2

### Required Files
- `frontend/lib/capabilities/use-net-worth-capability.ts`
- `frontend/lib/capabilities/net-worth-context.tsx`

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
Remove capability files and index export. No consumers yet.

### Atomic TODOs
1. Create `NetWorthContext` with state and actions
2. Create `NetWorthProvider` component
3. Implement `useNetWorthCapability` hook
4. Add `fetchNetWorth` action with React Query
5. Add `fetchHistoricalSnapshots` action
6. Add `filterByDateRange` action
7. Add `filterByAccountType` action
8. Add `filterByPeriod` action
9. Add `toggleEvidenceDrawer` action
10. Add `refreshNetWorth` action
11. Add loading state management
12. Add error state management
13. Add retry action for failed operations
14. Add React Query cache configuration
15. Add query key constants
16. Create unit tests for all actions
17. Export from capabilities index

---

## Capability 4: Net Worth Summary Card

### Goal
Display current net worth with trend indicator and period comparison.

### Dependencies
Capability 3

### Required Files
- `frontend/components/net-worth/net-worth-summary.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows total net worth in formatted currency
- Shows trend arrow (up/down/flat) with percentage
- Shows period comparison (this month vs last month)
- Loading skeleton state
- Error state with retry

### Definition of Done
- Component renders all states correctly
- Responsive layout
- Dark mode support
- Accessibility (ARIA labels)
- Unit tests pass

### Rollback Strategy
Remove component file. No consumers yet.

### Atomic TODOs
1. Create summary card layout
2. Add net worth amount display with formatting
3. Add trend indicator (up/down/flat arrow)
4. Add percentage change display
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

## Capability 5: Net Worth Composition Chart

### Goal
Visualize net worth composition as assets vs liabilities breakdown.

### Dependencies
Capability 3

### Required Files
- `frontend/components/net-worth/composition-chart.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows asset categories with values
- Shows liability categories with values
- Interactive legend
- Responsive sizing
- Loading/empty/error states

### Definition of Done
- Chart renders correctly
- All states handled
- Responsive
- Accessible

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create composition chart layout
2. Add asset breakdown section with category bars
3. Add liability breakdown section with category bars
4. Add value labels for each category
5. Add percentage labels for each category
6. Add interactive legend
7. Add loading skeleton state
8. Add empty state (no accounts configured)
9. Add error state
10. Add responsive sizing
11. Add dark mode support
12. Add ARIA labels for chart elements
13. Create unit tests
14. Add accessibility tests

---

## Capability 6: Net Worth Historical Trend Chart

### Goal
Display net worth history over time with interactive date range.

### Dependencies
Capability 3

### Required Files
- `frontend/components/net-worth/trend-chart.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Line chart showing net worth over time
- Date range selector (1M, 3M, 6M, 1Y, ALL)
- Interactive tooltips
- Loading/empty/error states

### Definition of Done
- Chart renders with historical data
- Date range switching works
- Tooltips show values
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create trend chart layout
2. Add line chart for net worth over time
3. Add date range selector buttons (1M, 3M, 6M, 1Y, ALL)
4. Add interactive tooltips with date and value
5. Add loading skeleton state
6. Add empty state (no history)
7. Add error state
8. Add responsive sizing
9. Add dark mode support
10. Add ARIA labels
11. Create unit tests
12. Add accessibility tests

---

## Capability 7: Net Worth Account Breakdown Table

### Goal
Show detailed list of all accounts contributing to net worth.

### Dependencies
Capability 3

### Required Files
- `frontend/components/net-worth/account-breakdown.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Table with account name, type, balance, contribution %
- Sortable by any column
- Clickable rows navigate to account workspace
- Loading/empty/error states

### Definition of Done
- Table renders with all accounts
- Sorting works
- Navigation works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create account breakdown table layout
2. Add columns: name, type, balance, contribution %
3. Add sort controls for each column
4. Add click handler for row navigation
5. Add loading skeleton rows
6. Add empty state (no accounts)
7. Add error state
8. Add responsive horizontal scroll
9. Add dark mode support
10. Add ARIA labels for table
11. Create unit tests
12. Add accessibility tests

---

## Capability 8: Net Worth Filters

### Goal
Filter net worth view by account type, date range, and period.

### Dependencies
Capability 3

### Required Files
- `frontend/components/net-worth/net-worth-filters.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Account type filter (all, assets, liabilities)
- Date range filter
- Period comparison selector
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
2. Add account type selector (all/assets/liabilities)
3. Add date range picker
4. Add period comparison selector
5. Add active filter count badge
6. Add clear all filters button
7. Add filter state persistence to URL
8. Add responsive collapse on mobile
9. Add dark mode support
10. Add ARIA labels
11. Add keyboard navigation
12. Create unit tests
13. Add accessibility tests

---

## Capability 9: Net Worth Search

### Goal
Search accounts within net worth view.

### Dependencies
Capability 3

### Required Files
- `frontend/components/net-worth/net-worth-search.tsx`

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

## Capability 10: Net Worth Evidence Drawer

### Goal
Show explainability evidence for net worth calculations.

### Dependencies
Capability 3

### Required Files
- `frontend/components/net-worth/evidence-drawer.tsx`

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

## Capability 11: Net Worth Insights Panel

### Goal
Display actionable insights about net worth.

### Dependencies
Capability 3

### Required Files
- `frontend/components/net-worth/insights-panel.tsx`

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

## Capability 12: Net Worth Toolbar

### Goal
Provide toolbar with actions for net worth workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/net-worth/net-worth-toolbar.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Refresh button
- Filter toggle
- Export button
- Date range selector
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
5. Add date range quick selector
6. Add active filter count badge
7. Add responsive collapse menu on mobile
8. Add dark mode support
9. Add ARIA labels
10. Add keyboard shortcuts
11. Create unit tests
12. Add accessibility tests

---

## Capability 13: Net Worth Workspace Page

### Goal
Compose all net worth components into a complete workspace page.

### Dependencies
Capabilities 1-12

### Required Files
- `frontend/app/net-worth/page.tsx`

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
2. Add NetWorthProvider at page level
3. Add toolbar region
4. Add summary card region
5. Add composition chart region
6. Add trend chart region
7. Add account breakdown table region
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

## Capability 14: Net Worth Loading States

### Goal
Handle all loading states for net worth workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/net-worth/loading-skeleton.tsx`

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
2. Create composition chart skeleton
3. Create trend chart skeleton
4. Create table skeleton rows
5. Add pulse animation
6. Add responsive sizing
7. Add dark mode support
8. Create unit tests

---

## Capability 15: Net Worth Error States

### Goal
Handle all error states for net worth workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/net-worth/error-state.tsx`

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

## Capability 16: Net Worth Empty States

### Goal
Handle empty states for net worth workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/net-worth/empty-state.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Empty message displayed
- Action button to add accounts
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
4. Add action button (add accounts)
5. Add help text with instructions
6. Add responsive layout
7. Add dark mode support
8. Add ARIA labels
9. Create unit tests

---

## Capability 17: Net Worth Cross-Navigation

### Goal
Enable navigation from net worth to related workspaces.

### Dependencies
Capability 3

### Required Files
- `frontend/lib/navigation/net-worth-navigation.ts`

### Files to Modify
- `frontend/lib/navigation/index.ts` (add export)

### Validation Criteria
- Click account navigates to Accounts workspace
- Click investment navigates to Investments workspace
- Click loan navigates to Loans workspace
- Click card navigates to Credit Cards workspace
- Deep links preserve context

### Definition of Done
- All navigation paths work
- Deep links preserve filter context
- Tested

### Rollback Strategy
Remove navigation file and revert index.

### Atomic TODOs
1. Create navigation to Accounts workspace
2. Create navigation to Investments workspace
3. Create navigation to Loans workspace
4. Create navigation to Credit Cards workspace
5. Add deep link context preservation
6. Add navigation breadcrumb
7. Add back button
8. Add keyboard shortcuts for navigation
9. Create unit tests
10. Export from navigation index

---

## Capability 18: Net Worth Backend DTO

### Goal
Define backend DTO for net worth API response.

### Dependencies
None (backend)

### Required Files
- `backend/src/core/dtos/net_worth_dto.py`

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
1. Create `NetWorthDTO` with total_net_worth_paise
2. Add `NetWorthCompositionDTO` with asset/liability breakdown
3. Add `NetWorthSnapshotDTO` for historical data
4. Add `NetWorthTrendDTO` with direction and percentage
5. Add `NetWorthInsightDTO` with type and severity
6. Add Pydantic validators for paise fields
7. Add optional field handling
8. Add field descriptions
9. Create unit tests
10. Export from DTOs __init__

---

## Capability 19: Net Worth Backend Router

### Goal
Create API endpoints for net worth data.

### Dependencies
Capability 18

### Required Files
- `backend/src/routers/net_worth_router.py`

### Files to Modify
- `backend/src/api.py` (register router)

### Validation Criteria
- GET /api/v1/net-worth returns current net worth
- GET /api/v1/net-worth/history returns historical snapshots
- GET /api/v1/net-worth/insights returns insights
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
2. Add GET /net-worth endpoint
3. Add GET /net-worth/history endpoint
4. Add GET /net-worth/insights endpoint
5. Add query parameter handling (date_range, account_types)
6. Add error handling for missing data
7. Add response models
8. Add tags and metadata
9. Create unit tests
10. Register router in api.py

---

## Capability 20: Net Worth Backend Service

### Goal
Implement business logic for net worth calculations.

### Dependencies
Capability 18, Capability 19

### Required Files
- `backend/src/services/net_worth_service.py`

### Files to Modify
None (new file)

### Validation Criteria
- Aggregates all account balances
- Calculates total assets and liabilities
- Computes historical snapshots
- Generates insights
- Handles empty account state

### Definition of Done
- Service returns correct calculations
- Edge cases handled
- Tests pass
- mypy strict passes

### Rollback Strategy
Remove service file.

### Atomic TODOs
1. Create `NetWorthService` class
2. Implement `get_current_net_worth` method
3. Implement `get_historical_snapshots` method
4. Implement `get_composition_breakdown` method
5. Implement `get_trend` method
6. Implement `get_insights` method
7. Add account aggregation logic
8. Add asset/liability classification
9. Add empty state handling
10. Add error handling
11. Create unit tests
12. Add integration tests

---

## Capability 21: Net Worth Benchmark Validation

### Goal
Validate net worth workspace against Stage 4 benchmark.

### Dependencies
All capabilities 1-20

### Required Files
- `docs/stage-4/benchmarks/net-worth-benchmark.md`

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