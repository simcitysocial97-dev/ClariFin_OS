# W4.5 — Credit Cards Intelligence Workspace

## Overview
Real-time credit card tracking across all cards. Aggregates card details, statement summaries, outstanding balances, due dates, payment history, and rewards into a single credit card intelligence view with full explainability.

---

## Capability 1: CreditCards ViewModel

### Goal
Define the canonical ViewModel for credit card display with full explainability support.

### Dependencies
None (foundational type)

### Required Files
- `frontend/types/credit-cards-view-model.ts`

### Files to Modify
- `frontend/types/index.ts` (add export)

### Validation Criteria
- All fields typed with paise (integer) for monetary values
- Evidence chain, calculation steps, source references present
- Statement history, rewards typed correctly
- Outstanding, credit limit, due date fields present

### Definition of Done
- ViewModel compiles with strict TypeScript
- All monetary fields use `number` (paise)
- Evidence, calculation, source, confidence fields present
- Exported from types index

### Rollback Strategy
Revert file creation. No consumers exist yet.

### Atomic TODOs
1. Create `CreditCardViewModel` type with card_id, card_name, card_network, issuer
2. Add monetary fields: outstanding_paise, total_credit_limit_paise, available_credit_paise, minimum_due_paise
3. Add `CardStatement` type with statement_id, period_start, period_end, total_due_paise, minimum_due_paise, due_date, payment_status, paid_amount_paise
4. Add `CardRewards` type with reward_type, points_earned, points_redeemed, points_balance, expiry_date
5. Add `CardSpendingByCategory` type with category, amount_paise, percentage, transaction_count
6. Add `EvidenceChain` type with summary, evidence array, calculation steps, source references
7. Add `ConfidenceScore` type with score (0-100), factors array
8. Add `CreditCardInsight` type with type, severity, message, action_url
9. Add `CreditCardFilters` type with card_ids, statement_period, status, category
10. Add `CreditCardNavigation` type with deep_link, cross_references
11. Add JSDoc comments for all fields
12. Create unit tests verifying type structure
13. Export from `frontend/types/index.ts`
14. Validate against backend DTO structure
15. Add invariant tests (outstanding + available = credit_limit)

---

## Capability 2: CreditCards Mapper

### Goal
Transform backend DTO to CreditCardViewModel with full evidence mapping.

### Dependencies
Capability 1 (CreditCardViewModel)

### Required Files
- `frontend/lib/mappers/credit-cards-mapper.ts`

### Files to Modify
- `frontend/lib/mappers/index.ts` (add export)

### Validation Criteria
- All DTO fields mapped to ViewModel
- Monetary values converted to paise
- Statement history mapped correctly
- Rewards mapped correctly
- Evidence chain preserved
- Empty/null handling for missing data

### Definition of Done
- Mapper compiles with strict TypeScript
- All transformation functions tested
- Edge cases handled (null, empty, partial data)
- Performance: map 100 cards under 50ms

### Rollback Strategy
Remove mapper file and index export. No consumers yet.

### Atomic TODOs
1. Create `mapCreditCardDTO` function signature
2. Implement card details mapping
3. Implement statement history mapping
4. Implement rewards mapping
5. Implement spending by category mapping
6. Implement utilization calculation mapping
7. Implement evidence chain mapping
8. Implement confidence score mapping
9. Implement insight mapping
10. Add null/empty handling for all fields
11. Add date formatting for statement periods and due dates
12. Add amount formatting (paise to display)
13. Create unit tests for all mapping functions
14. Add performance test (100 cards under 50ms)
15. Add integration test with mock API response
16. Export from mappers index

---

## Capability 3: CreditCards Capability Hook

### Goal
Provide credit card data, filters, and actions to workspace components.

### Dependencies
Capability 1, Capability 2

### Required Files
- `frontend/lib/capabilities/use-credit-cards-capability.ts`
- `frontend/lib/capabilities/credit-cards-context.tsx`

### Files to Modify
- `frontend/lib/capabilities/index.ts` (add export)

### Validation Criteria
- Hook returns ViewModel, loading, error, filters, actions
- React Query integration for caching
- Filter/sort/group actions work correctly
- Evidence drawer toggle works
- Statement navigation works

### Definition of Done
- Hook compiles with strict TypeScript
- All actions tested
- Loading/error states managed
- React Query cache configured

### Rollback Strategy
Remove capability files and index export. No consumers yet.

### Atomic TODOs
1. Create `CreditCardsContext` with state and actions
2. Create `CreditCardsProvider` component
3. Implement `useCreditCardsCapability` hook
4. Add `fetchCreditCards` action with React Query
5. Add `fetchCardDetails` action for single card
6. Add `fetchStatements` action
7. Add `fetchSpendingByCategory` action
8. Add `fetchRewards` action
9. Add `filterByCard` action
10. Add `filterByStatementPeriod` action
11. Add `filterByStatus` action
12. Add `filterByCategory` action
13. Add `toggleEvidenceDrawer` action
14. Add `refreshCreditCards` action
15. Add loading state management
16. Add error state management
17. Add retry action for failed operations
18. Add React Query cache configuration
19. Add query key constants
20. Create unit tests for all actions
21. Export from capabilities index

---

## Capability 4: CreditCards Summary Card

### Goal
Display total outstanding, total credit limit, utilization percentage, and next due date.

### Dependencies
Capability 3

### Required Files
- `frontend/components/credit-cards/credit-cards-summary.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows total outstanding in formatted currency
- Shows total credit limit
- Shows utilization percentage with color coding
- Shows next due date and minimum due
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
2. Add total outstanding amount display with formatting
3. Add total credit limit display
4. Add utilization percentage with color coding (green < 30%, yellow < 50%, red > 50%)
5. Add next due date display
6. Add minimum due amount display
7. Add loading skeleton state
8. Add error state with retry button
9. Add responsive styling
10. Add dark mode support
11. Add ARIA labels
12. Add keyboard navigation
13. Create unit tests
14. Add accessibility tests

---

## Capability 5: CreditCards Statement History

### Goal
Display statement list with periods, amounts, and payment status.

### Dependencies
Capability 3

### Required Files
- `frontend/components/credit-cards/statement-history.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- List of statements with period, total due, minimum due, due date
- Payment status indicator (paid, pending, overdue)
- Click to expand statement details
- Pagination for long lists
- Loading/empty/error states

### Definition of Done
- Statement list renders correctly
- Status indicators work
- Expand details works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create statement history list layout
2. Add statement row with period, total due, minimum due, due date
3. Add payment status badge (paid, pending, overdue)
4. Add expandable statement details section
5. Add pagination (12 statements per page)
6. Add loading skeleton rows
7. Add empty state (no statements)
8. Add error state
9. Add responsive layout
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 6: CreditCards Utilization Chart

### Goal
Display credit utilization rate over time as a chart.

### Dependencies
Capability 3

### Required Files
- `frontend/components/credit-cards/utilization-chart.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Line/bar chart showing utilization % over time
- Per-card utilization lines
- Combined utilization line
- Threshold lines (30%, 50%)
- Interactive tooltips
- Loading/empty/error states

### Definition of Done
- Chart renders with utilization data
- Threshold lines visible
- Tooltips show values
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create utilization chart layout
2. Add line chart for combined utilization over time
3. Add per-card utilization lines
4. Add 30% threshold line (green zone boundary)
5. Add 50% threshold line (warning zone boundary)
6. Add interactive tooltips with date and percentage
7. Add legend for card selection
8. Add loading skeleton state
9. Add empty state (no utilization history)
10. Add error state
11. Add responsive sizing
12. Add dark mode support
13. Add ARIA labels
14. Create unit tests
15. Add accessibility tests

---

## Capability 7: CreditCards Spending by Category

### Goal
Display spending breakdown by category for selected card.

### Dependencies
Capability 3

### Required Files
- `frontend/components/credit-cards/spending-by-category.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Pie/bar chart showing spending by category
- Category list with amounts and percentages
- Card selector dropdown
- Period selector
- Loading/empty/error states

### Definition of Done
- Chart renders with category data
- Card selector works
- Period selector works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create spending by category layout
2. Add card selector dropdown
3. Add period selector (current month, last month, last 3 months, custom)
4. Add pie/bar chart for category breakdown
5. Add category list with amount and percentage
6. Add color coding for each category
7. Add loading skeleton state
8. Add empty state (no spending data)
9. Add error state
10. Add responsive sizing
11. Add dark mode support
12. Add ARIA labels
13. Create unit tests
14. Add accessibility tests

---

## Capability 8: CreditCards Transaction List

### Goal
Display card transactions with evidence.

### Dependencies
Capability 3

### Required Files
- `frontend/components/credit-cards/transaction-list.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- List of transactions with date, merchant, amount, category
- Evidence icon for each transaction
- Click to expand evidence details
- Pagination for long lists
- Loading/empty/error states

### Definition of Done
- Transaction list renders correctly
- Evidence expand works
- Pagination works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create transaction list layout
2. Add transaction row with date, merchant, amount, category
3. Add evidence icon per transaction
4. Add expandable evidence details section
5. Add transaction status indicator (posted, pending, refunded)
6. Add pagination (20 items per page)
7. Add loading skeleton rows
8. Add empty state (no transactions)
9. Add error state
10. Add responsive layout
11. Add dark mode support
12. Add ARIA labels
13. Create unit tests
14. Add accessibility tests

---

## Capability 9: CreditCards Filters

### Goal
Filter credit cards by card, statement period, status, and category.

### Dependencies
Capability 3

### Required Files
- `frontend/components/credit-cards/credit-cards-filters.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Card multi-select filter
- Statement period filter
- Status filter (posted, pending, refunded, all)
- Category filter
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
2. Add card multi-select
3. Add statement period selector
4. Add status multi-select (posted, pending, refunded, all)
5. Add category multi-select
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

## Capability 10: CreditCards Search

### Goal
Search credit cards and transactions within the workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/credit-cards/credit-cards-search.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Search input with debounce
- Searches card names, merchant names, transaction references
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
3. Add search across card names, merchant names, transaction references
4. Add search results highlighting
5. Add clear button
6. Add keyboard shortcut (Ctrl+K)
7. Add empty results state
8. Add loading state
9. Add error state
10. Add responsive full-width on mobile
11. Add dark mode support
12. Add ARIA labels
13. Create unit tests
14. Add accessibility tests

---

## Capability 11: CreditCards Evidence Drawer

### Goal
Show explainability evidence for credit card calculations.

### Dependencies
Capability 3

### Required Files
- `frontend/components/credit-cards/evidence-drawer.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Drawer slides in from right
- Shows summary, evidence list, calculation chain, source references
- Confidence score displayed
- Interest/fee calculation breakdown shown
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
4. Add calculation chain view (interest, fees, rewards breakdown)
5. Add source reference links (bank statements, card agreements)
6. Add confidence score display
7. Add close button
8. Add Escape key handler
9. Add responsive full-width on mobile
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 12: CreditCards Insights Panel

### Goal
Display actionable insights about credit cards including spending alerts and payment reminders.

### Dependencies
Capability 3

### Required Files
- `frontend/components/credit-cards/insights-panel.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows insights with severity indicators
- Spending alerts (high utilization, unusual spending)
- Payment reminders (upcoming due dates)
- Rewards optimization suggestions
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
3. Add high utilization alert insight
4. Add unusual spending pattern insight
5. Add payment due reminder insight
6. Add rewards optimization suggestion insight
7. Add fee avoidance suggestion insight
8. Add action button for actionable insights
9. Add loading skeleton state
10. Add empty state (no insights)
11. Add error state
12. Add responsive layout
13. Add dark mode support
14. Add ARIA labels
15. Create unit tests
16. Add accessibility tests

---

## Capability 13: CreditCards Toolbar

### Goal
Provide toolbar with actions for credit cards workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/credit-cards/credit-cards-toolbar.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Refresh button
- Filter toggle
- Export button
- Card view toggle (list/grid)
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
5. Add card view toggle (list/grid)
6. Add active filter count badge
7. Add responsive collapse menu on mobile
8. Add dark mode support
9. Add ARIA labels
10. Add keyboard shortcuts
11. Create unit tests
12. Add accessibility tests

---

## Capability 14: CreditCards Workspace Page

### Goal
Compose all credit card components into a complete workspace page.

### Dependencies
Capabilities 1-13

### Required Files
- `frontend/app/credit-cards/page.tsx`

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
2. Add CreditCardsProvider at page level
3. Add toolbar region
4. Add summary card region
5. Add statement history region
6. Add utilization chart region
7. Add spending by category region
8. Add transaction list region
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

## Capability 15: CreditCards Loading States

### Goal
Handle all loading states for credit cards workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/credit-cards/loading-skeleton.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Skeleton matches final layout
- Summary card skeleton
- Statement list skeleton
- Chart skeleton
- Transaction list skeleton
- Animation

### Definition of Done
- All skeletons render correctly
- Animation smooth
- Responsive

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create summary card skeleton
2. Create statement list skeleton rows
3. Create utilization chart skeleton
4. Create spending by category chart skeleton
5. Create transaction list skeleton rows
6. Add pulse animation
7. Add responsive sizing
8. Add dark mode support
9. Create unit tests

---

## Capability 16: CreditCards Error States

### Goal
Handle all error states for credit cards workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/credit-cards/error-state.tsx`

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

## Capability 17: CreditCards Empty States

### Goal
Handle empty states for credit cards workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/credit-cards/empty-state.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Empty message displayed
- Action button to add credit cards
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
4. Add action button (add credit card)
5. Add help text with instructions
6. Add responsive layout
7. Add dark mode support
8. Add ARIA labels
9. Create unit tests

---

## Capability 18: CreditCards Cross-Navigation

### Goal
Enable navigation from credit cards to related workspaces.

### Dependencies
Capability 3

### Required Files
- `frontend/lib/navigation/credit-cards-navigation.ts`

### Files to Modify
- `frontend/lib/navigation/index.ts` (add export)

### Validation Criteria
- Click issuer navigates to Accounts workspace
- Click transaction navigates to Accounts workspace
- Click payment navigates to Accounts workspace
- Deep links preserve context

### Definition of Done
- All navigation paths work
- Deep links preserve filter context
- Tested

### Rollback Strategy
Remove navigation file and revert index.

### Atomic TODOs
1. Create navigation to Accounts workspace (issuer account)
2. Create navigation to Net Worth workspace
3. Create navigation to Loans workspace (if linked)
4. Add deep link context preservation
5. Add navigation breadcrumb
6. Add back button
7. Add keyboard shortcuts for navigation
8. Create unit tests
9. Export from navigation index

---

## Capability 19: CreditCards Backend DTO

### Goal
Define backend DTO for credit cards API response.

### Dependencies
None (backend)

### Required Files
- `backend/src/core/dtos/credit_cards_dto.py`

### Files to Modify
- `backend/src/core/dtos/__init__.py` (add export)

### Validation Criteria
- DTO includes all required fields
- Monetary values in paise (integer)
- Pydantic validation
- Optional fields handled
- Statement, rewards, spending DTOs present

### Definition of Done
- DTO compiles with mypy strict
- Pydantic validation works
- All fields typed correctly

### Rollback Strategy
Remove DTO file and revert __init__.py.

### Atomic TODOs
1. Create `CreditCardDTO` with card_id, name, network, issuer
2. Add `CardFinancialDTO` with outstanding_paise, credit_limit_paise, available_credit_paise, minimum_due_paise
3. Add `CardStatementDTO` with period_start, period_end, total_due_paise, minimum_due_paise, due_date, payment_status, paid_amount_paise
4. Add `CardRewardsDTO` with reward_type, points_earned, points_redeemed, points_balance, expiry_date
5. Add `CardSpendingCategoryDTO` with category, amount_paise, percentage, transaction_count
6. Add `CreditCardInsightDTO` with type, severity, message, action_url
7. Add Pydantic validators for paise fields
8. Add optional field handling
9. Add field descriptions
10. Create unit tests
11. Export from DTOs __init__

---

## Capability 20: CreditCards Backend Router

### Goal
Create API endpoints for credit cards data.

### Dependencies
Capability 19

### Required Files
- `backend/src/routers/credit_cards_router.py`

### Files to Modify
- `backend/src/api.py` (register router)

### Validation Criteria
- GET /api/v1/credit-cards returns all cards
- GET /api/v1/credit-cards/{id} returns single card details
- GET /api/v1/credit-cards/{id}/statements returns statements
- GET /api/v1/credit-cards/{id}/spending returns spending by category
- GET /api/v1/credit-cards/{id}/rewards returns rewards
- GET /api/v1/credit-cards/{id}/insights returns insights
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
2. Add GET /credit-cards endpoint with filtering
3. Add GET /credit-cards/{id} endpoint
4. Add GET /credit-cards/{id}/statements endpoint
5. Add GET /credit-cards/{id}/spending endpoint
6. Add GET /credit-cards/{id}/rewards endpoint
7. Add GET /credit-cards/{id}/insights endpoint
8. Add query parameter handling (card_ids, statement_period, status, category)
9. Add error handling for missing card
10. Add response models
11. Add tags and metadata
12. Create unit tests
13. Register router in api.py

---

## Capability 21: CreditCards Benchmark Validation

### Goal
Validate credit cards workspace against Stage 4 benchmark.

### Dependencies
All capabilities 1-20

### Required Files
- `docs/stage-4/benchmarks/credit-cards-benchmark.md`

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
