# W4.4 — Loans Intelligence Workspace

## Overview
Real-time loan tracking across all active and closed loans. Aggregates loan details, EMI schedules, outstanding balances, paid amounts, and amortization schedules into a single loan intelligence view with full explainability.

---

## Capability 1: Loans ViewModel

### Goal
Define the canonical ViewModel for loan display with full explainability support.

### Dependencies
None (foundational type)

### Required Files
- `frontend/types/loans-view-model.ts`

### Files to Modify
- `frontend/types/index.ts` (add export)

### Validation Criteria
- All fields typed with paise (integer) for monetary values
- Evidence chain, calculation steps, source references present
- EMI schedule, amortization schedule typed correctly
- Outstanding, paid, total interest fields present

### Definition of Done
- ViewModel compiles with strict TypeScript
- All monetary fields use `number` (paise)
- Evidence, calculation, source, confidence fields present
- Exported from types index

### Rollback Strategy
Revert file creation. No consumers exist yet.

### Atomic TODOs
1. Create `LoanViewModel` type with loan_id, loan_name, loan_type, status
2. Add monetary fields: total_amount_paise, outstanding_paise, paid_paise, monthly_emi_paise
3. Add `LoanEMISchedule` type with emi_number, due_date, amount_paise, principal_paise, interest_paise, balance_paise, status
4. Add `LoanAmortizationEntry` type with month, principal_paise, interest_paise, balance_paise, cumulative_interest_paise
5. Add `LoanDetails` type with interest_rate, tenure_months, start_date, end_date, lender_name
6. Add `EvidenceChain` type with summary, evidence array, calculation steps, source references
7. Add `ConfidenceScore` type with score (0-100), factors array
8. Add `LoanInsight` type with type, severity, message, action_url
9. Add `LoanFilters` type with loan_type, status, date_range, interest_rate_range
10. Add `LoanNavigation` type with deep_link, cross_references
11. Add JSDoc comments for all fields
12. Create unit tests verifying type structure
13. Export from `frontend/types/index.ts`
14. Validate against backend DTO structure
15. Add invariant tests (outstanding + paid = total_amount)

---

## Capability 2: Loans Mapper

### Goal
Transform backend DTO to LoanViewModel with full evidence mapping.

### Dependencies
Capability 1 (LoanViewModel)

### Required Files
- `frontend/lib/mappers/loans-mapper.ts`

### Files to Modify
- `frontend/lib/mappers/index.ts` (add export)

### Validation Criteria
- All DTO fields mapped to ViewModel
- Monetary values converted to paise
- EMI schedule mapped correctly
- Amortization schedule mapped correctly
- Evidence chain preserved
- Empty/null handling for missing data

### Definition of Done
- Mapper compiles with strict TypeScript
- All transformation functions tested
- Edge cases handled (null, empty, partial data)
- Performance: map 100 loans under 50ms

### Rollback Strategy
Remove mapper file and index export. No consumers yet.

### Atomic TODOs
1. Create `mapLoanDTO` function signature
2. Implement loan details mapping
3. Implement EMI schedule mapping
4. Implement amortization schedule mapping
5. Implement outstanding/paid calculation mapping
6. Implement interest analysis mapping
7. Implement evidence chain mapping
8. Implement confidence score mapping
9. Implement insight mapping
10. Add null/empty handling for all fields
11. Add date formatting for EMI due dates
12. Add amount formatting (paise to display)
13. Create unit tests for all mapping functions
14. Add performance test (100 loans under 50ms)
15. Add integration test with mock API response
16. Export from mappers index

---

## Capability 3: Loans Capability Hook

### Goal
Provide loan data, filters, and actions to workspace components.

### Dependencies
Capability 1, Capability 2

### Required Files
- `frontend/lib/capabilities/use-loans-capability.ts`
- `frontend/lib/capabilities/loans-context.tsx`

### Files to Modify
- `frontend/lib/capabilities/index.ts` (add export)

### Validation Criteria
- Hook returns ViewModel, loading, error, filters, actions
- React Query integration for caching
- Filter/sort/group actions work correctly
- Evidence drawer toggle works
- EMI schedule navigation works

### Definition of Done
- Hook compiles with strict TypeScript
- All actions tested
- Loading/error states managed
- React Query cache configured

### Rollback Strategy
Remove capability files and index export. No consumers yet.

### Atomic TODOs
1. Create `LoansContext` with state and actions
2. Create `LoansProvider` component
3. Implement `useLoansCapability` hook
4. Add `fetchLoans` action with React Query
5. Add `fetchLoanDetails` action for single loan
6. Add `fetchEMISchedule` action
7. Add `fetchAmortizationSchedule` action
8. Add `filterByLoanType` action
9. Add `filterByStatus` action
10. Add `filterByDateRange` action
11. Add `filterByInterestRateRange` action
12. Add `toggleEvidenceDrawer` action
13. Add `refreshLoans` action
14. Add loading state management
15. Add error state management
16. Add retry action for failed operations
17. Add React Query cache configuration
18. Add query key constants
19. Create unit tests for all actions
20. Export from capabilities index

---

## Capability 4: Loans Summary Card

### Goal
Display total outstanding, monthly EMI, and active loans count.

### Dependencies
Capability 3

### Required Files
- `frontend/components/loans/loans-summary.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows total outstanding in formatted currency
- Shows total monthly EMI
- Shows active loans count
- Shows paid-to-total ratio
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
3. Add total monthly EMI display
4. Add active loans count badge
5. Add paid-to-total ratio progress bar
6. Add loading skeleton state
7. Add error state with retry button
8. Add responsive styling
9. Add dark mode support
10. Add ARIA labels
11. Add keyboard navigation
12. Create unit tests
13. Add accessibility tests

---

## Capability 5: Loans Amortization Schedule

### Goal
Display full amortization table with month, principal, interest, and balance.

### Dependencies
Capability 3

### Required Files
- `frontend/components/loans/amortization-schedule.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Table with month, principal, interest, balance columns
- Cumulative interest column
- Sortable by any column
- Paginated for long schedules
- Loading/empty/error states

### Definition of Done
- Table renders with amortization data
- Sorting works
- Pagination works
- All states handled

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create amortization schedule table layout
2. Add columns: month, principal_paise, interest_paise, balance_paise, cumulative_interest_paise
3. Add sort controls for each column
4. Add pagination (20 rows per page)
5. Add row highlighting for current month
6. Add loading skeleton rows
7. Add empty state (no amortization data)
8. Add error state
9. Add responsive horizontal scroll
10. Add dark mode support
11. Add ARIA labels for table
12. Create unit tests
13. Add accessibility tests

---

## Capability 6: Loans Payment Progress

### Goal
Visual progress bar and comparison chart showing loan repayment progress.

### Dependencies
Capability 3

### Required Files
- `frontend/components/loans/payment-progress.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Progress bar showing paid vs outstanding
- Percentage complete display
- Visual comparison chart (paid vs remaining)
- Color coding (green for paid, blue for outstanding)
- Loading/empty/error states

### Definition of Done
- Progress bar renders correctly
- Comparison chart renders correctly
- All states handled
- Responsive

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create payment progress layout
2. Add progress bar with paid/outstanding ratio
3. Add percentage complete label
4. Add paid amount display
5. Add outstanding amount display
6. Add visual comparison chart (stacked bar)
7. Add color coding for paid vs outstanding
8. Add loading skeleton state
9. Add empty state (no loan data)
10. Add error state
11. Add responsive sizing
12. Add dark mode support
13. Add ARIA labels
14. Create unit tests
15. Add accessibility tests

---

## Capability 7: Loans Interest Analysis

### Goal
Display total interest, interest saved on prepayment analysis.

### Dependencies
Capability 3

### Required Files
- `frontend/components/loans/interest-analysis.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows total interest payable over tenure
- Shows interest paid so far
- Shows interest saved on prepayment scenarios
- Prepayment scenario selector (6 months, 12 months, custom)
- Loading/empty/error states

### Definition of Done
- Interest analysis renders correctly
- Prepayment scenarios calculate correctly
- All states handled
- Responsive

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create interest analysis layout
2. Add total interest payable display
3. Add interest paid so far display
4. Add remaining interest display
5. Add prepayment scenario selector (6m, 12m, custom)
6. Add interest saved calculation for each scenario
7. Add visual comparison (with/without prepayment)
8. Add loading skeleton state
9. Add empty state (no loan data)
10. Add error state
11. Add responsive layout
12. Add dark mode support
13. Add ARIA labels
14. Create unit tests
15. Add accessibility tests

---

## Capability 8: Loans Transaction List

### Goal
Display EMI transactions with evidence for each payment.

### Dependencies
Capability 3

### Required Files
- `frontend/components/loans/transaction-list.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- List of EMI transactions with date, amount, principal, interest
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
2. Add transaction row with date, amount, principal, interest
3. Add evidence icon per transaction
4. Add expandable evidence details section
5. Add transaction status indicator (paid, pending, overdue)
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

## Capability 9: Loans Filters

### Goal
Filter loans by loan type, status, date range, and interest rate range.

### Dependencies
Capability 3

### Required Files
- `frontend/components/loans/loans-filters.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Loan type filter (home, auto, personal, education, other)
- Status filter (active, closed, all)
- Date range filter (start date, end date)
- Interest rate range filter (min, max)
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
2. Add loan type multi-select (home, auto, personal, education, other)
3. Add status selector (active, closed, all)
4. Add date range picker (start date, end date)
5. Add interest rate range slider (min, max)
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

## Capability 10: Loans Search

### Goal
Search loans and transactions within the workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/loans/loans-search.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Search input with debounce
- Searches loan names, lender names, transaction references
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
3. Add search across loan names, lender names, transaction references
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

## Capability 11: Loans Evidence Drawer

### Goal
Show explainability evidence for loan calculations.

### Dependencies
Capability 3

### Required Files
- `frontend/components/loans/evidence-drawer.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Drawer slides in from right
- Shows summary, evidence list, calculation chain, source references
- Confidence score displayed
- EMI calculation breakdown shown
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
4. Add calculation chain view (EMI formula breakdown)
5. Add source reference links (bank statements, agreements)
6. Add confidence score display
7. Add close button
8. Add Escape key handler
9. Add responsive full-width on mobile
10. Add dark mode support
11. Add ARIA labels
12. Create unit tests
13. Add accessibility tests

---

## Capability 12: Loans Insights Panel

### Goal
Display actionable insights about loans.

### Dependencies
Capability 3

### Required Files
- `frontend/components/loans/insights-panel.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Shows insights with severity indicators
- Prepayment suggestions with savings estimates
- Interest rate alerts
- EMI due reminders
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
3. Add prepayment suggestion insight with savings estimate
4. Add interest rate alert insight
5. Add EMI due reminder insight
6. Add loan completion forecast insight
7. Add action button for actionable insights
8. Add loading skeleton state
9. Add empty state (no insights)
10. Add error state
11. Add responsive layout
12. Add dark mode support
13. Add ARIA labels
14. Create unit tests
15. Add accessibility tests

---

## Capability 13: Loans Workspace Page

### Goal
Compose all loan components into a complete workspace page.

### Dependencies
Capabilities 1-12

### Required Files
- `frontend/app/loans/page.tsx`

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
2. Add LoansProvider at page level
3. Add toolbar region
4. Add summary card region
5. Add amortization schedule region
6. Add payment progress region
7. Add interest analysis region
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

## Capability 14: Loans Loading States

### Goal
Handle all loading states for loans workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/loans/loading-skeleton.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Skeleton matches final layout
- Summary card skeleton
- Amortization table skeleton
- Transaction list skeleton
- Chart skeleton
- Animation

### Definition of Done
- All skeletons render correctly
- Animation smooth
- Responsive

### Rollback Strategy
Remove component file.

### Atomic TODOs
1. Create summary card skeleton
2. Create amortization table skeleton rows
3. Create transaction list skeleton rows
4. Create payment progress chart skeleton
5. Create interest analysis skeleton
6. Add pulse animation
7. Add responsive sizing
8. Add dark mode support
9. Create unit tests

---

## Capability 15: Loans Error States

### Goal
Handle all error states for loans workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/loans/error-state.tsx`

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

## Capability 16: Loans Empty States

### Goal
Handle empty states for loans workspace.

### Dependencies
Capability 3

### Required Files
- `frontend/components/loans/empty-state.tsx`

### Files to Modify
None (new file)

### Validation Criteria
- Empty message displayed
- Action button to add loans
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
4. Add action button (add loan)
5. Add help text with instructions
6. Add responsive layout
7. Add dark mode support
8. Add ARIA labels
9. Create unit tests

---

## Capability 17: Loans Cross-Navigation

### Goal
Enable navigation from loans to related workspaces.

### Dependencies
Capability 3

### Required Files
- `frontend/lib/navigation/loans-navigation.ts`

### Files to Modify
- `frontend/lib/navigation/index.ts` (add export)

### Validation Criteria
- Click lender navigates to Accounts workspace
- Click loan type navigates to relevant workspace
- Click payment transaction navigates to Accounts workspace
- Deep links preserve context

### Definition of Done
- All navigation paths work
- Deep links preserve filter context
- Tested

### Rollback Strategy
Remove navigation file and revert index.

### Atomic TODOs
1. Create navigation to Accounts workspace (lender account)
2. Create navigation to Net Worth workspace
3. Create navigation to Credit Cards workspace (if linked)
4. Add deep link context preservation
5. Add navigation breadcrumb
6. Add back button
7. Add keyboard shortcuts for navigation
8. Create unit tests
9. Export from navigation index

---

## Capability 18: Loans Backend DTO

### Goal
Define backend DTO for loans API response.

### Dependencies
None (backend)

### Required Files
- `backend/src/core/dtos/loans_dto.py`

### Files to Modify
- `backend/src/core/dtos/__init__.py` (add export)

### Validation Criteria
- DTO includes all required fields
- Monetary values in paise (integer)
- Pydantic validation
- Optional fields handled
- EMI and amortization schedule DTOs present

### Definition of Done
- DTO compiles with mypy strict
- Pydantic validation works
- All fields typed correctly

### Rollback Strategy
Remove DTO file and revert __init__.py.

### Atomic TODOs
1. Create `LoanDTO` with loan_id, name, type, status
2. Add `LoanDetailsDTO` with interest_rate, tenure, start_date, end_date, lender
3. Add `LoanFinancialDTO` with total_amount_paise, outstanding_paise, paid_paise, monthly_emi_paise
4. Add `EMIScheduleEntryDTO` with emi_number, due_date, amount_paise, principal_paise, interest_paise, balance_paise, status
5. Add `AmortizationEntryDTO` with month, principal_paise, interest_paise, balance_paise, cumulative_interest_paise
6. Add `LoanInsightDTO` with type, severity, message, action_url
7. Add Pydantic validators for paise fields
8. Add optional field handling
9. Add field descriptions
10. Create unit tests
11. Export from DTOs __init__

---

## Capability 19: Loans Backend Router

### Goal
Create API endpoints for loans data.

### Dependencies
Capability 18

### Required Files
- `backend/src/routers/loans_router.py`

### Files to Modify
- `backend/src/api.py` (register router)

### Validation Criteria
- GET /api/v1/loans returns all loans
- GET /api/v1/loans/{id} returns single loan details
- GET /api/v1/loans/{id}/emi-schedule returns EMI schedule
- GET /api/v1/loans/{id}/amortization returns amortization schedule
- GET /api/v1/loans/{id}/insights returns loan insights
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
2. Add GET /loans endpoint with filtering
3. Add GET /loans/{id} endpoint
4. Add GET /loans/{id}/emi-schedule endpoint
5. Add GET /loans/{id}/amortization endpoint
6. Add GET /loans/{id}/insights endpoint
7. Add query parameter handling (loan_type, status, date_range, interest_rate_range)
8. Add error handling for missing loan
9. Add response models
10. Add tags and metadata
11. Create unit tests
12. Register router in api.py

---

## Capability 20: Loans Backend Service

### Goal
Implement business logic for loan calculations and analysis.

### Dependencies
Capability 18, Capability 19

### Required Files
- `backend/src/services/loans_service.py`

### Files to Modify
None (new file)

### Validation Criteria
- Retrieves loan data from data source
- Calculates EMI schedule using standard formula
- Generates amortization schedule
- Computes interest analysis
- Generates insights
- Handles empty loan state

### Definition of Done
- Service returns correct calculations
- Edge cases handled
- Tests pass
- mypy strict passes

### Rollback Strategy
Remove service file.

### Atomic TODOs
1. Create `LoansService` class
2. Implement `get_all_loans` method with filtering
3. Implement `get_loan_by_id` method
4. Implement `get_emi_schedule` method
5. Implement `get_amortization_schedule` method using standard formula
6. Implement `get_interest_analysis` method
7. Implement `get_insights` method
8. Add EMI calculation logic (P * r * (1+r)^n / ((1+r)^n - 1))
9. Add amortization table generation logic
10. Add prepayment scenario calculation
11. Add empty state handling
12. Add error handling
13. Create unit tests
14. Add integration tests

---

## Capability 21: Loans Benchmark Validation

### Goal
Validate loans workspace against Stage 4 benchmark.

### Dependencies
All capabilities 1-20

### Required Files
- `docs/stage-4/benchmarks/loans-benchmark.md`

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
