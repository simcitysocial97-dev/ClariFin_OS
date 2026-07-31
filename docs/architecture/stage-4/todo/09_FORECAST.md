# W4.9 — Forecast Intelligence Workspace

## Overview
Real-time financial forecasting. Projects future net worth, cashflow, and financial health based on historical patterns and trends with full explainability.

---

## Capability 1: Forecast ViewModel

### Goal
Define the canonical ViewModel for forecast display with full explainability support.

### Dependencies
None (foundational type)

### Required Files
- `frontend/types/forecast-view-model.ts`

### Files to Modify
- `frontend/types/index.ts` (add export)

### Validation Criteria
- All monetary fields in paise (integer)
- Forecast projections, confidence intervals, scenarios typed correctly
- Evidence chain, calculation steps, source references present

### Definition of Done
- ViewModel compiles with strict TypeScript
- All monetary fields use `number` (paise)
- Evidence, calculation, source, confidence fields present
- Exported from types index

### Rollback Strategy
Revert file creation. No consumers exist yet.

### Atomic TODOs
1. Create `ForecastViewModel` type with projections, scenarios, confidence_intervals
2. Add `NetWorthProjection` type with date, projected_paise, lower_bound_paise, upper_bound_paise
3. Add `CashflowProjection` type with month, income_paise, expenses_paise, net_paise
4. Add `ForecastScenario` type with name, description, probability, projections array
5. Add `ConfidenceInterval` type with level (90/95/99), lower_paise, upper_paise
6. Add `EvidenceChain` type with summary, evidence array, calculation steps, source references
7. Add `ConfidenceScore` type with score (0-100), factors array
8. Add `ForecastInsight` type with type, severity, message, action_url
9. Add `ForecastFilters` type with horizon, scenarios, metric_types
10. Add JSDoc comments for all fields
11. Create unit tests verifying type structure
12. Export from `frontend/types/index.ts`
13. Validate against backend DTO structure
14. Add invariant tests (lower_bound <= projected <= upper_bound)

---

## Capability 2: Forecast Mapper

### Goal
Transform backend DTO to ForecastViewModel with full evidence mapping.

### Dependencies
Capability 1 (ForecastViewModel)

### Required Files
- `frontend/lib/mappers/forecast-mapper.ts`

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
- Performance: map 1000 projections under 50ms

### Rollback Strategy
Remove mapper file and index export.

### Atomic TODOs
1. Create `mapForecastDTO` function signature
2. Implement net worth projection mapping
3. Implement cashflow projection mapping
4. Implement scenario mapping
5. Implement confidence interval mapping
6. Implement evidence chain mapping
7. Implement confidence score mapping
8. Implement insight mapping
9. Add null/empty handling for all fields
10. Add date formatting for projections
11. Add amount formatting (paise to display)
12. Create unit tests for all mapping functions
13. Add performance test (1000 projections under 50ms)
14. Add integration test with mock API response
15. Export from mappers index

---

## Capability 3: Forecast Capability Hook

### Goal
Provide forecast data, filters, and actions to workspace components.

### Dependencies
Capability 1, Capability 2

### Required Files
- `frontend/lib/capabilities/use-forecast-capability.ts`
- `frontend/lib/capabilities/forecast-context.tsx`

### Files to Modify
- `frontend/lib/capabilities/index.ts` (add export)

### Validation Criteria
- Hook returns ViewModel, loading, error, filters, actions
- React Query integration for caching
- Filter actions work correctly
- Evidence drawer toggle works

### Definition of Done
- Hook compiles with strict TypeScript
- All actions tested
- Loading/error states managed
- React Query cache configured

### Rollback Strategy
Remove capability files and index export.

### Atomic TODOs
1. Create `ForecastContext` with state and actions
2. Create `ForecastProvider` component
3. Implement `useForecastCapability` hook
4. Add `fetchNetWorthProjection` action with React Query
5. Add `fetchCashflowProjection` action
6. Add `fetchScenarios` action
7. Add `filterByHorizon` action (3M, 6M, 1Y, 3Y, 5Y)
8. Add `filterByScenario` action
9. Add `filterByMetricType` action
10. Add `selectScenario` action
11. Add `toggleEvidenceDrawer` action
12. Add `refreshForecast` action
13. Add loading state management
14. Add error state management
15. Add retry action for failed operations
16. Add React Query cache configuration
17. Add query key constants
18. Create unit tests for all actions
19. Export from capabilities index

---

## Capability 4: Forecast Summary Card

### Goal
Display forecast summary with projected values and confidence.

### Dependencies
Capability 3

### Required Files
- `frontend/components/forecast/forecast-summary.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows projected net worth at horizon
- Shows projected cashflow
- Shows confidence level
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
2. Add projected net worth display
3. Add projected cashflow display
4. Add confidence level indicator
5. Add horizon selector
6. Add loading skeleton state
7. Add error state with retry button
8. Add responsive styling
9. Add dark mode support
10. Add ARIA labels
11. Add keyboard navigation
12. Create unit tests
13. Add accessibility tests

---

## Capability 5: Forecast Net Worth Projection Chart

### Goal
Visualize projected net worth over time with confidence bands.

### Dependencies
Capability 3

### Required Files
- `frontend/components/forecast/net-worth-projection.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Line chart showing projected net worth
- Confidence interval bands (shaded area)
- Historical data overlay
- Interactive tooltips
- Loading/empty/error states

### Definition of Done
- Chart renders with projection data
- Confidence bands displayed
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create projection chart layout
2. Add line chart for projected net worth
3. Add confidence interval shaded bands
4. Add historical data overlay
5. Add horizon selector (3M, 6M, 1Y, 3Y, 5Y)
6. Add interactive tooltips with values
7. Add loading skeleton state
8. Add empty state (no projection)
9. Add error state
10. Add responsive sizing
11. Add dark mode support
12. Add ARIA labels
13. Create unit tests
14. Add accessibility tests

---

## Capability 6: Forecast Cashflow Projection Chart

### Goal
Show projected income and expenses over forecast horizon.

### Dependencies
Capability 3

### Required Files
- `frontend/components/forecast/cashflow-projection.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Bar/line chart showing projected income and expenses
- Net cashflow line
- Interactive tooltips
- Loading/empty/error states

### Definition of Done
- Chart renders with projection data
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create cashflow projection layout
2. Add bars/lines for projected income
3. Add bars/lines for projected expenses
4. Add net cashflow line
5. Add interactive tooltips with values
6. Add loading skeleton state
7. Add empty state (no projection)
8. Add error state
9. Add responsive sizing
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 7: Forecast Scenario Comparison

### Goal
Compare multiple forecast scenarios side by side.

### Dependencies
Capability 3

### Required Files
- `frontend/components/forecast/scenario-comparison.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Multiple scenario lines on same chart
- Scenario selector
- Probability labels
- Interactive tooltips
- Loading/empty/error states

### Definition of Done
- Chart renders with scenarios
- Scenario switching works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create scenario comparison layout
2. Add multiple scenario lines on chart
3. Add scenario selector with checkboxes
4. Add probability labels for each scenario
5. Add interactive tooltips with values
6. Add loading skeleton state
7. Add empty state (no scenarios)
8. Add error state
9. Add responsive sizing
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 8: Forecast Filters

### Goal
Filter forecast view by horizon, scenario, and metric type.

### Dependencies
Capability 3

### Required Files
- `frontend/components/forecast/forecast-filters.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Horizon selector (3M, 6M, 1Y, 3Y, 5Y)
- Scenario multi-select
- Metric type filter
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
2. Add horizon selector buttons
3. Add scenario multi-select
4. Add metric type filter (net worth, cashflow, both)
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

## Capability 9: Forecast Search

### Goal
Search projections and scenarios within forecast view.

### Dependencies
Capability 3

### Required Files
- `frontend/components/forecast/forecast-search.tsx`

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

## Capability 10: Forecast Evidence Drawer

### Goal
Show explainability evidence for forecast calculations.

### Dependencies
Capability 3

### Required Files
- `frontend/components/forecast/evidence-drawer.tsx`

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

## Capability 11: Forecast Insights Panel

### Goal
Display actionable insights about forecast projections.

### Dependencies
Capability 3

### Required Files
- `frontend/components/forecast/insights-panel.tsx`

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

## Capability 12: Forecast Toolbar

### Goal
Provide toolbar with actions for forecast workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/forecast/forecast-toolbar.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Refresh button
- Filter toggle
- Export button
- Horizon selector
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
5. Add horizon quick selector
6. Add active filter count badge
7. Add responsive collapse menu on mobile
8. Add dark mode support
9. Add ARIA labels
10. Add keyboard shortcuts
11. Create unit tests
12. Add accessibility tests

---

## Capability 13: Forecast Workspace Page

### Goal
Compose all forecast components into a complete workspace page.

### Dependencies
Capabilities 1-12

### Required Files
- `frontend/app/forecast/page.tsx`

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
2. Add ForecastProvider at page level
3. Add toolbar region
4. Add summary card region
5. Add net worth projection chart region
6. Add cashflow projection chart region
7. Add scenario comparison region
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

## Capability 14: Forecast Loading States

### Goal
Handle all loading states for forecast workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/forecast/loading-skeleton.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Skeleton matches final layout
- Summary card skeleton
- Chart skeletons
- Animation

### Definition of Done
- All skeletons render correctly
- Animation smooth
- Responsive

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create summary card skeleton
2. Create net worth projection chart skeleton
3. Create cashflow projection chart skeleton
4. Create scenario comparison skeleton
5. Add pulse animation
6. Add responsive sizing
7. Add dark mode support
8. Create unit tests

---

## Capability 15: Forecast Error States

### Goal
Handle all error states for forecast workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/forecast/error-state.tsx`

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

## Capability 16: Forecast Empty States

### Goal
Handle empty states for forecast workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/forecast/empty-state.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Empty message displayed
- Action button to add data
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

## Capability 17: Forecast Cross-Navigation

### Goal
Enable navigation from forecast to related workspaces.

### Dependencies
Capability 3

### Required Files
- `frontend/lib/navigation/forecast-navigation.ts`

### Files to Modify
- `frontend/lib/navigation/index.ts` (add export)

### Validation Criteria
- Click projection point navigates to Net Worth workspace
- Click cashflow point navigates to Cashflow workspace
- Deep links preserve context

### Definition of Done
- All navigation paths work
- Deep links preserve filter context
- Tested

### Rollback Strategy
Remove navigation file and revert index.

### Atomic TODOs
1. Create navigation to Net Worth workspace
2. Create navigation to Cashflow workspace
3. Add deep link context preservation
4. Add navigation breadcrumb
5. Add back button
6. Add keyboard shortcuts for navigation
7. Create unit tests
8. Export from navigation index

---

## Capability 18: Forecast Backend DTO

### Goal
Define backend DTO for forecast API response.

### Dependencies
None (backend)

### Required Files
- `backend/src/core/dtos/forecast_dto.py`

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
1. Create `NetWorthProjectionDTO` with date, projected_paise, lower_bound_paise, upper_bound_paise
2. Add `CashflowProjectionDTO` with month, income_paise, expenses_paise, net_paise
3. Add `ForecastScenarioDTO` with name, description, probability, projections
4. Add `ConfidenceIntervalDTO` with level, lower_paise, upper_paise
5. Add `ForecastInsightDTO` with type and severity
6. Add Pydantic validators for paise fields
7. Add optional field handling
8. Add field descriptions
9. Create unit tests
10. Export from DTOs __init__

---

## Capability 19: Forecast Backend Router

### Goal
Create API endpoints for forecast data.

### Dependencies
Capability 18

### Required Files
- `backend/src/routers/forecast_router.py`

### Files to Modify
- `backend/src/api.py` (register router)

### Validation Criteria
- GET /api/v1/forecast/net-worth returns net worth projection
- GET /api/v1/forecast/cashflow returns cashflow projection
- GET /api/v1/forecast/scenarios returns scenario list
- Query parameters for horizon and scenario
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
2. Add GET /forecast/net-worth endpoint
3. Add GET /forecast/cashflow endpoint
4. Add GET /forecast/scenarios endpoint
5. Add query parameter handling (horizon, scenario)
6. Add error handling for missing data
7. Add response models
8. Add tags and metadata
9. Create unit tests
10. Register router in api.py

---

## Capability 20: Forecast Backend Service

### Goal
Implement business logic for forecast calculations.

### Dependencies
Capability 18, Capability 19

### Required Files
- `backend/src/services/forecast_service.py`

### Files to Modify
None (new file)

### Validation Criteria
- Projects net worth based on historical trends
- Projects cashflow based on patterns
- Generates multiple scenarios
- Computes confidence intervals
- Handles insufficient data state

### Definition of Done
- Service returns correct projections
- Edge cases handled
- Tests pass
- mypy strict passes

### Rollback Strategy
Remove service file.

### Atomic TODOs
1. Create `ForecastService` class
2. Implement `get_net_worth_projection` method
3. Implement `get_cashflow_projection` method
4. Implement `get_scenarios` method
5. Implement `get_insights` method
6. Add trend extrapolation logic
7. Add confidence interval calculation
8. Add scenario generation logic
9. Add insufficient data handling
10. Add error handling
11. Create unit tests
12. Add integration tests

---

## Capability 21: Forecast Benchmark Validation

### Goal
Validate forecast workspace against Stage 4 benchmark.

### Dependencies
All capabilities 1-20

### Required Files
- `docs/stage-4/benchmarks/forecast-benchmark.md`

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