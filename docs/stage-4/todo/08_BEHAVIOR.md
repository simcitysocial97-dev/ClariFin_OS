# W4.8 — Behaviour Intelligence Workspace

## Overview
Real-time financial behaviour analysis. Shows behaviour score, spending patterns, savings rate, debt health, and wellness metrics with full explainability.

---

## Capability 1: Behaviour ViewModel

### Goal
Define the canonical ViewModel for behaviour display with full explainability support.

### Dependencies
None (foundational type)

### Required Files
- `frontend/types/behaviour-view-model.ts`

### Files to Modify
- `frontend/types/index.ts` (add export)

### Validation Criteria
- All monetary fields in paise (integer)
- Score, patterns, metrics, wellness typed correctly
- Evidence chain, calculation steps, source references present

### Definition of Done
- ViewModel compiles with strict TypeScript
- All monetary fields use `number` (paise)
- Evidence, calculation, source, confidence fields present
- Exported from types index

### Rollback Strategy
Revert file creation. No consumers exist yet.

### Atomic TODOs
1. Create `BehaviourViewModel` type with overall_score, score_breakdown, wellness_dimensions
2. Add `BehaviourScore` type with score (0-100), trend, category_scores array
3. Add `SpendingPattern` type with category, trend, monthly_average_paise, volatility, anomalies
4. Add `SavingsRate` type with rate_percentage, trend, target_percentage, gap_paise
5. Add `DebtHealth` type with debt_to_income_ratio, credit_utilization, trend, status
6. Add `WellnessDimension` type with name, score (0-100), description, trend
7. Add `EvidenceChain` type with summary, evidence array, calculation steps, source references
8. Add `ConfidenceScore` type with score (0-100), factors array
9. Add `BehaviourInsight` type with type, severity, message, action_url
10. Add `BehaviourFilters` type with period, categories, metric_types
11. Add JSDoc comments for all fields
12. Create unit tests verifying type structure
13. Export from `frontend/types/index.ts`
14. Validate against backend DTO structure
15. Add invariant tests (score between 0-100)

---

## Capability 2: Behaviour Mapper

### Goal
Transform backend DTO to BehaviourViewModel with full evidence mapping.

### Dependencies
Capability 1 (BehaviourViewModel)

### Required Files
- `frontend/lib/mappers/behaviour-mapper.ts`

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
- Performance: map 1000 patterns under 50ms

### Rollback Strategy
Remove mapper file and index export.

### Atomic TODOs
1. Create `mapBehaviourDTO` function signature
2. Implement score mapping
3. Implement spending pattern mapping
4. Implement savings rate mapping
5. Implement debt health mapping
6. Implement wellness dimension mapping
7. Implement evidence chain mapping
8. Implement confidence score mapping
9. Implement insight mapping
10. Add null/empty handling for all fields
11. Add date formatting for patterns
12. Add amount formatting (paise to display)
13. Create unit tests for all mapping functions
14. Add performance test (1000 patterns under 50ms)
15. Add integration test with mock API response
16. Export from mappers index

---

## Capability 3: Behaviour Capability Hook

### Goal
Provide behaviour data, filters, and actions to workspace components.

### Dependencies
Capability 1, Capability 2

### Required Files
- `frontend/lib/capabilities/use-behaviour-capability.ts`
- `frontend/lib/capabilities/behaviour-context.tsx`

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
1. Create `BehaviourContext` with state and actions
2. Create `BehaviourProvider` component
3. Implement `useBehaviourCapability` hook
4. Add `fetchBehaviourScore` action with React Query
5. Add `fetchSpendingPatterns` action
6. Add `fetchSavingsRate` action
7. Add `fetchDebtHealth` action
8. Add `fetchWellnessMetrics` action
9. Add `filterByPeriod` action
10. Add `filterByCategory` action
11. Add `filterByMetricType` action
12. Add `toggleEvidenceDrawer` action
13. Add `refreshBehaviour` action
14. Add loading state management
15. Add error state management
16. Add retry action for failed operations
17. Add React Query cache configuration
18. Add query key constants
19. Create unit tests for all actions
20. Export from capabilities index

---

## Capability 4: Behaviour Score Card

### Goal
Display overall behaviour score with trend and category breakdown.

### Dependencies
Capability 3

### Required Files
- `frontend/components/behaviour/score-card.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows overall score (0-100) with gauge or circular display
- Shows trend direction
- Shows category breakdown scores
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
1. Create score card layout
2. Add overall score gauge/circular display
3. Add score label and color coding
4. Add trend direction indicator
5. Add category breakdown bars or list
6. Add loading skeleton state
7. Add error state with retry button
8. Add responsive styling
9. Add dark mode support
10. Add ARIA labels
11. Add keyboard navigation
12. Create unit tests
13. Add accessibility tests

---

## Capability 5: Behaviour Spending Patterns Chart

### Goal
Visualize spending pattern analysis over time.

### Dependencies
Capability 3

### Required Files
- `frontend/components/behaviour/spending-patterns.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Chart showing spending trends by category
- Anomaly highlighting
- Period comparison
- Interactive tooltips
- Loading/empty/error states

### Definition of Done
- Chart renders with pattern data
- Anomalies highlighted
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create spending patterns layout
2. Add chart for spending by category over time
3. Add anomaly highlighting with visual markers
4. Add period comparison overlay
5. Add interactive tooltips with values
6. Add loading skeleton state
7. Add empty state (no patterns)
8. Add error state
9. Add responsive sizing
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 6: Behaviour Savings Rate Chart

### Goal
Show savings rate trend with target comparison.

### Dependencies
Capability 3

### Required Files
- `frontend/components/behaviour/savings-rate.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Line chart showing savings rate over time
- Target line overlay
- Gap indicator
- Interactive tooltips
- Loading/empty/error states

### Definition of Done
- Chart renders with savings data
- Target comparison works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create savings rate layout
2. Add line chart for savings rate over time
3. Add target line overlay
4. Add gap indicator (difference from target)
5. Add interactive tooltips with values
6. Add loading skeleton state
7. Add empty state (no data)
8. Add error state
9. Add responsive sizing
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 7: Behaviour Debt Health Chart

### Goal
Show debt-to-income ratio and credit utilization trend.

### Dependencies
Capability 3

### Required Files
- `frontend/components/behaviour/debt-health.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Chart showing DTI ratio trend
- Credit utilization trend
- Healthy/unhealthy threshold lines
- Interactive tooltips
- Loading/empty/error states

### Definition of Done
- Chart renders with debt data
- Threshold comparisons work
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create debt health layout
2. Add chart for DTI ratio over time
3. Add credit utilization trend line
4. Add healthy/unhealthy threshold lines
5. Add interactive tooltips with values
6. Add loading skeleton state
7. Add empty state (no data)
8. Add error state
9. Add responsive sizing
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 8: Behaviour Wellness Radar

### Goal
Show multi-dimensional wellness score visualization.

### Dependencies
Capability 3

### Required Files
- `frontend/components/behaviour/wellness-radar.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Radar/spider chart with wellness dimensions
- Score labels on each axis
- Previous period overlay
- Interactive legend
- Loading/empty/error states

### Definition of Done
- Radar chart renders with dimensions
- Period comparison works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create wellness radar layout
2. Add radar/spider chart with wellness dimensions
3. Add score labels on each axis
4. Add previous period overlay
5. Add interactive legend
6. Add loading skeleton state
7. Add empty state (no dimensions)
8. Add error state
9. Add responsive sizing
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 9: Behaviour Filters

### Goal
Filter behaviour view by period, category, and metric type.

### Dependencies
Capability 3

### Required Files
- `frontend/components/behaviour/behaviour-filters.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Period filter (1M, 3M, 6M, 1Y)
- Category filter
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
2. Add period selector (1M, 3M, 6M, 1Y)
3. Add category multi-select
4. Add metric type filter (score, patterns, savings, debt)
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

## Capability 10: Behaviour Search

### Goal
Search patterns and insights within behaviour view.

### Dependencies
Capability 3

### Required Files
- `frontend/components/behaviour/behaviour-search.tsx`

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

## Capability 11: Behaviour Evidence Drawer

### Goal
Show explainability evidence for behaviour score and patterns.

### Dependencies
Capability 3

### Required Files
- `frontend/components/behaviour/evidence-drawer.tsx`

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

## Capability 12: Behaviour Insights Panel

### Goal
Display actionable recommendations for behaviour improvement.

### Dependencies
Capability 3

### Required Files
- `frontend/components/behaviour/insights-panel.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows recommendations with priority indicators
- Each recommendation has message and action
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
2. Add recommendation card with priority icon
3. Add recommendation message display
4. Add action button for each recommendation
5. Add loading skeleton state
6. Add empty state (no recommendations)
7. Add error state
8. Add responsive layout
9. Add dark mode support
10. Add ARIA labels
11. Create unit tests
12. Add accessibility tests

---

## Capability 13: Behaviour Workspace Page

### Goal
Compose all behaviour components into a complete workspace page.

### Dependencies
Capabilities 1-12

### Required Files
- `frontend/app/behaviour/page.tsx`

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
2. Add BehaviourProvider at page level
3. Add toolbar region
4. Add score card region
5. Add spending patterns chart region
6. Add savings rate chart region
7. Add debt health chart region
8. Add wellness radar region
9. Add insights panel region
10. Add evidence drawer region
11. Add workspace loading state
12. Add workspace error state
13. Add workspace empty state
14. Add URL state persistence for filters
15. Add responsive layout
16. Add dark mode support
17. Add keyboard navigation
18. Add ARIA landmarks
19. Create workspace integration tests
20. Create accessibility tests
21. Add navigation route to config

---

## Capability 14: Behaviour Loading States

### Goal
Handle all loading states for behaviour workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/behaviour/loading-skeleton.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Skeleton matches final layout
- Score card skeleton
- Chart skeletons
- Radar skeleton
- Animation

### Definition of Done
- All skeletons render correctly
- Animation smooth
- Responsive

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create score card skeleton
2. Create spending patterns chart skeleton
3. Create savings rate chart skeleton
4. Create debt health chart skeleton
5. Create wellness radar skeleton
6. Add pulse animation
7. Add responsive sizing
8. Add dark mode support
9. Create unit tests

---

## Capability 15: Behaviour Error States

### Goal
Handle all error states for behaviour workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/behaviour/error-state.tsx`

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

## Capability 16: Behaviour Empty States

### Goal
Handle empty states for behaviour workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/behaviour/empty-state.tsx`

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

## Capability 17: Behaviour Cross-Navigation

### Goal
Enable navigation from behaviour to related workspaces.

### Dependencies
Capability 3

### Required Files
- `frontend/lib/navigation/behaviour-navigation.ts`

### Files to Modify
- `frontend/lib/navigation/index.ts` (add export)

### Validation Criteria
- Click category navigates to Cashflow workspace
- Click account navigates to Accounts workspace
- Click debt metric navigates to Loans workspace
- Deep links preserve context

### Definition of Done
- All navigation paths work
- Deep links preserve filter context
- Tested

### Rollback Strategy
Remove navigation file and revert index.

### Atomic TODOs
1. Create navigation to Cashflow workspace
2. Create navigation to Accounts workspace
3. Create navigation to Loans workspace
4. Add deep link context preservation
5. Add navigation breadcrumb
6. Add back button
7. Add keyboard shortcuts for navigation
8. Create unit tests
9. Export from navigation index

---

## Capability 18: Behaviour Backend DTO

### Goal
Define backend DTO for behaviour API response.

### Dependencies
None (backend)

### Required Files
- `backend/src/core/dtos/behaviour_dto.py`

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
1. Create `BehaviourScoreDTO` with overall_score, trend, category_scores
2. Add `SpendingPatternDTO` with category, trend, monthly_average_paise, volatility
3. Add `SavingsRateDTO` with rate_percentage, trend, target_percentage
4. Add `DebtHealthDTO` with dti_ratio, credit_utilization, trend, status
5. Add `WellnessDimensionDTO` with name, score, description, trend
6. Add `BehaviourInsightDTO` with type, severity, message, action_url
7. Add Pydantic validators for score ranges (0-100)
8. Add optional field handling
9. Add field descriptions
10. Create unit tests
11. Export from DTOs __init__

---

## Capability 19: Behaviour Backend Router

### Goal
Create API endpoints for behaviour data.

### Dependencies
Capability 18

### Required Files
- `backend/src/routers/behaviour_router.py` (modify existing)

### Files to Modify
- `backend/src/api.py` (ensure registration)

### Validation Criteria
- GET /api/v1/behaviour/score returns behaviour score
- GET /api/v1/behaviour/patterns returns spending patterns
- GET /api/v1/behaviour/savings returns savings rate
- GET /api/v1/behaviour/debt returns debt health
- GET /api/v1/behaviour/wellness returns wellness metrics
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
2. Add GET /behaviour/score endpoint
3. Add GET /behaviour/patterns endpoint
4. Add GET /behaviour/savings endpoint
5. Add GET /behaviour/debt endpoint
6. Add GET /behaviour/wellness endpoint
7. Add query parameter handling (period, categories)
8. Add error handling for missing data
9. Add response models
10. Add tags and metadata
11. Create unit tests
12. Ensure registered in api.py

---

## Capability 20: Behaviour Backend Service

### Goal
Implement business logic for behaviour calculations.

### Dependencies
Capability 18, Capability 19

### Required Files
- `backend/src/services/behaviour_service.py`

### Files to Modify
None (new file)

### Validation Criteria
- Computes behaviour score from spending/savings/debt data
- Analyzes spending patterns
- Calculates savings rate
- Assesses debt health
- Generates wellness metrics
- Handles empty transaction state

### Definition of Done
- Service returns correct calculations
- Edge cases handled
- Tests pass
- mypy strict passes

### Rollback Strategy
Remove service file.

### Atomic TODOs
1. Create `BehaviourService` class
2. Implement `get_score` method
3. Implement `get_spending_patterns` method
4. Implement `get_savings_rate` method
5. Implement `get_debt_health` method
6. Implement `get_wellness_metrics` method
7. Implement `get_insights` method
8. Add score calculation logic
9. Add pattern detection logic
10. Add empty state handling
11. Add error handling
12. Create unit tests
13. Add integration tests

---

## Capability 21: Behaviour Benchmark Validation

### Goal
Validate behaviour workspace against Stage 4 benchmark.

### Dependencies
All capabilities 1-20

### Required Files
- `docs/stage-4/benchmarks/behaviour-benchmark.md`

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