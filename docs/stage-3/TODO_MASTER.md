# Stage 3 — TODO Master

## Capability 1: Transaction ViewModel

S3-TVM-001
Title: Create TransactionViewModel type definition
Purpose: Define the canonical ViewModel for transaction display
Dependencies: None
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Type includes all required fields for transaction display, explainability, and navigation
Status: Pending

S3-TVM-002
Title: Add transaction summary field to ViewModel
Purpose: Provide human-readable transaction summary
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Summary field includes date, description, amount, and category
Status: Pending

S3-TVM-003
Title: Add evidence array to TransactionViewModel
Purpose: Support explainability with evidence references
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Evidence array contains source references and calculation chain
Status: Pending

S3-TVM-004
Title: Add import lineage to TransactionViewModel
Purpose: Track transaction source and import history
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Import lineage includes file reference, import date, and source details
Status: Pending

S3-TVM-005
Title: Add adjustment visibility to TransactionViewModel
Purpose: Show adjustment status and related adjustments
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Adjustment fields show is_adjusted, adjustment_id, and adjustment_reason
Status: Pending

S3-TVM-006
Title: Add relationship fields to TransactionViewModel
Purpose: Enable navigation to dependent entities
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Relationship fields include account_id, balance_id, reconciliation_id
Status: Pending

S3-TVM-007
Title: Add merchant navigation fields to TransactionViewModel
Purpose: Support merchant-based filtering and navigation
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Merchant fields include merchant_name, merchant_id, and merchant_category
Status: Pending

S3-TVM-008
Title: Add category navigation fields to TransactionViewModel
Purpose: Support category-based filtering and navigation
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Category fields include category_id, category_name, and category_path
Status: Pending

S3-TVM-009
Title: Add date navigation fields to TransactionViewModel
Purpose: Support date-based grouping and navigation
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Date fields include year, month, day, and formatted date string
Status: Pending

S3-TVM-010
Title: Add selection state fields to TransactionViewModel
Purpose: Support bulk selection and actions
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Selection fields include selected, selectable, and selection_reason
Status: Pending

S3-TVM-011
Title: Add formatted amount fields to TransactionViewModel
Purpose: Display amounts in user-friendly format
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Amount fields include formatted_amount, currency, and absolute_paise
Status: Pending

S3-TVM-012
Title: Add confidence score to TransactionViewModel
Purpose: Show categorization confidence where applicable
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Confidence field is optional number 0-100
Status: Pending

S3-TVM-013
Title: Add calculation chain to TransactionViewModel
Purpose: Enable explainability of derived values
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Calculation chain includes steps and source references
Status: Pending

S3-TVM-014
Title: Add source reference to TransactionViewModel
Purpose: Enable navigation to original data source
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Source reference includes file_id, row_number, and extraction_id
Status: Pending

S3-TVM-015
Title: Add balance reference to TransactionViewModel
Purpose: Link transactions to their account balances
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Balance reference includes balance_id and account_id
Status: Pending

S3-TVM-016
Title: Add reconciliation reference to TransactionViewModel
Purpose: Link transactions to reconciliation records
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: Reconciliation reference includes reconciliation_id and status
Status: Pending

S3-TVM-017
Title: Create TransactionViewModel index export
Purpose: Provide clean import path for ViewModel
Dependencies: S3-TVM-001
Files Expected: frontend/types/index.ts
Acceptance Criteria: TransactionViewModel exported from types index
Status: Pending

S3-TVM-018
Title: Add ViewModel unit tests
Purpose: Verify ViewModel type structure
Dependencies: S3-TVM-017
Files Expected: frontend/types/__tests__/transaction-view-model.test.ts
Acceptance Criteria: Tests verify all required fields exist
Status: Pending

S3-TVM-019
Title: Add ViewModel documentation comments
Purpose: Document field purposes and relationships
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: All fields have JSDoc comments
Status: Pending

S3-TVM-020
Title: Validate ViewModel against backend DTO
Purpose: Ensure ViewModel matches backend data structure
Dependencies: S3-TVM-001
Files Expected: frontend/types/transaction-view-model.ts
Acceptance Criteria: All backend fields mapped to ViewModel
Status: Pending

## Capability 2: Mapper Layer

S3-MAP-001
Title: Create transaction mapper interface
Purpose: Define contract for DTO to ViewModel mapping
Dependencies: S3-TVM-001
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: Interface defines mapTransaction and mapTransactions methods
Status: Pending

S3-MAP-002
Title: Implement mapTransaction function
Purpose: Convert single DTO to ViewModel
Dependencies: S3-MAP-001
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: Function transforms all DTO fields to ViewModel format
Status: Pending

S3-MAP-003
Title: Implement mapTransactions function
Purpose: Convert array of DTOs to ViewModels
Dependencies: S3-MAP-002
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: Function handles empty arrays and null values
Status: Pending

S3-MAP-004
Title: Add date formatting in mapper
Purpose: Format transaction dates for display
Dependencies: S3-MAP-002
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: Dates formatted consistently with user locale
Status: Pending

S3-MAP-005
Title: Add amount formatting in mapper
Purpose: Format transaction amounts for display
Dependencies: S3-MAP-002
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: Amounts formatted with currency symbol and proper decimals
Status: Pending

S3-MAP-006
Title: Add evidence mapping in mapper
Purpose: Transform evidence data to ViewModel format
Dependencies: S3-MAP-002
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: Evidence array properly mapped with all required fields
Status: Pending

S3-MAP-007
Title: Add import lineage mapping in mapper
Purpose: Transform import data to ViewModel format
Dependencies: S3-MAP-002
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: Import lineage includes all source references
Status: Pending

S3-MAP-008
Title: Add adjustment mapping in mapper
Purpose: Transform adjustment data to ViewModel format
Dependencies: S3-MAP-002
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: Adjustment fields correctly mapped
Status: Pending

S3-MAP-009
Title: Add relationship mapping in mapper
Purpose: Transform relationship data to ViewModel format
Dependencies: S3-MAP-002
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: All relationship fields mapped correctly
Status: Pending

S3-MAP-010
Title: Add merchant mapping in mapper
Purpose: Transform merchant data to ViewModel format
Dependencies: S3-MAP-002
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: Merchant fields correctly mapped
Status: Pending

S3-MAP-011
Title: Add category mapping in mapper
Purpose: Transform category data to ViewModel format
Dependencies: S3-MAP-002
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: Category fields correctly mapped
Status: Pending

S3-MAP-012
Title: Add selection state mapping in mapper
Purpose: Initialize selection state for transactions
Dependencies: S3-MAP-002
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: Selection fields initialized to default values
Status: Pending

S3-MAP-013
Title: Create mapper index export
Purpose: Provide clean import path for mappers
Dependencies: S3-MAP-001
Files Expected: frontend/lib/mappers/index.ts
Acceptance Criteria: All mapper functions exported from index
Status: Pending

S3-MAP-014
Title: Add mapper unit tests
Purpose: Verify mapper transformations
Dependencies: S3-MAP-013
Files Expected: frontend/lib/mappers/__tests__/transaction-mapper.test.ts
Acceptance Criteria: Tests cover all mapping scenarios
Status: Pending

S3-MAP-015
Title: Add mapper error handling
Purpose: Handle malformed DTO data gracefully
Dependencies: S3-MAP-002
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: Invalid data returns null or throws descriptive error
Status: Pending

S3-MAP-016
Title: Add mapper performance tests
Purpose: Ensure mapper handles large datasets efficiently
Dependencies: S3-MAP-014
Files Expected: frontend/lib/mappers/__tests__/transaction-mapper.performance.test.ts
Acceptance Criteria: Mapper processes 1000 transactions under 50ms
Status: Pending

S3-MAP-017
Title: Add mapper documentation
Purpose: Document mapping logic and transformations
Dependencies: S3-MAP-001
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: All functions have JSDoc comments
Status: Pending

S3-MAP-018
Title: Validate mapper against API schema
Purpose: Ensure mapper handles all API response fields
Dependencies: S3-MAP-002
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: All API fields accounted for in mapping
Status: Pending

S3-MAP-019
Title: Add mapper integration test
Purpose: Test mapper with real API responses
Dependencies: S3-MAP-014
Files Expected: frontend/lib/mappers/__tests__/transaction-mapper.integration.test.ts
Acceptance Criteria: Integration test passes with mock API data
Status: Pending

S3-MAP-020
Title: Create shared formatter utilities
Purpose: Reuse formatting logic across mappers
Dependencies: S3-MAP-001
Files Expected: frontend/lib/formatters/index.ts
Acceptance Criteria: Shared formatters for dates, amounts, and currency
Status: Pending

## Capability 3: Capability Layer

S3-CAP-001
Title: Create transaction capability context
Purpose: Define React context for transaction state
Dependencies: S3-TVM-001
Files Expected: frontend/lib/capabilities/transaction-context.tsx
Acceptance Criteria: Context provides transaction state and actions
Status: Pending

S3-CAP-002
Title: Implement useTransactionCapability hook
Purpose: Provide transaction capability to components
Dependencies: S3-CAP-001
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Hook returns transactions, filters, and actions
Status: Pending

S3-CAP-003
Title: Add fetchTransactions action to capability
Purpose: Fetch transactions from backend API
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action fetches and maps transactions using mapper
Status: Pending

S3-CAP-004
Title: Add filterTransactions action to capability
Purpose: Filter transactions by various criteria
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action filters by date, category, merchant, amount
Status: Pending

S3-CAP-005
Title: Add searchTransactions action to capability
Purpose: Search transactions by text query
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action searches description, merchant, and category
Status: Pending

S3-CAP-006
Title: Add sortTransactions action to capability
Purpose: Sort transactions by various fields
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action sorts by date, amount, description, category
Status: Pending

S3-CAP-007
Title: Add groupTransactions action to capability
Purpose: Group transactions by date, category, or merchant
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action returns grouped transaction structure
Status: Pending

S3-CAP-008
Title: Add selection state to capability
Purpose: Manage transaction selection for bulk actions
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Selection state tracks selected transaction IDs
Status: Pending

S3-CAP-009
Title: Add toggleSelection action to capability
Purpose: Toggle individual transaction selection
Dependencies: S3-CAP-008
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action toggles selection state for single transaction
Status: Pending

S3-CAP-010
Title: Add selectAll action to capability
Purpose: Select all visible transactions
Dependencies: S3-CAP-008
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action selects all transactions matching current filters
Status: Pending

S3-CAP-011
Title: Add clearSelection action to capability
Purpose: Clear all transaction selections
Dependencies: S3-CAP-008
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action clears all selected transaction IDs
Status: Pending

S3-CAP-012
Title: Add bulk action execution to capability
Purpose: Execute actions on selected transactions
Dependencies: S3-CAP-008
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Bulk actions include categorize, adjust, and delete
Status: Pending

S3-CAP-013
Title: Add pagination support to capability
Purpose: Handle large transaction datasets
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Pagination includes page, limit, and total count
Status: Pending

S3-CAP-014
Title: Add React Query integration to capability
Purpose: Cache and manage transaction data
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Query keys and cache invalidation configured
Status: Pending

S3-CAP-015
Title: Add capability index export
Purpose: Provide clean import path for capability
Dependencies: S3-CAP-001
Files Expected: frontend/lib/capabilities/index.ts
Acceptance Criteria: All capability exports available from index
Status: Pending

S3-CAP-016
Title: Add capability unit tests
Purpose: Verify capability logic
Dependencies: S3-CAP-015
Files Expected: frontend/lib/capabilities/__tests__/use-transaction-capability.test.ts
Acceptance Criteria: Tests cover all capability actions
Status: Pending

S3-CAP-017
Title: Add capability error handling
Purpose: Handle API and runtime errors gracefully
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Errors caught and exposed via state
Status: Pending

S3-CAP-018
Title: Add capability loading states
Purpose: Track loading status for all operations
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Loading states for fetch, filter, search, and sort
Status: Pending

S3-CAP-019
Title: Add capability refresh action
Purpose: Allow manual data refresh
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Refresh action invalidates cache and refetches
Status: Pending

S3-CAP-020
Title: Add capability documentation
Purpose: Document capability API and usage
Dependencies: S3-CAP-001
Files Expected: frontend/lib/capabilities/README.md
Acceptance Criteria: README documents all hooks and actions
Status: Pending

## Capability 4: Filtering Engine

S3-FIL-001
Title: Create filter types definition
Purpose: Define types for transaction filters
Dependencies: S3-TVM-001
Files Expected: frontend/lib/filters/types.ts
Acceptance Criteria: Types include date, category, merchant, amount, and status filters
Status: Pending

S3-FIL-002
Title: Create date filter component
Purpose: UI for date range filtering
Dependencies: S3-FIL-001
Files Expected: frontend/components/filters/date-filter.tsx
Acceptance Criteria: Component allows selecting date range with calendar
Status: Pending

S3-FIL-003
Title: Create category filter component
Purpose: UI for category filtering
Dependencies: S3-FIL-001
Files Expected: frontend/components/filters/category-filter.tsx
Acceptance Criteria: Component shows category tree with checkboxes
Status: Pending

S3-FIL-004
Title: Create merchant filter component
Purpose: UI for merchant filtering
Dependencies: S3-FIL-001
Files Expected: frontend/components/filters/merchant-filter.tsx
Acceptance Criteria: Component shows merchant list with search
Status: Pending

S3-FIL-005
Title: Create amount filter component
Purpose: UI for amount range filtering
Dependencies: S3-FIL-001
Files Expected: frontend/components/filters/amount-filter.tsx
Acceptance Criteria: Component allows min/max amount input
Status: Pending

S3-FIL-006
Title: Create status filter component
Purpose: UI for transaction status filtering
Dependencies: S3-FIL-001
Files Expected: frontend/components/filters/status-filter.tsx
Acceptance Criteria: Component shows status options (cleared, pending, adjusted)
Status: Pending

S3-FIL-007
Title: Create filter panel container
Purpose: Compose all filter components
Dependencies: S3-FIL-002, S3-FIL-003, S3-FIL-004, S3-FIL-005, S3-FIL-006
Files Expected: frontend/components/filters/filter-panel.tsx
Acceptance Criteria: Panel contains all filter components in layout
Status: Pending

S3-FIL-008
Title: Add filter state management
Purpose: Track active filters in capability
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Filter state includes all filter types
Status: Pending

S3-FIL-009
Title: Add applyFilters action to capability
Purpose: Apply active filters to transaction list
Dependencies: S3-FIL-008
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action filters transactions and updates state
Status: Pending

S3-FIL-010
Title: Add clearFilters action to capability
Purpose: Clear all active filters
Dependencies: S3-FIL-008
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action resets all filter values to defaults
Status: Pending

S3-FIL-011
Title: Add filter persistence to capability
Purpose: Save filter state to URL or storage
Dependencies: S3-FIL-008
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Filters persist across page reloads
Status: Pending

S3-FIL-012
Title: Add multi-filter support
Purpose: Allow multiple filters simultaneously
Dependencies: S3-FIL-008
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Multiple filters combine with AND logic
Status: Pending

S3-FIL-013
Title: Add filter validation
Purpose: Validate filter values before applying
Dependencies: S3-FIL-008
Files Expected: frontend/lib/filters/validation.ts
Acceptance Criteria: Invalid filters rejected with error message
Status: Pending

S3-FIL-014
Title: Add filter UI tests
Purpose: Verify filter component behavior
Dependencies: S3-FIL-007
Files Expected: frontend/components/filters/__tests__/filter-panel.test.tsx
Acceptance Criteria: Tests cover all filter interactions
Status: Pending

S3-FIL-015
Title: Add filter performance tests
Purpose: Ensure filtering is responsive
Dependencies: S3-FIL-014
Files Expected: frontend/lib/capabilities/__tests__/filter-performance.test.ts
Acceptance Criteria: Filter 1000 transactions under 100ms
Status: Pending

S3-FIL-016
Title: Add filter documentation
Purpose: Document filter usage and options
Dependencies: S3-FIL-001
Files Expected: frontend/lib/filters/README.md
Acceptance Criteria: README documents all filter types
Status: Pending

S3-FIL-017
Title: Add filter keyboard shortcuts
Purpose: Enable keyboard navigation for filters
Dependencies: S3-FIL-007
Files Expected: frontend/components/filters/filter-panel.tsx
Acceptance Criteria: Tab navigation and Enter to apply
Status: Pending

S3-FIL-018
Title: Add filter responsive design
Purpose: Ensure filters work on mobile
Dependencies: S3-FIL-007
Files Expected: frontend/components/filters/filter-panel.tsx
Acceptance Criteria: Filters collapse into dropdown on mobile
Status: Pending

S3-FIL-019
Title: Add filter dark mode support
Purpose: Ensure filters visible in dark mode
Dependencies: S3-FIL-007
Files Expected: frontend/components/filters/filter-panel.tsx
Acceptance Criteria: All filter components respect dark mode
Status: Pending

S3-FIL-020
Title: Add filter accessibility
Purpose: Ensure filters are screen-reader accessible
Dependencies: S3-FIL-007
Files Expected: frontend/components/filters/filter-panel.tsx
Acceptance Criteria: ARIA labels and keyboard navigation
Status: Pending

## Capability 5: Search Engine

S3-SEA-001
Title: Create search input component
Purpose: Text input for transaction search
Dependencies: None
Files Expected: frontend/components/search/transaction-search.tsx
Acceptance Criteria: Input with clear button and search icon
Status: Pending

S3-SEA-002
Title: Add search state to capability
Purpose: Track search query in capability
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Search state includes query and debounced value
Status: Pending

S3-SEA-003
Title: Add searchTransactions action
Purpose: Search transactions by query
Dependencies: S3-SEA-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action searches description, merchant, and category
Status: Pending

S3-SEA-004
Title: Add search debouncing
Purpose: Prevent excessive API calls during typing
Dependencies: S3-SEA-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: 300ms debounce on search input
Status: Pending

S3-SEA-005
Title: Add search highlighting
Purpose: Highlight search matches in results
Dependencies: S3-SEA-001
Files Expected: frontend/components/search/transaction-search.tsx
Acceptance Criteria: Matching text highlighted in transaction list
Status: Pending

S3-SEA-006
Title: Add search clear action
Purpose: Clear search query
Dependencies: S3-SEA-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action clears query and resets results
Status: Pending

S3-SEA-007
Title: Add search keyboard shortcut
Purpose: Enable quick search access
Dependencies: S3-SEA-001
Files Expected: frontend/components/search/transaction-search.tsx
Acceptance Criteria: Ctrl+K or / opens search
Status: Pending

S3-SEA-008
Title: Add search history
Purpose: Remember recent searches
Dependencies: S3-SEA-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Last 5 searches saved to localStorage
Status: Pending

S3-SEA-009
Title: Add search suggestions
Purpose: Show matching suggestions as user types
Dependencies: S3-SEA-001
Files Expected: frontend/components/search/transaction-search.tsx
Acceptance Criteria: Suggestions appear below input
Status: Pending

S3-SEA-010
Title: Add search API endpoint
Purpose: Backend endpoint for search
Dependencies: None
Files Expected: backend/src/routers/transaction_router.py
Acceptance Criteria: Endpoint accepts query and returns matching transactions
Status: Pending

S3-SEA-011
Title: Add search service
Purpose: Backend service for search logic
Dependencies: S3-SEA-010
Files Expected: backend/src/services/transaction_search_service.py
Acceptance Criteria: Service handles full-text search on transactions
Status: Pending

S3-SEA-012
Title: Add search performance tests
Purpose: Ensure search is responsive
Dependencies: S3-SEA-011
Files Expected: backend/tests/test_transaction_search.py
Acceptance Criteria: Search 10000 transactions under 200ms
Status: Pending

S3-SEA-013
Title: Add search UI tests
Purpose: Verify search component behavior
Dependencies: S3-SEA-001
Files Expected: frontend/components/search/__tests__/transaction-search.test.tsx
Acceptance Criteria: Tests cover search, clear, and keyboard shortcut
Status: Pending

S3-SEA-014
Title: Add search empty state
Purpose: Show message when no results
Dependencies: S3-SEA-001
Files Expected: frontend/components/search/transaction-search.tsx
Acceptance Criteria: "No transactions found" message displayed
Status: Pending

S3-SEA-015
Title: Add search loading state
Purpose: Show loading during search
Dependencies: S3-SEA-001
Files Expected: frontend/components/search/transaction-search.tsx
Acceptance Criteria: Spinner shown during search operation
Status: Pending

S3-SEA-016
Title: Add search error handling
Purpose: Handle search errors gracefully
Dependencies: S3-SEA-001
Files Expected: frontend/components/search/transaction-search.tsx
Acceptance Criteria: Error message shown on search failure
Status: Pending

S3-SEA-017
Title: Add search documentation
Purpose: Document search functionality
Dependencies: S3-SEA-001
Files Expected: frontend/lib/search/README.md
Acceptance Criteria: README documents search API and usage
Status: Pending

S3-SEA-018
Title: Add search responsive design
Purpose: Ensure search works on mobile
Dependencies: S3-SEA-001
Files Expected: frontend/components/search/transaction-search.tsx
Acceptance Criteria: Search expands to full width on mobile
Status: Pending

S3-SEA-019
Title: Add search dark mode support
Purpose: Ensure search visible in dark mode
Dependencies: S3-SEA-001
Files Expected: frontend/components/search/transaction-search.tsx
Acceptance Criteria: Search input respects dark mode
Status: Pending

S3-SEA-020
Title: Add search accessibility
Purpose: Ensure search is screen-reader accessible
Dependencies: S3-SEA-001
Files Expected: frontend/components/search/transaction-search.tsx
Acceptance Criteria: ARIA labels and keyboard navigation
Status: Pending

## Capability 6: Grouping

S3-GRP-001
Title: Create group types definition
Purpose: Define types for transaction grouping
Dependencies: S3-TVM-001
Files Expected: frontend/lib/groups/types.ts
Acceptance Criteria: Types include group_by and group structure
Status: Pending

S3-GRP-002
Title: Add groupByDate action to capability
Purpose: Group transactions by date
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action groups by day, week, month, or year
Status: Pending

S3-GRP-003
Title: Add groupByCategory action to capability
Purpose: Group transactions by category
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action groups by primary and subcategories
Status: Pending

S3-GRP-004
Title: Add groupByMerchant action to capability
Purpose: Group transactions by merchant
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action groups by merchant name
Status: Pending

S3-GRP-005
Title: Add groupByAmount action to capability
Purpose: Group transactions by amount range
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action groups by small, medium, large amounts
Status: Pending

S3-GRP-006
Title: Add group state to capability
Purpose: Track active grouping in capability
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Group state includes group_by and group_order
Status: Pending

S3-GRP-007
Title: Add toggleGroup action to capability
Purpose: Toggle grouping on/off
Dependencies: S3-GRP-006
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action enables/disables grouping
Status: Pending

S3-GRP-008
Title: Add group UI component
Purpose: Display grouped transactions
Dependencies: S3-GRP-001
Files Expected: frontend/components/groups/transaction-groups.tsx
Acceptance Criteria: Component shows expandable group headers
Status: Pending

S3-GRP-009
Title: Add group header component
Purpose: Display group summary information
Dependencies: S3-GRP-008
Files Expected: frontend/components/groups/group-header.tsx
Acceptance Criteria: Header shows group name and transaction count
Status: Pending

S3-GRP-010
Title: Add group expand/collapse state
Purpose: Allow users to expand/collapse groups
Dependencies: S3-GRP-008
Files Expected: frontend/components/groups/transaction-groups.tsx
Acceptance Criteria: State tracks expanded groups
Status: Pending

S3-GRP-011
Title: Add group all action
Purpose: Expand all groups at once
Dependencies: S3-GRP-010
Files Expected: frontend/components/groups/transaction-groups.tsx
Acceptance Criteria: Action expands all groups
Status: Pending

S3-GRP-012
Title: Add group none action
Purpose: Collapse all groups at once
Dependencies: S3-GRP-010
Files Expected: frontend/components/groups/transaction-groups.tsx
Acceptance Criteria: Action collapses all groups
Status: Pending

S3-GRP-013
Title: Add group keyboard navigation
Purpose: Navigate groups with keyboard
Dependencies: S3-GRP-008
Files Expected: frontend/components/groups/transaction-groups.tsx
Acceptance Criteria: Arrow keys expand/collapse groups
Status: Pending

S3-GRP-014
Title: Add group performance tests
Purpose: Ensure grouping is performant
Dependencies: S3-GRP-002
Files Expected: frontend/lib/capabilities/__tests__/group-performance.test.ts
Acceptance Criteria: Group 1000 transactions under 50ms
Status: Pending

S3-GRP-015
Title: Add group UI tests
Purpose: Verify group component behavior
Dependencies: S3-GRP-008
Files Expected: frontend/components/groups/__tests__/transaction-groups.test.tsx
Acceptance Criteria: Tests cover expand, collapse, and navigation
Status: Pending

S3-GRP-016
Title: Add group documentation
Purpose: Document grouping functionality
Dependencies: S3-GRP-001
Files Expected: frontend/lib/groups/README.md
Acceptance Criteria: README documents all group types
Status: Pending

S3-GRP-017
Title: Add group responsive design
Purpose: Ensure groups work on mobile
Dependencies: S3-GRP-008
Files Expected: frontend/components/groups/transaction-groups.tsx
Acceptance Criteria: Groups stack vertically on mobile
Status: Pending

S3-GRP-018
Title: Add group dark mode support
Purpose: Ensure groups visible in dark mode
Dependencies: S3-GRP-008
Files Expected: frontend/components/groups/transaction-groups.tsx
Acceptance Criteria: Group headers respect dark mode
Status: Pending

S3-GRP-019
Title: Add group accessibility
Purpose: Ensure groups are screen-reader accessible
Dependencies: S3-GRP-008
Files Expected: frontend/components/groups/transaction-groups.tsx
Acceptance Criteria: ARIA labels for expand/collapse
Status: Pending

S3-GRP-020
Title: Add group selection support
Purpose: Allow selection within groups
Dependencies: S3-GRP-008, S3-CAP-008
Files Expected: frontend/components/groups/transaction-groups.tsx
Acceptance Criteria: Selection works within grouped view
Status: Pending

## Capability 7: Sorting

S3-SRT-001
Title: Create sort types definition
Purpose: Define types for transaction sorting
Dependencies: S3-TVM-001
Files Expected: frontend/lib/sorting/types.ts
Acceptance Criteria: Types include sort field and direction
Status: Pending

S3-SRT-002
Title: Add sort state to capability
Purpose: Track active sort in capability
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Sort state includes field and direction
Status: Pending

S3-SRT-003
Title: Add sortTransactions action to capability
Purpose: Sort transactions by field
Dependencies: S3-SRT-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action sorts by date, amount, description, category
Status: Pending

S3-SRT-004
Title: Add sort by date
Purpose: Sort transactions chronologically
Dependencies: S3-SRT-003
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Date sorting ascending and descending
Status: Pending

S3-SRT-005
Title: Add sort by amount
Purpose: Sort transactions by amount
Dependencies: S3-SRT-003
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Amount sorting ascending and descending
Status: Pending

S3-SRT-006
Title: Add sort by description
Purpose: Sort transactions alphabetically
Dependencies: S3-SRT-003
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Description sorting ascending and descending
Status: Pending

S3-SRT-007
Title: Add sort by category
Purpose: Sort transactions by category
Dependencies: S3-SRT-003
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Category sorting ascending and descending
Status: Pending

S3-SRT-008
Title: Add sort by merchant
Purpose: Sort transactions by merchant
Dependencies: S3-SRT-003
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Merchant sorting ascending and descending
Status: Pending

S3-SRT-009
Title: Add sort UI component
Purpose: Display sort controls
Dependencies: S3-SRT-001
Files Expected: frontend/components/sorting/sort-controls.tsx
Acceptance Criteria: Component shows sortable column headers
Status: Pending

S3-SRT-010
Title: Add sort indicator to UI
Purpose: Show current sort direction
Dependencies: S3-SRT-009
Files Expected: frontend/components/sorting/sort-controls.tsx
Acceptance Criteria: Visual indicator for ascending/descending
Status: Pending

S3-SRT-011
Title: Add multi-column sort support
Purpose: Allow sorting by multiple columns
Dependencies: S3-SRT-003
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Shift+Click adds secondary sort
Status: Pending

S3-SRT-012
Title: Add sort persistence
Purpose: Save sort state to URL
Dependencies: S3-SRT-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Sort state persists across reloads
Status: Pending

S3-SRT-013
Title: Add sort performance tests
Purpose: Ensure sorting is performant
Dependencies: S3-SRT-003
Files Expected: frontend/lib/capabilities/__tests__/sort-performance.test.ts
Acceptance Criteria: Sort 1000 transactions under 30ms
Status: Pending

S3-SRT-014
Title: Add sort UI tests
Purpose: Verify sort component behavior
Dependencies: S3-SRT-009
Files Expected: frontend/components/sorting/__tests__/sort-controls.test.tsx
Acceptance Criteria: Tests cover all sort interactions
Status: Pending

S3-SRT-015
Title: Add sort documentation
Purpose: Document sorting functionality
Dependencies: S3-SRT-001
Files Expected: frontend/lib/sorting/README.md
Acceptance Criteria: README documents all sort options
Status: Pending

S3-SRT-016
Title: Add sort keyboard navigation
Purpose: Navigate sort controls with keyboard
Dependencies: S3-SRT-009
Files Expected: frontend/components/sorting/sort-controls.tsx
Acceptance Criteria: Tab navigation and Enter to sort
Status: Pending

S3-SRT-017
Title: Add sort responsive design
Purpose: Ensure sort works on mobile
Dependencies: S3-SRT-009
Files Expected: frontend/components/sorting/sort-controls.tsx
Acceptance Criteria: Sort controls collapse on mobile
Status: Pending

S3-SRT-018
Title: Add sort dark mode support
Purpose: Ensure sort visible in dark mode
Dependencies: S3-SRT-009
Files Expected: frontend/components/sorting/sort-controls.tsx
Acceptance Criteria: Sort controls respect dark mode
Status: Pending

S3-SRT-019
Title: Add sort accessibility
Purpose: Ensure sort is screen-reader accessible
Dependencies: S3-SRT-009
Files Expected: frontend/components/sorting/sort-controls.tsx
Acceptance Criteria: ARIA labels for sort controls
Status: Pending

S3-SRT-020
Title: Add sort default configuration
Purpose: Set default sort order
Dependencies: S3-SRT-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Default sort is date descending
Status: Pending

## Capability 8: Selection Model

S3-SEL-001
Title: Create selection types definition
Purpose: Define types for transaction selection
Dependencies: S3-TVM-001
Files Expected: frontend/lib/selection/types.ts
Acceptance Criteria: Types include selection state and actions
Status: Pending

S3-SEL-002
Title: Add selection state to capability
Purpose: Track selected transactions
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Selection state includes selected IDs and count
Status: Pending

S3-SEL-003
Title: Add toggleSelection action
Purpose: Toggle single transaction selection
Dependencies: S3-SEL-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action adds/removes transaction from selection
Status: Pending

S3-SEL-004
Title: Add selectAll action
Purpose: Select all visible transactions
Dependencies: S3-SEL-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action selects all filtered transactions
Status: Pending

S3-SEL-005
Title: Add selectNone action
Purpose: Clear all selections
Dependencies: S3-SEL-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action clears all selected IDs
Status: Pending

S3-SEL-006
Title: Add selectPage action
Purpose: Select current page of transactions
Dependencies: S3-SEL-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action selects all transactions on current page
Status: Pending

S3-SEL-007
Title: Add selection count display
Purpose: Show number of selected transactions
Dependencies: S3-SEL-002
Files Expected: frontend/components/selection/selection-summary.tsx
Acceptance Criteria: Component shows count and clear button
Status: Pending

S3-SEL-008
Title: Add selection checkbox component
Purpose: Checkbox for individual transaction selection
Dependencies: S3-SEL-001
Files Expected: frontend/components/selection/transaction-checkbox.tsx
Acceptance Criteria: Checkbox reflects selection state
Status: Pending

S3-SEL-009
Title: Add select all checkbox
Purpose: Checkbox to select all visible transactions
Dependencies: S3-SEL-001
Files Expected: frontend/components/selection/select-all-checkbox.tsx
Acceptance Criteria: Checkbox shows indeterminate state
Status: Pending

S3-SEL-010
Title: Add selection keyboard shortcuts
Purpose: Enable keyboard selection
Dependencies: S3-SEL-002
Files Expected: frontend/lib/selection/keyboard.ts
Acceptance Criteria: Ctrl+A selects all, Escape clears
Status: Pending

S3-SEL-011
Title: Add selection persistence
Purpose: Save selection to URL
Dependencies: S3-SEL-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Selection persists across page reloads
Status: Pending

S3-SEL-012
Title: Add selection range support
Purpose: Select range of transactions
Dependencies: S3-SEL-002
Files Expected: frontend/lib/selection/range.ts
Acceptance Criteria: Shift+Click selects range
Status: Pending

S3-SEL-013
Title: Add selection validation
Purpose: Validate selection before bulk actions
Dependencies: S3-SEL-002
Files Expected: frontend/lib/selection/validation.ts
Acceptance Criteria: Invalid selections rejected
Status: Pending

S3-SEL-014
Title: Add selection UI tests
Purpose: Verify selection component behavior
Dependencies: S3-SEL-007, S3-SEL-008
Files Expected: frontend/components/selection/__tests__/selection.test.tsx
Acceptance Criteria: Tests cover all selection actions
Status: Pending

S3-SEL-015
Title: Add selection performance tests
Purpose: Ensure selection is performant
Dependencies: S3-SEL-002
Files Expected: frontend/lib/capabilities/__tests__/selection-performance.test.ts
Acceptance Criteria: Select 1000 transactions under 10ms
Status: Pending

S3-SEL-016
Title: Add selection documentation
Purpose: Document selection functionality
Dependencies: S3-SEL-001
Files Expected: frontend/lib/selection/README.md
Acceptance Criteria: README documents all selection actions
Status: Pending

S3-SEL-017
Title: Add selection responsive design
Purpose: Ensure selection works on mobile
Dependencies: S3-SEL-007
Files Expected: frontend/components/selection/selection-summary.tsx
Acceptance Criteria: Selection summary adapts to mobile
Status: Pending

S3-SEL-018
Title: Add selection dark mode support
Purpose: Ensure selection visible in dark mode
Dependencies: S3-SEL-007, S3-SEL-008
Files Expected: frontend/components/selection/*.tsx
Acceptance Criteria: All selection components respect dark mode
Status: Pending

S3-SEL-019
Title: Add selection accessibility
Purpose: Ensure selection is screen-reader accessible
Dependencies: S3-SEL-007, S3-SEL-008
Files Expected: frontend/components/selection/*.tsx
Acceptance Criteria: ARIA labels for all selection controls
Status: Pending

S3-SEL-020
Title: Add selection integration with table
Purpose: Connect selection to transaction table
Dependencies: S3-SEL-002, S3-TBL-001
Files Expected: frontend/components/transaction-table/*.tsx
Acceptance Criteria: Table checkboxes sync with selection state
Status: Pending

## Capability 9: Evidence System

S3-EVD-001
Title: Create evidence types definition
Purpose: Define types for transaction evidence
Dependencies: S3-TVM-001
Files Expected: frontend/types/evidence.ts
Acceptance Criteria: Types include evidence type and content
Status: Pending

S3-EVD-002
Title: Add evidence drawer component
Purpose: Display evidence for selected transaction
Dependencies: S3-EVD-001
Files Expected: frontend/components/evidence/evidence-drawer.tsx
Acceptance Criteria: Drawer slides in from right with evidence
Status: Pending

S3-EVD-003
Title: Add evidence summary section
Purpose: Show evidence summary at top
Dependencies: S3-EVD-002
Files Expected: frontend/components/evidence/evidence-summary.tsx
Acceptance Criteria: Summary shows key evidence points
Status: Pending

S3-EVD-004
Title: Add evidence list component
Purpose: Display list of evidence items
Dependencies: S3-EVD-002
Files Expected: frontend/components/evidence/evidence-list.tsx
Acceptance Criteria: List shows all evidence with icons
Status: Pending

S3-EVD-005
Title: Add evidence item component
Purpose: Display single evidence item
Dependencies: S3-EVD-001
Files Expected: frontend/components/evidence/evidence-item.tsx
Acceptance Criteria: Item shows type, content, and source
Status: Pending

S3-EVD-006
Title: Add evidence source link
Purpose: Navigate to evidence source
Dependencies: S3-EVD-005
Files Expected: frontend/components/evidence/evidence-item.tsx
Acceptance Criteria: Click navigates to source document
Status: Pending

S3-EVD-007
Title: Add evidence calculation view
Purpose: Show calculation chain for evidence
Dependencies: S3-EVD-002
Files Expected: frontend/components/evidence/calculation-view.tsx
Acceptance Criteria: View shows step-by-step calculation
Status: Pending

S3-EVD-008
Title: Add evidence confidence display
Purpose: Show confidence score for evidence
Dependencies: S3-EVD-002
Files Expected: frontend/components/evidence/evidence-summary.tsx
Acceptance Criteria: Confidence shown as percentage or bar
Status: Pending

S3-EVD-009
Title: Add evidence toggle action
Purpose: Open/close evidence drawer
Dependencies: S3-EVD-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Action toggles drawer open/closed
Status: Pending

S3-EVD-010
Title: Add evidence for categorization
Purpose: Show evidence for category assignment
Dependencies: S3-EVD-001
Files Expected: frontend/components/evidence/evidence-item.tsx
Acceptance Criteria: Shows rules and patterns used
Status: Pending

S3-EVD-011
Title: Add evidence for import
Purpose: Show evidence for import lineage
Dependencies: S3-EVD-001
Files Expected: frontend/components/evidence/evidence-item.tsx
Acceptance Criteria: Shows source file and row
Status: Pending

S3-EVD-012
Title: Add evidence for adjustment
Purpose: Show evidence for adjustments
Dependencies: S3-EVD-001
Files Expected: frontend/components/evidence/evidence-item.tsx
Acceptance Criteria: Shows adjustment reason and date
Status: Pending

S3-EVD-013
Title: Add evidence for balance
Purpose: Show evidence for balance impact
Dependencies: S3-EVD-001
Files Expected: frontend/components/evidence/evidence-item.tsx
Acceptance Criteria: Shows balance calculation
Status: Pending

S3-EVD-014
Title: Add evidence for reconciliation
Purpose: Show evidence for reconciliation
Dependencies: S3-EVD-001
Files Expected: frontend/components/evidence/evidence-item.tsx
Acceptance Criteria: Shows reconciliation status
Status: Pending

S3-EVD-015
Title: Add evidence drawer tests
Purpose: Verify evidence drawer behavior
Dependencies: S3-EVD-002
Files Expected: frontend/components/evidence/__tests__/evidence-drawer.test.tsx
Acceptance Criteria: Tests cover open, close, and navigation
Status: Pending

S3-EVD-016
Title: Add evidence performance tests
Purpose: Ensure evidence loads quickly
Dependencies: S3-EVD-002
Files Expected: frontend/components/evidence/__tests__/evidence-performance.test.ts
Acceptance Criteria: Evidence loads under 100ms
Status: Pending

S3-EVD-017
Title: Add evidence documentation
Purpose: Document evidence system
Dependencies: S3-EVD-001
Files Expected: frontend/lib/evidence/README.md
Acceptance Criteria: README documents all evidence types
Status: Pending

S3-EVD-018
Title: Add evidence responsive design
Purpose: Ensure evidence works on mobile
Dependencies: S3-EVD-002
Files Expected: frontend/components/evidence/evidence-drawer.tsx
Acceptance Criteria: Drawer full-width on mobile
Status: Pending

S3-EVD-019
Title: Add evidence dark mode support
Purpose: Ensure evidence visible in dark mode
Dependencies: S3-EVD-002
Files Expected: frontend/components/evidence/*.tsx
Acceptance Criteria: All evidence components respect dark mode
Status: Pending

S3-EVD-020
Title: Add evidence accessibility
Purpose: Ensure evidence is screen-reader accessible
Dependencies: S3-EVD-002
Files Expected: frontend/components/evidence/*.tsx
Acceptance Criteria: ARIA labels and keyboard navigation
Status: Pending

## Capability 10: Workspace Layout

S3-WS-001
Title: Create workspace page component
Purpose: Define main workspace page
Dependencies: S3-CAP-001
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: Page composes all workspace regions
Status: Pending

S3-WS-002
Title: Add toolbar to workspace
Purpose: Display workspace toolbar
Dependencies: S3-TBR-001
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: Toolbar at top of page
Status: Pending

S3-WS-003
Title: Add filter panel to workspace
Purpose: Display filter panel
Dependencies: S3-FIL-007
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: Filter panel below toolbar
Status: Pending

S3-WS-004
Title: Add transaction table to workspace
Purpose: Display transaction grid
Dependencies: S3-TBL-001
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: Table below filter panel
Status: Pending

S3-WS-005
Title: Add selection summary to workspace
Purpose: Display selection summary
Dependencies: S3-SEL-007
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: Summary below transaction table
Status: Pending

S3-WS-006
Title: Add insight panel to workspace
Purpose: Display transaction insights
Dependencies: S3-INS-001
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: Panel below selection summary
Status: Pending

S3-WS-007
Title: Add evidence drawer to workspace
Purpose: Display evidence drawer
Dependencies: S3-EVD-002
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: Drawer overlays workspace
Status: Pending

S3-WS-008
Title: Add action drawer to workspace
Purpose: Display bulk action drawer
Dependencies: S3-ACT-001
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: Drawer for bulk actions
Status: Pending

S3-WS-009
Title: Add workspace loading state
Purpose: Show loading during data fetch
Dependencies: S3-CAP-002
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: Loading spinner shown during fetch
Status: Pending

S3-WS-010
Title: Add workspace error state
Purpose: Show error when fetch fails
Dependencies: S3-CAP-002
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: Error message with retry button
Status: Pending

S3-WS-011
Title: Add workspace empty state
Purpose: Show message when no transactions
Dependencies: S3-CAP-002
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: "No transactions" message displayed
Status: Pending

S3-WS-012
Title: Add workspace responsive layout
Purpose: Ensure workspace works on mobile
Dependencies: S3-WS-001
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: Layout adapts to screen size
Status: Pending

S3-WS-013
Title: Add workspace dark mode support
Purpose: Ensure workspace visible in dark mode
Dependencies: S3-WS-001
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: All regions respect dark mode
Status: Pending

S3-WS-014
Title: Add workspace keyboard navigation
Purpose: Enable full keyboard navigation
Dependencies: S3-WS-001
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: Tab navigates all interactive elements
Status: Pending

S3-WS-015
Title: Add workspace accessibility
Purpose: Ensure workspace is accessible
Dependencies: S3-WS-001
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: All regions have ARIA labels
Status: Pending

S3-WS-016
Title: Add workspace scroll management
Purpose: Manage scroll position
Dependencies: S3-WS-001
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: Scroll preserved on filter change
Status: Pending

S3-WS-017
Title: Add workspace state persistence
Purpose: Save workspace state to URL
Dependencies: S3-WS-001
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: Filters, sort, and selection persist
Status: Pending

S3-WS-018
Title: Add workspace performance optimization
Purpose: Optimize workspace rendering
Dependencies: S3-WS-001
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: No unnecessary re-renders
Status: Pending

S3-WS-019
Title: Add workspace tests
Purpose: Verify workspace behavior
Dependencies: S3-WS-001
Files Expected: frontend/app/transactions/__tests__/page.test.tsx
Acceptance Criteria: Tests cover all workspace states
Status: Pending

S3-WS-020
Title: Add workspace documentation
Purpose: Document workspace usage
Dependencies: S3-WS-001
Files Expected: frontend/lib/workspace/README.md
Acceptance Criteria: README documents all regions
Status: Pending

## Capability 11: Toolbar

S3-TBR-001
Title: Create toolbar component
Purpose: Display workspace toolbar
Dependencies: None
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: Toolbar contains all action buttons
Status: Pending

S3-TBR-002
Title: Add search button to toolbar
Purpose: Open search input
Dependencies: S3-SEA-001
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: Button opens search on click
Status: Pending

S3-TBR-003
Title: Add filter toggle to toolbar
Purpose: Open/close filter panel
Dependencies: S3-FIL-007
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: Button toggles filter panel
Status: Pending

S3-TBR-004
Title: Add group toggle to toolbar
Purpose: Open/close group controls
Dependencies: S3-GRP-008
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: Button toggles grouping
Status: Pending

S3-TBR-005
Title: Add sort toggle to toolbar
Purpose: Open/close sort controls
Dependencies: S3-SRT-009
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: Button toggles sort panel
Status: Pending

S3-TBR-006
Title: Add export button to toolbar
Purpose: Export selected transactions
Dependencies: S3-SEL-002
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: Button exports CSV of selection
Status: Pending

S3-TBR-007
Title: Add refresh button to toolbar
Purpose: Refresh transaction data
Dependencies: S3-CAP-019
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: Button triggers data refresh
Status: Pending

S3-TBR-008
Title: Add settings button to toolbar
Purpose: Open workspace settings
Dependencies: None
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: Button opens settings modal
Status: Pending

S3-TBR-009
Title: Add transaction count to toolbar
Purpose: Show total transaction count
Dependencies: S3-CAP-002
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: Count updates with filters
Status: Pending

S3-TBR-010
Title: Add active filter count to toolbar
Purpose: Show number of active filters
Dependencies: S3-FIL-008
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: Badge shows count of active filters
Status: Pending

S3-TBR-011
Title: Add toolbar responsive design
Purpose: Ensure toolbar works on mobile
Dependencies: S3-TBR-001
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: Buttons collapse into menu on mobile
Status: Pending

S3-TBR-012
Title: Add toolbar dark mode support
Purpose: Ensure toolbar visible in dark mode
Dependencies: S3-TBR-001
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: All buttons respect dark mode
Status: Pending

S3-TBR-013
Title: Add toolbar keyboard shortcuts
Purpose: Enable toolbar keyboard navigation
Dependencies: S3-TBR-001
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: All buttons keyboard accessible
Status: Pending

S3-TBR-014
Title: Add toolbar accessibility
Purpose: Ensure toolbar is screen-reader accessible
Dependencies: S3-TBR-001
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: ARIA labels for all buttons
Status: Pending

S3-TBR-015
Title: Add toolbar tests
Purpose: Verify toolbar behavior
Dependencies: S3-TBR-001
Files Expected: frontend/components/toolbar/__tests__/workspace-toolbar.test.tsx
Acceptance Criteria: Tests cover all button actions
Status: Pending

S3-TBR-016
Title: Add toolbar performance tests
Purpose: Ensure toolbar renders quickly
Dependencies: S3-TBR-001
Files Expected: frontend/components/toolbar/__tests__/toolbar-performance.test.ts
Acceptance Criteria: Toolbar renders under 10ms
Status: Pending

S3-TBR-017
Title: Add toolbar documentation
Purpose: Document toolbar usage
Dependencies: S3-TBR-001
Files Expected: frontend/components/toolbar/README.md
Acceptance Criteria: README documents all buttons
Status: Pending

S3-TBR-018
Title: Add toolbar loading state
Purpose: Show loading in toolbar
Dependencies: S3-CAP-002
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: Refresh button shows spinner during load
Status: Pending

S3-TBR-019
Title: Add toolbar error state
Purpose: Show error in toolbar
Dependencies: S3-CAP-002
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: Error indicator shown on failure
Status: Pending

S3-TBR-020
Title: Add toolbar customization
Purpose: Allow toolbar configuration
Dependencies: S3-TBR-001
Files Expected: frontend/components/toolbar/workspace-toolbar.tsx
Acceptance Criteria: Toolbar accepts config for visible buttons
Status: Pending

## Capability 12: Transaction Table

S3-TBL-001
Title: Create transaction table component
Purpose: Display list of transactions
Dependencies: S3-TVM-001
Files Expected: frontend/components/transaction-table/transaction-table.tsx
Acceptance Criteria: Table shows all transaction fields
Status: Pending

S3-TBL-002
Title: Add table header component
Purpose: Display column headers
Dependencies: S3-SRT-009
Files Expected: frontend/components/transaction-table/table-header.tsx
Acceptance Criteria: Headers match ViewModel fields
Status: Pending

S3-TBL-003
Title: Add table row component
Purpose: Display single transaction row
Dependencies: S3-TVM-001
Files Expected: frontend/components/transaction-table/table-row.tsx
Acceptance Criteria: Row shows all transaction data
Status: Pending

S3-TBL-004
Title: Add table cell component
Purpose: Display single table cell
Dependencies: S3-TVM-001
Files Expected: frontend/components/transaction-table/table-cell.tsx
Acceptance Criteria: Cell formats data appropriately
Status: Pending

S3-TBL-005
Title: Add table pagination
Purpose: Handle large transaction sets
Dependencies: S3-CAP-013
Files Expected: frontend/components/transaction-table/table-pagination.tsx
Acceptance Criteria: Pagination with page size options
Status: Pending

S3-TBL-006
Title: Add table virtualization
Purpose: Optimize rendering for large sets
Dependencies: S3-TBL-001
Files Expected: frontend/components/transaction-table/transaction-table.tsx
Acceptance Criteria: Virtual scroll for 1000+ rows
Status: Pending

S3-TBL-007
Title: Add table row selection
Purpose: Enable row selection
Dependencies: S3-SEL-008
Files Expected: frontend/components/transaction-table/table-row.tsx
Acceptance Criteria: Checkbox toggles selection
Status: Pending

S3-TBL-008
Title: Add table row click action
Purpose: Open evidence on row click
Dependencies: S3-EVD-009
Files Expected: frontend/components/transaction-table/table-row.tsx
Acceptance Criteria: Click opens evidence drawer
Status: Pending

S3-TBL-009
Title: Add table empty state
Purpose: Show message when no transactions
Dependencies: S3-TBL-001
Files Expected: frontend/components/transaction-table/transaction-table.tsx
Acceptance Criteria: "No transactions" message displayed
Status: Pending

S3-TBL-010
Title: Add table loading state
Purpose: Show loading during fetch
Dependencies: S3-TBL-001
Files Expected: frontend/components/transaction-table/transaction-table.tsx
Acceptance Criteria: Skeleton rows shown during load
Status: Pending

S3-TBL-011
Title: Add table error state
Purpose: Show error when fetch fails
Dependencies: S3-TBL-001
Files Expected: frontend/components/transaction-table/transaction-table.tsx
Acceptance Criteria: Error message with retry
Status: Pending

S3-TBL-012
Title: Add table responsive design
Purpose: Ensure table works on mobile
Dependencies: S3-TBL-001
Files Expected: frontend/components/transaction-table/transaction-table.tsx
Acceptance Criteria: Horizontal scroll on mobile
Status: Pending

S3-TBL-013
Title: Add table dark mode support
Purpose: Ensure table visible in dark mode
Dependencies: S3-TBL-001
Files Expected: frontend/components/transaction-table/*.tsx
Acceptance Criteria: All table components respect dark mode
Status: Pending

S3-TBL-014
Title: Add table keyboard navigation
Purpose: Enable keyboard table navigation
Dependencies: S3-TBL-001
Files Expected: frontend/components/transaction-table/transaction-table.tsx
Acceptance Criteria: Arrow keys navigate rows
Status: Pending

S3-TBL-015
Title: Add table accessibility
Purpose: Ensure table is screen-reader accessible
Dependencies: S3-TBL-001
Files Expected: frontend/components/transaction-table/*.tsx
Acceptance Criteria: ARIA labels and roles
Status: Pending

S3-TBL-016
Title: Add table column visibility
Purpose: Allow hiding/showing columns
Dependencies: S3-TBL-002
Files Expected: frontend/components/transaction-table/table-header.tsx
Acceptance Criteria: Column menu to toggle visibility
Status: Pending

S3-TBL-017
Title: Add table column resizing
Purpose: Allow resizing columns
Dependencies: S3-TBL-002
Files Expected: frontend/components/transaction-table/table-header.tsx
Acceptance Criteria: Drag to resize columns
Status: Pending

S3-TBL-018
Title: Add table tests
Purpose: Verify table behavior
Dependencies: S3-TBL-001
Files Expected: frontend/components/transaction-table/__tests__/transaction-table.test.tsx
Acceptance Criteria: Tests cover all table states
Status: Pending

S3-TBL-019
Title: Add table performance tests
Purpose: Ensure table is performant
Dependencies: S3-TBL-001
Files Expected: frontend/components/transaction-table/__tests__/table-performance.test.ts
Acceptance Criteria: Render 1000 rows under 100ms
Status: Pending

S3-TBL-020
Title: Add table documentation
Purpose: Document table usage
Dependencies: S3-TBL-001
Files Expected: frontend/components/transaction-table/README.md
Acceptance Criteria: README documents all features
Status: Pending

## Capability 13: Navigation

S3-NAV-001
Title: Add navigation to category workspace
Purpose: Navigate to category view
Dependencies: S3-TVM-001
Files Expected: frontend/lib/navigation/category-navigation.ts
Acceptance Criteria: Link to category-based transaction view
Status: Pending

S3-NAV-002
Title: Add navigation to merchant workspace
Purpose: Navigate to merchant view
Dependencies: S3-TVM-001
Files Expected: frontend/lib/navigation/merchant-navigation.ts
Acceptance Criteria: Link to merchant-based transaction view
Status: Pending

S3-NAV-003
Title: Add navigation to date workspace
Purpose: Navigate to date view
Dependencies: S3-TVM-001
Files Expected: frontend/lib/navigation/date-navigation.ts
Acceptance Criteria: Link to date-based transaction view
Status: Pending

S3-NAV-004
Title: Add navigation to account workspace
Purpose: Navigate to account view
Dependencies: S3-TVM-001
Files Expected: frontend/lib/navigation/account-navigation.ts
Acceptance Criteria: Link to account-based transaction view
Status: Pending

S3-NAV-005
Title: Add navigation to balance workspace
Purpose: Navigate to balance view
Dependencies: S3-TVM-001
Files Expected: frontend/lib/navigation/balance-navigation.ts
Acceptance Criteria: Link to balance view
Status: Pending

S3-NAV-006
Title: Add navigation to reconciliation workspace
Purpose: Navigate to reconciliation view
Dependencies: S3-TVM-001
Files Expected: frontend/lib/navigation/reconciliation-navigation.ts
Acceptance Criteria: Link to reconciliation view
Status: Pending

S3-NAV-007
Title: Add navigation to import workspace
Purpose: Navigate to import view
Dependencies: S3-TVM-001
Files Expected: frontend/lib/navigation/import-navigation.ts
Acceptance Criteria: Link to import lineage view
Status: Pending

S3-NAV-008
Title: Add navigation to adjustment workspace
Purpose: Navigate to adjustment view
Dependencies: S3-TVM-001
Files Expected: frontend/lib/navigation/adjustment-navigation.ts
Acceptance Criteria: Link to adjustment view
Status: Pending

S3-NAV-009
Title: Add cross-navigation from table
Purpose: Enable navigation from table cells
Dependencies: S3-TBL-003
Files Expected: frontend/components/transaction-table/table-cell.tsx
Acceptance Criteria: Clickable cells navigate to related views
Status: Pending

S3-NAV-010
Title: Add navigation breadcrumb
Purpose: Show current navigation path
Dependencies: S3-NAV-001
Files Expected: frontend/components/navigation/breadcrumb.tsx
Acceptance Criteria: Breadcrumb shows current location
Status: Pending

S3-NAV-011
Title: Add navigation back button
Purpose: Allow returning to previous view
Dependencies: S3-NAV-001
Files Expected: frontend/components/navigation/back-button.tsx
Acceptance Criteria: Button navigates back in history
Status: Pending

S3-NAV-012
Title: Add navigation keyboard shortcuts
Purpose: Enable keyboard navigation
Dependencies: S3-NAV-001
Files Expected: frontend/lib/navigation/keyboard.ts
Acceptance Criteria: Alt+Arrow keys for navigation
Status: Pending

S3-NAV-013
Title: Add navigation state persistence
Purpose: Save navigation state
Dependencies: S3-NAV-001
Files Expected: frontend/lib/navigation/persistence.ts
Acceptance Criteria: Navigation state in URL
Status: Pending

S3-NAV-014
Title: Add navigation tests
Purpose: Verify navigation behavior
Dependencies: S3-NAV-001
Files Expected: frontend/lib/navigation/__tests__/navigation.test.ts
Acceptance Criteria: Tests cover all navigation paths
Status: Pending

S3-NAV-015
Title: Add navigation performance tests
Purpose: Ensure navigation is fast
Dependencies: S3-NAV-001
Files Expected: frontend/lib/navigation/__tests__/navigation-performance.test.ts
Acceptance Criteria: Navigation under 50ms
Status: Pending

S3-NAV-016
Title: Add navigation documentation
Purpose: Document navigation system
Dependencies: S3-NAV-001
Files Expected: frontend/lib/navigation/README.md
Acceptance Criteria: README documents all navigation paths
Status: Pending

S3-NAV-017
Title: Add navigation responsive design
Purpose: Ensure navigation works on mobile
Dependencies: S3-NAV-001
Files Expected: frontend/components/navigation/*.tsx
Acceptance Criteria: Navigation adapts to mobile
Status: Pending

S3-NAV-018
Title: Add navigation dark mode support
Purpose: Ensure navigation visible in dark mode
Dependencies: S3-NAV-001
Files Expected: frontend/components/navigation/*.tsx
Acceptance Criteria: All navigation components respect dark mode
Status: Pending

S3-NAV-019
Title: Add navigation accessibility
Purpose: Ensure navigation is accessible
Dependencies: S3-NAV-001
Files Expected: frontend/components/navigation/*.tsx
Acceptance Criteria: ARIA labels for all navigation
Status: Pending

S3-NAV-020
Title: Add navigation error handling
Purpose: Handle navigation errors
Dependencies: S3-NAV-001
Files Expected: frontend/lib/navigation/error-handling.ts
Acceptance Criteria: Invalid navigation shows error
Status: Pending

## Capability 14: Loading/Error States

S3-LOD-001
Title: Create loading spinner component
Purpose: Show loading state
Dependencies: None
Files Expected: frontend/components/ui/loading-spinner.tsx
Acceptance Criteria: Spinner animates while loading
Status: Pending

S3-LOD-002
Title: Create skeleton row component
Purpose: Show loading for table rows
Dependencies: None
Files Expected: frontend/components/ui/skeleton-row.tsx
Acceptance Criteria: Skeleton matches table row structure
Status: Pending

S3-LOD-003
Title: Create error message component
Purpose: Show error state
Dependencies: None
Files Expected: frontend/components/ui/error-message.tsx
Acceptance Criteria: Error shows message and retry button
Status: Pending

S3-LOD-004
Title: Create empty state component
Purpose: Show empty state
Dependencies: None
Files Expected: frontend/components/ui/empty-state.tsx
Acceptance Criteria: Empty state shows message and action
Status: Pending

S3-LOD-005
Title: Add loading state to capability
Purpose: Track loading in capability
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Loading state for all async operations
Status: Pending

S3-LOD-006
Title: Add error state to capability
Purpose: Track errors in capability
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Error state includes message and code
Status: Pending

S3-LOD-007
Title: Add retry action to capability
Purpose: Allow retrying failed operations
Dependencies: S3-LOD-006
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Retry action re-executes failed operation
Status: Pending

S3-LOD-008
Title: Add loading timeout handling
Purpose: Handle long loading times
Dependencies: S3-LOD-005
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Timeout after 30 seconds
Status: Pending

S3-LOD-009
Title: Add error recovery
Purpose: Recover from errors automatically
Dependencies: S3-LOD-006
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Auto-retry on network errors
Status: Pending

S3-LOD-010
Title: Add loading performance tests
Purpose: Ensure loading states are fast
Dependencies: S3-LOD-001
Files Expected: frontend/components/ui/__tests__/loading-performance.test.ts
Acceptance Criteria: Loading components render under 5ms
Status: Pending

S3-LOD-011
Title: Add error performance tests
Purpose: Ensure error states are fast
Dependencies: S3-LOD-003
Files Expected: frontend/components/ui/__tests__/error-performance.test.ts
Acceptance Criteria: Error components render under 5ms
Status: Pending

S3-LOD-012
Title: Add empty state performance tests
Purpose: Ensure empty states are fast
Dependencies: S3-LOD-004
Files Expected: frontend/components/ui/__tests__/empty-performance.test.ts
Acceptance Criteria: Empty components render under 5ms
Status: Pending

S3-LOD-013
Title: Add loading tests
Purpose: Verify loading behavior
Dependencies: S3-LOD-001
Files Expected: frontend/components/ui/__tests__/loading-spinner.test.tsx
Acceptance Criteria: Tests cover all loading states
Status: Pending

S3-LOD-014
Title: Add error tests
Purpose: Verify error behavior
Dependencies: S3-LOD-003
Files Expected: frontend/components/ui/__tests__/error-message.test.tsx
Acceptance Criteria: Tests cover error display
Status: Pending

S3-LOD-015
Title: Add empty state tests
Purpose: Verify empty state behavior
Dependencies: S3-LOD-004
Files Expected: frontend/components/ui/__tests__/empty-state.test.tsx
Acceptance Criteria: Tests cover empty state display
Status: Pending

S3-LOD-016
Title: Add loading documentation
Purpose: Document loading states
Dependencies: S3-LOD-001
Files Expected: frontend/components/ui/README.md
Acceptance Criteria: README documents all loading components
Status: Pending

S3-LOD-017
Title: Add loading responsive design
Purpose: Ensure loading works on mobile
Dependencies: S3-LOD-001
Files Expected: frontend/components/ui/loading-spinner.tsx
Acceptance Criteria: Loading adapts to screen size
Status: Pending

S3-LOD-018
Title: Add loading dark mode support
Purpose: Ensure loading visible in dark mode
Dependencies: S3-LOD-001
Files Expected: frontend/components/ui/loading-spinner.tsx
Acceptance Criteria: Spinner visible in dark mode
Status: Pending

S3-LOD-019
Title: Add loading accessibility
Purpose: Ensure loading is accessible
Dependencies: S3-LOD-001
Files Expected: frontend/components/ui/loading-spinner.tsx
Acceptance Criteria: ARIA label for loading state
Status: Pending

S3-LOD-020
Title: Add loading integration tests
Purpose: Test loading in workspace
Dependencies: S3-LOD-001
Files Expected: frontend/app/transactions/__tests__/loading.test.tsx
Acceptance Criteria: Tests cover workspace loading
Status: Pending

## Capability 15: Testing

S3-TST-001
Title: Create capability contract tests
Purpose: Verify capability API
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/__tests__/contract.test.ts
Acceptance Criteria: Tests verify all capability methods
Status: Pending

S3-TST-002
Title: Create explainability tests
Purpose: Verify evidence system
Dependencies: S3-EVD-002
Files Expected: frontend/lib/evidence/__tests__/explainability.test.ts
Acceptance Criteria: Tests verify all evidence types
Status: Pending

S3-TST-003
Title: Create invariant tests
Purpose: Verify data invariants
Dependencies: S3-TVM-001
Files Expected: frontend/types/__tests__/invariants.test.ts
Acceptance Criteria: Tests verify data consistency
Status: Pending

S3-TST-004
Title: Create user behavior tests
Purpose: Verify user interactions
Dependencies: S3-WS-001
Files Expected: frontend/app/transactions/__tests__/user-behavior.test.tsx
Acceptance Criteria: Tests cover all user actions
Status: Pending

S3-TST-005
Title: Add mapper tests
Purpose: Verify mapper transformations
Dependencies: S3-MAP-014
Files Expected: frontend/lib/mappers/__tests__/transaction-mapper.test.ts
Acceptance Criteria: Tests cover all mapping scenarios
Status: Pending

S3-TST-006
Title: Add filter tests
Purpose: Verify filter logic
Dependencies: S3-FIL-014
Files Expected: frontend/lib/filters/__tests__/filter-logic.test.ts
Acceptance Criteria: Tests cover all filter combinations
Status: Pending

S3-TST-007
Title: Add search tests
Purpose: Verify search logic
Dependencies: S3-SEA-013
Files Expected: frontend/lib/search/__tests__/search-logic.test.ts
Acceptance Criteria: Tests cover all search scenarios
Status: Pending

S3-TST-008
Title: Add group tests
Purpose: Verify grouping logic
Dependencies: S3-GRP-015
Files Expected: frontend/lib/groups/__tests__/group-logic.test.ts
Acceptance Criteria: Tests cover all group types
Status: Pending

S3-TST-009
Title: Add sort tests
Purpose: Verify sorting logic
Dependencies: S3-SRT-014
Files Expected: frontend/lib/sorting/__tests__/sort-logic.test.ts
Acceptance Criteria: Tests cover all sort types
Status: Pending

S3-TST-010
Title: Add selection tests
Purpose: Verify selection logic
Dependencies: S3-SEL-014
Files Expected: frontend/lib/selection/__tests__/selection-logic.test.ts
Acceptance Criteria: Tests cover all selection actions
Status: Pending

S3-TST-011
Title: Add navigation tests
Purpose: Verify navigation logic
Dependencies: S3-NAV-014
Files Expected: frontend/lib/navigation/__tests__/navigation-logic.test.ts
Acceptance Criteria: Tests cover all navigation paths
Status: Pending

S3-TST-012
Title: Add loading tests
Purpose: Verify loading states
Dependencies: S3-LOD-013
Files Expected: frontend/components/ui/__tests__/loading-states.test.tsx
Acceptance Criteria: Tests cover all loading states
Status: Pending

S3-TST-013
Title: Add error tests
Purpose: Verify error states
Dependencies: S3-LOD-014
Files Expected: frontend/components/ui/__tests__/error-states.test.tsx
Acceptance Criteria: Tests cover all error states
Status: Pending

S3-TST-014
Title: Add empty state tests
Purpose: Verify empty states
Dependencies: S3-LOD-015
Files Expected: frontend/components/ui/__tests__/empty-states.test.tsx
Acceptance Criteria: Tests cover all empty states
Status: Pending

S3-TST-015
Title: Add performance tests
Purpose: Verify performance requirements
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/__tests__/performance.test.ts
Acceptance Criteria: All operations under performance thresholds
Status: Pending

S3-TST-016
Title: Add integration tests
Purpose: Verify end-to-end flow
Dependencies: S3-WS-001
Files Expected: frontend/app/transactions/__tests__/integration.test.tsx
Acceptance Criteria: Tests cover full user flow
Status: Pending

S3-TST-017
Title: Add accessibility tests
Purpose: Verify accessibility compliance
Dependencies: S3-WS-001
Files Expected: frontend/app/transactions/__tests__/accessibility.test.tsx
Acceptance Criteria: All components pass a11y tests
Status: Pending

S3-TST-018
Title: Add responsive tests
Purpose: Verify responsive design
Dependencies: S3-WS-001
Files Expected: frontend/app/transactions/__tests__/responsive.test.tsx
Acceptance Criteria: Tests cover all screen sizes
Status: Pending

S3-TST-019
Title: Add dark mode tests
Purpose: Verify dark mode support
Dependencies: S3-WS-001
Files Expected: frontend/app/transactions/__tests__/dark-mode.test.tsx
Acceptance Criteria: All components work in dark mode
Status: Pending

S3-TST-020
Title: Add test documentation
Purpose: Document testing approach
Dependencies: S3-TST-001
Files Expected: frontend/tests/README.md
Acceptance Criteria: README documents all test types
Status: Pending

## Capability 16: Validation

S3-VAL-001
Title: Run TypeScript type check
Purpose: Verify no type errors
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: No TypeScript errors
Status: Pending

S3-VAL-002
Title: Run ESLint check
Purpose: Verify code style
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: No ESLint errors
Status: Pending

S3-VAL-003
Title: Run FVF Fast check
Purpose: Verify financial values
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: No FVF violations
Status: Pending

S3-VAL-004
Title: Run architecture validation
Purpose: Verify architecture rules
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: No architecture violations
Status: Pending

S3-VAL-005
Title: Run React Query validation
Purpose: Verify query usage
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: No query violations
Status: Pending

S3-VAL-006
Title: Run generated type validation
Purpose: Verify API types
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: Types match API schema
Status: Pending

S3-VAL-007
Title: Run build verification
Purpose: Verify build succeeds
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: Build completes without errors
Status: Pending

S3-VAL-008
Title: Check for console errors
Purpose: Verify no runtime errors
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: No console errors in browser
Status: Pending

S3-VAL-009
Title: Run backend ruff check
Purpose: Verify Python style
Dependencies: All backend files
Files Expected: backend/
Acceptance Criteria: No ruff errors
Status: Pending

S3-VAL-010
Title: Run backend mypy check
Purpose: Verify Python types
Dependencies: All backend files
Files Expected: backend/
Acceptance Criteria: No mypy errors
Status: Pending

S3-VAL-011
Title: Verify no DTO in components
Purpose: Ensure architecture rule
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: No DTO imports in components
Status: Pending

S3-VAL-012
Title: Verify no calculations in components
Purpose: Ensure architecture rule
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: No financial calculations in components
Status: Pending

S3-VAL-013
Title: Verify no business logic in page
Purpose: Ensure architecture rule
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: No business logic in page.tsx
Status: Pending

S3-VAL-014
Title: Verify mapper usage everywhere
Purpose: Ensure architecture rule
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: All DTOs mapped through mapper
Status: Pending

S3-VAL-015
Title: Verify no duplicated mappers
Purpose: Ensure architecture rule
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: No duplicate mapper implementations
Status: Pending

S3-VAL-016
Title: Verify no duplicated hooks
Purpose: Ensure architecture rule
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: No duplicate hook implementations
Status: Pending

S3-VAL-017
Title: Verify no duplicated capabilities
Purpose: Ensure architecture rule
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: No duplicate capability implementations
Status: Pending

S3-VAL-018
Title: Verify no duplicated components
Purpose: Ensure architecture rule
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: No duplicate component implementations
Status: Pending

S3-VAL-019
Title: Verify no TODO comments
Purpose: Ensure maintainability
Dependencies: All files
Files Expected: All files
Acceptance Criteria: No TODO comments in code
Status: Pending

S3-VAL-020
Title: Verify no FIXME comments
Purpose: Ensure maintainability
Dependencies: All files
Files Expected: All files
Acceptance Criteria: No FIXME comments in code
Status: Pending

## Capability 17: Performance

S3-PER-001
Title: Optimize mapper performance
Purpose: Ensure mapper is fast
Dependencies: S3-MAP-002
Files Expected: frontend/lib/mappers/transaction-mapper.ts
Acceptance Criteria: Map 1000 transactions under 50ms
Status: Pending

S3-PER-002
Title: Optimize filter performance
Purpose: Ensure filtering is fast
Dependencies: S3-FIL-009
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Filter 1000 transactions under 100ms
Status: Pending

S3-PER-003
Title: Optimize search performance
Purpose: Ensure search is fast
Dependencies: S3-SEA-003
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Search 1000 transactions under 200ms
Status: Pending

S3-PER-004
Title: Optimize sort performance
Purpose: Ensure sorting is fast
Dependencies: S3-SRT-003
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Sort 1000 transactions under 30ms
Status: Pending

S3-PER-005
Title: Optimize group performance
Purpose: Ensure grouping is fast
Dependencies: S3-GRP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Group 1000 transactions under 50ms
Status: Pending

S3-PER-006
Title: Optimize selection performance
Purpose: Ensure selection is fast
Dependencies: S3-SEL-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Select 1000 transactions under 10ms
Status: Pending

S3-PER-007
Title: Optimize table rendering
Purpose: Ensure table renders quickly
Dependencies: S3-TBL-001
Files Expected: frontend/components/transaction-table/transaction-table.tsx
Acceptance Criteria: Render 1000 rows under 100ms
Status: Pending

S3-PER-008
Title: Optimize re-render prevention
Purpose: Prevent unnecessary re-renders
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: No re-renders on unrelated state changes
Status: Pending

S3-PER-009
Title: Optimize query cache
Purpose: Ensure stable query cache
Dependencies: S3-CAP-014
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Cache keys stable and efficient
Status: Pending

S3-PER-010
Title: Optimize request deduplication
Purpose: Prevent duplicate requests
Dependencies: S3-CAP-014
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: No duplicate API calls
Status: Pending

S3-PER-011
Title: Add lazy loading
Purpose: Load data on demand
Dependencies: S3-CAP-002
Files Expected: frontend/lib/capabilities/use-transaction-capability.ts
Acceptance Criteria: Data loaded only when needed
Status: Pending

S3-PER-012
Title: Add performance monitoring
Purpose: Track performance metrics
Dependencies: S3-CAP-002
Files Expected: frontend/lib/performance/monitor.ts
Acceptance Criteria: Performance logged for all operations
Status: Pending

S3-PER-013
Title: Add performance budget
Purpose: Set performance thresholds
Dependencies: S3-PER-001
Files Expected: frontend/lib/performance/budget.ts
Acceptance Criteria: All operations under budget
Status: Pending

S3-PER-014
Title: Add performance tests
Purpose: Verify performance requirements
Dependencies: S3-PER-001
Files Expected: frontend/lib/performance/__tests__/performance.test.ts
Acceptance Criteria: All tests pass performance thresholds
Status: Pending

S3-PER-015
Title: Add performance documentation
Purpose: Document performance approach
Dependencies: S3-PER-001
Files Expected: frontend/lib/performance/README.md
Acceptance Criteria: README documents all optimizations
Status: Pending

S3-PER-016
Title: Optimize bundle size
Purpose: Reduce bundle size
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: Bundle under 500KB
Status: Pending

S3-PER-017
Title: Optimize initial load
Purpose: Reduce time to interactive
Dependencies: S3-WS-001
Files Expected: frontend/app/transactions/page.tsx
Acceptance Criteria: TTI under 2 seconds
Status: Pending

S3-PER-018
Title: Optimize memory usage
Purpose: Reduce memory footprint
Dependencies: All frontend files
Files Expected: frontend/
Acceptance Criteria: Memory under 50MB
Status: Pending

S3-PER-019
Title: Add performance CI check
Purpose: Block merges on performance
Dependencies: S3-PER-014
Files Expected: .github/workflows/performance.yml
Acceptance Criteria: CI fails on performance regression
Status: Pending

S3-PER-020
Title: Add performance report
Purpose: Document performance results
Dependencies: S3-PER-014
Files Expected: docs/stage-3/PERFORMANCE_REPORT.md
Acceptance Criteria: Report shows all metrics
Status: Pending

## Capability 18: Documentation

S3-DOC-001
Title: Create ViewModel documentation
Purpose: Document TransactionViewModel
Dependencies: S3-TVM-001
Files Expected: docs/stage-3/VIEWMODEL_DOCS.md
Acceptance Criteria: All fields documented with examples
Status: Pending

S3-DOC-002
Title: Create mapper documentation
Purpose: Document mapper layer
Dependencies: S3-MAP-001
Files Expected: docs/stage-3/MAPPER_DOCS.md
Acceptance Criteria: All mappers documented with examples
Status: Pending

S3-DOC-003
Title: Create capability documentation
Purpose: Document capability layer
Dependencies: S3-CAP-001
Files Expected: docs/stage-3/CAPABILITY_DOCS.md
Acceptance Criteria: All capabilities documented
Status: Pending

S3-DOC-004
Title: Create filter documentation
Purpose: Document filter system
Dependencies: S3-FIL-001
Files Expected: docs/stage-3/FILTER_DOCS.md
Acceptance Criteria: All filters documented
Status: Pending

S3-DOC-005
Title: Create search documentation
Purpose: Document search system
Dependencies: S3-SEA-001
Files Expected: docs/stage-3/SEARCH_DOCS.md
Acceptance Criteria: All search features documented
Status: Pending

S3-DOC-006
Title: Create group documentation
Purpose: Document grouping system
Dependencies: S3-GRP-001
Files Expected: docs/stage-3/GROUP_DOCS.md
Acceptance Criteria: All group types documented
Status: Pending

S3-DOC-007
Title: Create sort documentation
Purpose: Document sorting system
Dependencies: S3-SRT-001
Files Expected: docs/stage-3/SORT_DOCS.md
Acceptance Criteria: All sort options documented
Status: Pending

S3-DOC-008
Title: Create selection documentation
Purpose: Document selection system
Dependencies: S3-SEL-001
Files Expected: docs/stage-3/SELECTION_DOCS.md
Acceptance Criteria: All selection actions documented
Status: Pending

S3-DOC-009
Title: Create evidence documentation
Purpose: Document evidence system
Dependencies: S3-EVD-001
Files Expected: docs/stage-3/EVIDENCE_DOCS.md
Acceptance Criteria: All evidence types documented
Status: Pending

S3-DOC-010
Title: Create workspace documentation
Purpose: Document workspace layout
Dependencies: S3-WS-001
Files Expected: docs/stage-3/WORKSPACE_DOCS.md
Acceptance Criteria: All regions documented
Status: Pending

S3-DOC-011
Title: Create toolbar documentation
Purpose: Document toolbar
Dependencies: S3-TBR-001
Files Expected: docs/stage-3/TOOLBAR_DOCS.md
Acceptance Criteria: All toolbar buttons documented
Status: Pending

S3-DOC-012
Title: Create table documentation
Purpose: Document transaction table
Dependencies: S3-TBL-001
Files Expected: docs/stage-3/TABLE_DOCS.md
Acceptance Criteria: All table features documented
Status: Pending

S3-DOC-013
Title: Create navigation documentation
Purpose: Document navigation system
Dependencies: S3-NAV-001
Files Expected: docs/stage-3/NAVIGATION_DOCS.md
Acceptance Criteria: All navigation paths documented
Status: Pending

S3-DOC-014
Title: Create testing documentation
Purpose: Document testing approach
Dependencies: S3-TST-001
Files Expected: docs/stage-3/TESTING_DOCS.md
Acceptance Criteria: All test types documented
Status: Pending

S3-DOC-015
Title: Create performance documentation
Purpose: Document performance approach
Dependencies: S3-PER-001
Files Expected: docs/stage-3/PERFORMANCE_DOCS.md
Acceptance Criteria: All optimizations documented
Status: Pending

S3-DOC-016
Title: Create API documentation
Purpose: Document API endpoints
Dependencies: S3-SEA-010
Files Expected: docs/stage-3/API_DOCS.md
Acceptance Criteria: All endpoints documented
Status: Pending

S3-DOC-017
Title: Create architecture documentation
Purpose: Document architecture decisions
Dependencies: S3-CAP-001
Files Expected: docs/stage-3/ARCHITECTURE_DOCS.md
Acceptance Criteria: All decisions documented
Status: Pending

S3-DOC-018
Title: Create user guide
Purpose: Document user workflows
Dependencies: S3-WS-001
Files Expected: docs/stage-3/USER_GUIDE.md
Acceptance Criteria: All workflows documented
Status: Pending

S3-DOC-019
Title: Create quick start guide
Purpose: Document quick start
Dependencies: S3-WS-001
Files Expected: docs/stage-3/QUICK_START.md
Acceptance Criteria: Quick start for developers
Status: Pending

S3-DOC-020
Title: Update main documentation
Purpose: Update stage documentation
Dependencies: All documentation
Files Expected: docs/stage-3/README.md
Acceptance Criteria: README links to all docs
Status: Pending