# W4.7 — Reconciliation Intelligence Workspace

## Overview
Real-time reconciliation tracking across all accounts. Shows reconciliation status, discrepancies, audit trail, and resolution progress with full explainability.

---

## Capability 1: Reconciliation ViewModel

### Goal
Define the canonical ViewModel for reconciliation display with full explainability support.

### Dependencies
None (foundational type)

### Required Files
- `frontend/types/reconciliation-view-model.ts`

### Files to Modify
- `frontend/types/index.ts` (add export)

### Validation Criteria
- All fields typed with paise (integer) for monetary values
- Reconciliation status, discrepancy, audit trail types present
- Evidence chain, calculation steps, source references present

### Definition of Done
- ViewModel compiles with strict TypeScript
- All monetary fields use `number` (paise)
- Status, discrepancy, audit trail types defined
- Evidence, calculation, source, confidence fields present
- Exported from types index

### Rollback Strategy
Revert file creation. No consumers exist yet.

### Atomic TODOs
1. Create `ReconciliationViewModel` type with status, last_reconciled_date, total_accounts, reconciled_count, pending_count, discrepancy_count
2. Add `ReconciliationStatus` type with account_id, account_name, status, last_reconciled, discrepancy_amount_paise
3. Add `DiscrepancyDetail` type with id, account_id, amount_paise, type, status, description, created_date, resolved_date
4. Add `AuditTrailEntry` type with id, date, action, account_id, user, details, previous_status, new_status
5. Add `EvidenceChain` type with summary, evidence array, calculation steps, source references
6. Add `ConfidenceScore` type with score (0-100), factors array
7. Add `ReconciliationInsight` type with type, severity, message, action_url
8. Add `ReconciliationFilters` type with statuses, date_range, account_ids, discrepancy_types
9. Add JSDoc comments for all fields
10. Create unit tests verifying type structure
11. Export from `frontend/types/index.ts`
12. Validate against backend DTO structure
13. Add invariant tests (reconciled + pending + discrepancy = total_accounts)

---

## Capability 2: Reconciliation Mapper

### Goal
Transform backend DTO to ReconciliationViewModel with full evidence mapping.

### Dependencies
Capability 1 (ReconciliationViewModel)

### Required Files
- `frontend/lib/mappers/reconciliation-mapper.ts`

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
- Performance: map 1000 accounts under 50ms

### Rollback Strategy
Remove mapper file and index export.

### Atomic TODOs
1. Create `mapReconciliationDTO` function signature
2. Implement status overview mapping
3. Implement discrepancy detail mapping
4. Implement audit trail mapping
5. Implement evidence chain mapping
6. Implement confidence score mapping
7. Implement insight mapping
8. Add null/empty handling for all fields
9. Add date formatting for audit trail
10. Add amount formatting (paise to display)
11. Create unit tests for all mapping functions
12. Add performance test (1000 accounts under 50ms)
13. Add integration test with mock API response
14. Export from mappers index

---

## Capability 3: Reconciliation Capability Hook

### Goal
Provide reconciliation data, filters, and actions to workspace components.

### Dependencies
Capability 1, Capability 2

### Required Files
- `frontend/lib/capabilities/use-reconciliation-capability.ts`
- `frontend/lib/capabilities/reconciliation-context.tsx`

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
1. Create `ReconciliationContext` with state and actions
2. Create `ReconciliationProvider` component
3. Implement `useReconciliationCapability` hook
4. Add `fetchReconciliationStatus` action with React Query
5. Add `fetchDiscrepancies` action
6. Add `fetchAuditTrail` action
7. Add `filterByStatus` action
8. Add `filterByDateRange` action
9. Add `filterByAccount` action
10. Add `filterByDiscrepancyType` action
11. Add `selectAccount` action
12. Add `toggleEvidenceDrawer` action
13. Add `refreshReconciliation` action
14. Add loading state management
15. Add error state management
16. Add retry action for failed operations
17. Add React Query cache configuration
18. Add query key constants
19. Create unit tests for all actions
20. Export from capabilities index

---

## Capability 4: Reconciliation Summary Card

### Goal
Display reconciliation summary with counts and last reconciled date.

### Dependencies
Capability 3

### Required Files
- `frontend/components/reconciliation/reconciliation-summary.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows total accounts, reconciled, pending, discrepancy counts
- Shows last reconciliation date
- Color-coded status indicators
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
2. Add total accounts count
3. Add reconciled count with green indicator
4. Add pending count with yellow indicator
5. Add discrepancy count with red indicator
6. Add last reconciliation date
7. Add loading skeleton state
8. Add error state with retry button
9. Add responsive styling
10. Add dark mode support
11. Add ARIA labels
12. Add keyboard navigation
13. Create unit tests
14. Add accessibility tests

---

## Capability 5: Reconciliation Status Overview

### Goal
Show visual status of all accounts (reconciled/pending/discrepancy).

### Dependencies
Capability 3

### Required Files
- `frontend/components/reconciliation/status-overview.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Grid or list of accounts with status indicators
- Color-coded by status
- Clickable to filter
- Loading/empty/error states

### Definition of Done
- Overview renders with all accounts
- Click to filter works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create status overview layout
2. Add account cards with status indicators
3. Add color coding (green/yellow/red)
4. Add click handler to filter by account
5. Add loading skeleton state
6. Add empty state (no accounts)
7. Add error state
8. Add responsive grid layout
9. Add dark mode support
10. Add ARIA labels
11. Create unit tests
12. Add accessibility tests

---

## Capability 6: Reconciliation Discrepancy List

### Goal
Show detailed discrepancy list with amounts and resolution status.

### Dependencies
Capability 3

### Required Files
- `frontend/components/reconciliation/discrepancy-list.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Table with account, amount, type, status, date
- Sortable by any column
- Clickable rows open evidence
- Pagination
- Loading/empty/error states

### Definition of Done
- Table renders with discrepancies
- Sorting works
- Pagination works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create discrepancy list layout
2. Add columns: account, amount, type, status, created date, resolved date
3. Add sort controls for each column
4. Add click handler for evidence drawer
5. Add pagination controls
6. Add loading skeleton rows
7. Add empty state (no discrepancies)
8. Add error state
9. Add responsive horizontal scroll
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 7: Reconciliation Audit Trail

### Goal
Show chronological audit of reconciliation events.

### Dependencies
Capability 3

### Required Files
- `frontend/components/reconciliation/audit-trail.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Chronological timeline of events
- Event type icons
- Account and user references
- Loading/empty/error states

### Definition of Done
- Timeline renders with events
- All states handled
- Responsive
- Accessible

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create audit trail layout
2. Add timeline component with chronological ordering
3. Add event type icons
4. Add event details (date, action, account, user)
5. Add loading skeleton state
6. Add empty state (no audit events)
7. Add error state
8. Add responsive layout
9. Add dark mode support
10. Add ARIA labels
11. Create unit tests
12. Add accessibility tests

---

## Capability 8: Reconciliation Filters

### Goal
Filter reconciliation view by status, date range, account, and discrepancy type.

### Dependencies
Capability 3

### Required Files
- `frontend/components/reconciliation/reconciliation-filters.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Status filter (reconciled/pending/discrepancy)
- Date range filter
- Account multi-select
- Discrepancy type filter
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
2. Add status multi-select with checkboxes
3. Add date range picker
4. Add account multi-select
5. Add discrepancy type filter
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

## Capability 9: Reconciliation Search

### Goal
Search reconciliations and discrepancies.

### Dependencies
Capability 3

### Required Files
- `frontend/components/reconciliation/reconciliation-search.tsx`

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

## Capability 10: Reconciliation Evidence Drawer

### Goal
Show explainability evidence for reconciliation status.

### Dependencies
Capability 3

### Required Files
- `frontend/components/reconciliation/evidence-drawer.tsx`

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

## Capability 11: Reconciliation Insights Panel

### Goal
Display actionable insights about reconciliation.

### Dependencies
Capability 3

### Required Files
- `frontend/components/reconciliation/insights-panel.tsx`

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

## Capability 12: Reconciliation Toolbar

### Goal
Provide toolbar with actions for reconciliation workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/reconciliation/reconciliation-toolbar.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Refresh button
- Filter toggle
- Export button
- Run reconciliation button
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
5. Add run reconciliation button
6. Add active filter count badge
7. Add responsive collapse menu on mobile
8. Add dark mode support
9. Add ARIA labels
10. Add keyboard shortcuts
11. Create unit tests
12. Add accessibility tests

---

## Capability 13: Reconciliation Workspace Page

### Goal
Compose all reconciliation components into a complete workspace page.

### Dependencies
Capabilities 1-12

### Required Files
- `frontend/app/reconciliation/page.tsx` (modify existing)

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
2. Add ReconciliationProvider at page level
3. Add toolbar region
4. Add summary card region
5. Add status overview region
6. Add discrepancy list region
7. Add audit trail region
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

## Capability 14: Reconciliation Loading States

### Goal
Handle all loading states for reconciliation workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/reconciliation/loading-skeleton.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Skeleton matches final layout
- Summary card skeleton
- Status overview skeleton
- Table skeleton
- Timeline skeleton
- Animation

### Definition of Done
- All skeletons render correctly
- Animation smooth
- Responsive

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create summary card skeleton
2. Create status overview skeleton
3. Create discrepancy table skeleton
4. Create audit trail timeline skeleton
5. Add pulse animation
6. Add responsive sizing
7. Add dark mode support
8. Create unit tests

---

## Capability 15: Reconciliation Error States

### Goal
Handle all error states for reconciliation workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/reconciliation/error-state.tsx`

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

## Capability 16: Reconciliation Empty States

### Goal
Handle empty states for reconciliation workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/reconciliation/empty-state.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Empty message displayed
- Action button to import data
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
4. Add action button (import data)
5. Add help text with instructions
6. Add responsive layout
7. Add dark mode support
8. Add ARIA labels
9. Create unit tests

---

## Capability 17: Reconciliation Cross-Navigation

### Goal
Enable navigation from reconciliation to related workspaces.

### Dependencies
Capability 3

### Required Files
- `frontend/lib/navigation/reconciliation-navigation.ts`

### Files to Modify
- `frontend/lib/navigation/index.ts` (add export)

### Validation Criteria
- Click account navigates to Accounts workspace
- Click transaction navigates to Transactions workspace
- Deep links preserve context

### Definition of Done
- All navigation paths work
- Deep links preserve filter context
- Tested

### Rollback Strategy
Remove navigation file and revert index.

### Atomic TODOs
1. Create navigation to Accounts workspace
2. Create navigation to Transactions workspace
3. Add deep link context preservation
4. Add navigation breadcrumb
5. Add back button
6. Add keyboard shortcuts for navigation
7. Create unit tests
8. Export from navigation index

---

## Capability 18: Reconciliation Backend DTO

### Goal
Define backend DTO for reconciliation API response.

### Dependencies
None (backend)

### Required Files
- `backend/src/core/dtos/reconciliation_dto.py`

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
1. Create `ReconciliationSummaryDTO` with status counts and last_reconciled
2. Add `AccountStatusDTO` with account_id, account_name, status, discrepancy_amount_paise
3. Add `DiscrepancyDTO` with id, account_id, amount_paise, type, status, description
4. Add `AuditTrailDTO` with id, date, action, account_id, user, details
5. Add `ReconciliationInsightDTO` with type and severity
6. Add Pydantic validators for paise fields
7. Add optional field handling
8. Add field descriptions
9. Create unit tests
10. Export from DTOs __init__

---

## Capability 19: Reconciliation Backend Router

### Goal
Create API endpoints for reconciliation data.

### Dependencies
Capability 18

### Required Files
- `backend/src/routers/reconciliation_router.py` (modify existing)

### Files to Modify
- `backend/src/api.py` (ensure registration)

### Validation Criteria
- GET /api/v1/reconciliation/status returns status overview
- GET /api/v1/reconciliation/discrepancies returns discrepancy list
- GET /api/v1/reconciliation/audit-trail returns audit trail
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
2. Add GET /reconciliation/status endpoint
3. Add GET /reconciliation/discrepancies endpoint
4. Add GET /reconciliation/audit-trail endpoint
5. Add query parameter handling (status, date_range, account_id)
6. Add error handling for missing data
7. Add response models
8. Add tags and metadata
9. Create unit tests
10. Ensure registered in api.py

---

## Capability 20: Reconciliation Backend Service

### Goal
Implement business logic for reconciliation calculations.

### Dependencies
Capability 18, Capability 19

### Required Files
- `backend/src/services/reconciliation_service.py`

### Files to Modify
None (new file)

### Validation Criteria
- Aggregates reconciliation status across accounts
- Computes discrepancy analysis
- Generates audit trail
- Generates insights
- Handles empty state

### Definition of Done
- Service returns correct calculations
- Edge cases handled
- Tests pass
- mypy strict passes

### Rollback Strategy
Remove service file.

### Atomic TODOs
1. Create `ReconciliationService` class
2. Implement `get_status_overview` method
3. Implement `get_discrepancies` method
4. Implement `get_audit_trail` method
5. Implement `get_insights` method
6. Add status aggregation logic
7. Add discrepancy classification logic
8. Add empty state handling
9. Add error handling
10. Create unit tests
11. Add integration tests

---

## Capability 21: Reconciliation Benchmark Validation

### Goal
Validate reconciliation workspace against Stage 4 benchmark.

### Dependencies
All capabilities 1-20

### Required Files
- `docs/stage-4/benchmarks/reconciliation-benchmark.md`

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