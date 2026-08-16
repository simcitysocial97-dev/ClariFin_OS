# W4.3 — Accounts Intelligence Workspace

## Overview
Real-time account intelligence across all financial accounts. Shows balances, transaction history, account type breakdown, and trends with full explainability.

---

## Capability 1: Accounts ViewModel

### Goal
Define the canonical ViewModel for accounts display with full explainability support.

### Dependencies
None (foundational type)

### Required Files
- `frontend/types/accounts-view-model.ts`

### Files to Modify
- `frontend/types/index.ts` (add export)

### Validation Criteria
- All monetary fields in paise (integer)
- Account details, balance history, transaction types typed correctly
- Evidence chain, calculation steps, source references present

### Definition of Done
- ViewModel compiles with strict TypeScript
- All monetary fields use `number` (paise)
- Evidence, calculation, source, confidence fields present
- Exported from types index

### Rollback Strategy
Revert file creation. No consumers exist yet.

### Atomic TODOs
1. Create `AccountsViewModel` type with accounts array, total_balance_paise, account_count
2. Add `AccountDetail` type with id, name, type, institution, balance_paise, currency, status
3. Add `BalanceHistory` type with date, balance_paise, account_id
4. Add `AccountTransaction` type with id, date, description, amount_paise, category, merchant
5. Add `AccountTypeBreakdown` type with type, count, total_balance_paise, percentage
6. Add `EvidenceChain` type with summary, evidence array, calculation steps, source references
7. Add `ConfidenceScore` type with score (0-100), factors array
8. Add `AccountInsight` type with type, severity, message, action_url
9. Add `AccountFilters` type with account_types, institutions, statuses, date_range, balance_range
10. Add JSDoc comments for all fields
11. Create unit tests verifying type structure
12. Export from `frontend/types/index.ts`
13. Validate against backend DTO structure
14. Add invariant tests (sum of account balances = total_balance)

---

## Capability 2: Accounts Mapper

### Goal
Transform backend DTO to AccountsViewModel with full evidence mapping.

### Dependencies
Capability 1 (AccountsViewModel)

### Required Files
- `frontend/lib/mappers/accounts-mapper.ts`

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
1. Create `mapAccountsDTO` function signature
2. Implement account detail mapping
3. Implement balance history mapping
4. Implement transaction mapping
5. Implement type breakdown mapping
6. Implement evidence chain mapping
7. Implement confidence score mapping
8. Implement insight mapping
9. Add null/empty handling for all fields
10. Add date formatting for balance history
11. Add amount formatting (paise to display)
12. Create unit tests for all mapping functions
13. Add performance test (1000 accounts under 50ms)
14. Add integration test with mock API response
15. Export from mappers index

---

## Capability 3: Accounts Capability Hook

### Goal
Provide accounts data, filters, and actions to workspace components.

### Dependencies
Capability 1, Capability 2

### Required Files
- `frontend/lib/capabilities/use-accounts-capability.ts`
- `frontend/lib/capabilities/accounts-context.tsx`

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
1. Create `AccountsContext` with state and actions
2. Create `AccountsProvider` component
3. Implement `useAccountsCapability` hook
4. Add `fetchAccounts` action with React Query
5. Add `fetchAccountDetail` action
6. Add `fetchBalanceHistory` action
7. Add `fetchTransactions` action
8. Add `filterByAccountType` action
9. Add `filterByInstitution` action
10. Add `filterByDateRange` action
11. Add `filterByStatus` action
12. Add `selectAccount` action
13. Add `toggleEvidenceDrawer` action
14. Add `refreshAccounts` action
15. Add loading state management
16. Add error state management
17. Add retry action for failed operations
18. Add React Query cache configuration
19. Add query key constants
20. Create unit tests for all actions
21. Export from capabilities index

---

## Capability 4: Accounts Summary Card

### Goal
Display aggregated account summary with total balance and account count.

### Dependencies
Capability 3

### Required Files
- `frontend/components/accounts/accounts-summary.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows total balance across all accounts
- Shows account count by type
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
2. Add total balance display with formatting
3. Add account count by type breakdown
4. Add period comparison text
5. Add loading skeleton state
6. Add error state with retry button
7. Add responsive styling
8. Add dark mode support
9. Add ARIA labels
10. Add keyboard navigation
11. Create unit tests
12. Add accessibility tests

---

## Capability 5: Accounts Balance Trend Chart

### Goal
Visualize balance history over time for selected account or all accounts.

### Dependencies
Capability 3

### Required Files
- `frontend/components/accounts/balance-trend.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Line chart showing balance over time
- Account selector to pick specific account
- Date range selector
- Interactive tooltips
- Loading/empty/error states

### Definition of Done
- Chart renders with balance data
- Account switching works
- Date range switching works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create balance trend chart layout
2. Add line chart for balance over time
3. Add account selector dropdown
4. Add date range selector (1M, 3M, 6M, 1Y, ALL)
5. Add interactive tooltips with date and value
6. Add loading skeleton state
7. Add empty state (no history)
8. Add error state
9. Add responsive sizing
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 6: Accounts Type Breakdown

### Goal
Show account distribution by type (savings, current, etc.).

### Dependencies
Capability 3

### Required Files
- `frontend/components/accounts/type-breakdown.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Pie or bar chart by account type
- Value and percentage labels
- Interactive legend
- Clickable to filter
- Loading/empty/error states

### Definition of Done
- Chart renders with type data
- Click to filter works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create type breakdown layout
2. Add chart (pie or bar) for account types
3. Add type name labels
4. Add balance labels
5. Add percentage labels
6. Add interactive legend
7. Add click handler to filter by type
8. Add loading skeleton state
9. Add empty state (no accounts)
10. Add error state
11. Add responsive layout
12. Add dark mode support
13. Add ARIA labels
14. Create unit tests
15. Add accessibility tests

---

## Capability 7: Accounts Transaction List

### Goal
Show transactions for selected account with sorting and pagination.

### Dependencies
Capability 3

### Required Files
- `frontend/components/accounts/transaction-list.tsx`

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

## Capability 8: Accounts Filters

### Goal
Filter accounts view by type, institution, status, and date range.

### Dependencies
Capability 3

### Required Files
- `frontend/components/accounts/accounts-filters.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Account type multi-select
- Institution filter
- Status filter (active, dormant, closed)
- Date range filter
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
2. Add account type multi-select with checkboxes
3. Add institution search/select
4. Add status filter (active/dormant/closed)
5. Add date range picker
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

## Capability 9: Accounts Search

### Goal
Search accounts and transactions within accounts view.

### Dependencies
Capability 3

### Required Files
- `frontend/components/accounts/accounts-search.tsx`

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

## Capability 10: Accounts Evidence Drawer

### Goal
Show explainability evidence for account balances and calculations.

### Dependencies
Capability 3

### Required Files
- `frontend/components/accounts/evidence-drawer.tsx`

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

## Capability 11: Accounts Insights Panel

### Goal
Display actionable insights about accounts.

### Dependencies
Capability 3

### Required Files
- `frontend/components/accounts/insights-panel.tsx`

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

## Capability 12: Accounts Toolbar

### Goal
Provide toolbar with actions for accounts workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/accounts/accounts-toolbar.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Refresh button
- Filter toggle
- Export button
- Add account button
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
5. Add add account button
6. Add active filter count badge
7. Add responsive collapse menu on mobile
8. Add dark mode support
9. Add ARIA labels
10. Add keyboard shortcuts
11. Create unit tests
12. Add accessibility tests

---

## Capability 13: Accounts Workspace Page

### Goal
Compose all accounts components into a complete workspace page.

### Dependencies
Capabilities 1-12

### Required Files
- `frontend/app/accounts/page.tsx` (modify existing)

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
2. Add AccountsProvider at page level
3. Add toolbar region
4. Add summary card region
5. Add balance trend chart region
6. Add type breakdown region
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
20. Ensure navigation route in config

---

## Capability 14: Accounts Loading States

### Goal
Handle all loading states for accounts workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/accounts/loading-skeleton.tsx`

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
2. Create balance trend chart skeleton
3. Create type breakdown skeleton
4. Create table skeleton rows
5. Add pulse animation
6. Add responsive sizing
7. Add dark mode support
8. Create unit tests

---

## Capability 15: Accounts Error States

### Goal
Handle all error states for accounts workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/accounts/error-state.tsx`

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

## Capability 16: Accounts Empty States

### Goal
Handle empty states for accounts workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/accounts/empty-state.tsx`

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
4. Add action button (add account)
5. Add help text with instructions
6. Add responsive layout
7. Add dark mode support
8. Add ARIA labels
9. Create unit tests

---

## Capability 17: Accounts Cross-Navigation

### Goal
Enable navigation from accounts to related workspaces.

### Dependencies
Capability 3

### Required Files
- `frontend/lib/navigation/accounts-navigation.ts`

### Files to Modify
- `frontend/lib/navigation/index.ts` (add export)

### Validation Criteria
- Click account navigates to Net Worth workspace
- Click transaction navigates to Cashflow workspace
- Click loan account navigates to Loans workspace
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
3. Create navigation to Loans workspace
4. Add deep link context preservation
5. Add navigation breadcrumb
6. Add back button
7. Add keyboard shortcuts for navigation
8. Create unit tests
9. Export from navigation index

---

## Capability 18: Accounts Backend DTO

### Goal
Define backend DTO for accounts API response.

### Dependencies
None (backend)

### Required Files
- `backend/src/core/dtos/accounts_dto.py`

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
1. Create `AccountsSummaryDTO` with total_balance_paise, account_count
2. Add `AccountDetailDTO` with id, name, type, institution, balance_paise, status
3. Add `BalanceHistoryDTO` with date, balance_paise, account_id
4. Add `AccountTransactionDTO` with transaction details
5. Add `AccountTypeBreakdownDTO` with type breakdown
6. Add `AccountInsightDTO` with type and severity
7. Add Pydantic validators for paise fields
8. Add optional field handling
9. Add field descriptions
10. Create unit tests
11. Export from DTOs __init__

---

## Capability 19: Accounts Backend Router

### Goal
Create API endpoints for accounts data.

### Dependencies
Capability 18

### Required Files
- `backend/src/routers/accounts_router.py` (modify existing)

### Files to Modify
- `backend/src/api.py` (ensure registration)

### Validation Criteria
- GET /api/v1/accounts returns account list
- GET /api/v1/accounts/{id} returns account detail
- GET /api/v1/accounts/{id}/transactions returns transactions
- GET /api/v1/accounts/{id}/balance-history returns balance history
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
2. Add GET /accounts endpoint
3. Add GET /accounts/{id} endpoint
4. Add GET /accounts/{id}/transactions endpoint
5. Add GET /accounts/{id}/balance-history endpoint
6. Add GET /accounts/summary endpoint
7. Add query parameter handling (type, institution, status)
8. Add error handling for missing accounts
9. Add response models
10. Add tags and metadata
11. Create unit tests
12. Ensure registered in api.py

---

## Capability 20: Accounts Backend Service

### Goal
Implement business logic for accounts calculations.

### Dependencies
Capability 18, Capability 19

### Required Files
- `backend/src/services/accounts_service.py`

### Files to Modify
None (new file)

### Validation Criteria
- Aggregates account balances
- Computes type breakdowns
- Generates balance history
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
1. Create `AccountsService` class
2. Implement `get_accounts` method
3. Implement `get_account_detail` method
4. Implement `get_balance_history` method
5. Implement `get_transactions` method
6. Implement `get_type_breakdown` method
7. Implement `get_summary` method
8. Implement `get_insights` method
9. Add account aggregation logic
10. Add empty state handling
11. Add error handling
12. Create unit tests
13. Add integration tests

---

## Capability 21: Accounts Benchmark Validation

### Goal
Validate accounts workspace against Stage 4 benchmark.

### Dependencies
All capabilities 1-20

### Required Files
- `docs/stage-4/benchmarks/accounts-benchmark.md`

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