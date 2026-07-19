# Stage 3 Testing Documentation

## Test Types

### 1. Contract Tests (`lib/capabilities/__tests__/contract.test.ts`)
- Verify capability API contract
- Ensure all required state properties and action functions are exposed
- Type-level verification

### 2. Explainability Tests (`lib/evidence/__tests__/explainability.test.ts`)
- Verify evidence system provides explainability
- Test all evidence types: categorization, import, adjustment, balance, reconciliation
- Test evidence chain and traceability

### 3. Invariant Tests (`types/__tests__/invariants.test.ts`)
- Verify data consistency
- Test MoneyViewModel paise/rupees relationship
- Test date navigation field consistency
- Test selection state consistency

### 4. User Behavior Tests (`app/transactions/__tests__/user-behavior.test.tsx`)
- Verify user interactions
- Test workspace states (loading, error, empty)
- Test keyboard navigation shortcuts

### 5. Mapper Tests (`lib/mappers/__tests__/transaction-mapper.test.ts`)
- Verify DTO to ViewModel mapping
- Test date formatting
- Test amount formatting
- Test evidence building

### 6. Filter Tests (`lib/filters/__tests__/filter-logic.test.ts`)
- Verify filter logic
- Test date, amount, status filters
- Test filter combinations

### 7. Search Tests (`lib/search/__tests__/search-logic.test.ts`)
- Verify search logic
- Test debouncing
- Test search history
- Test search results

### 8. Group Tests (`lib/groups/__tests__/group-logic.test.ts`)
- Verify grouping logic
- Test all group types
- Test group expansion

### 9. Sort Tests (`lib/sort/__tests__/sort-logic.test.ts`)
- Verify sorting logic
- Test all sort fields
- Test sort direction toggling

### 10. Selection Tests (`lib/selection/__tests__/selection-logic.test.ts`)
- Verify selection logic
- Test select all, clear selection
- Test bulk actions

### 11. Navigation Tests (`lib/navigation/__tests__/navigation.test.ts`)
- Verify navigation utilities
- Test all navigation paths
- Test state persistence

### 12. Loading Tests (`components/loading/__tests__/loading-spinner.test.tsx`)
- Verify loading spinner component
- Test size variants
- Test accessibility

### 13. Error Tests (`components/loading/__tests__/error-message.test.tsx`)
- Verify error message component
- Test retry functionality
- Test accessibility

### 14. Empty State Tests (`components/loading/__tests__/empty-state.test.tsx`)
- Verify empty state component
- Test action button
- Test custom messages

### 15. Performance Tests (`lib/capabilities/__tests__/performance.test.ts`)
- Verify performance requirements
- Test mapper, filter, search, sort, group performance
- Test re-render prevention

### 16. Integration Tests (`app/transactions/__tests__/integration.test.tsx`)
- Verify end-to-end flow
- Test full user workflow
- Test data flow

### 17. Accessibility Tests (`app/transactions/__tests__/accessibility.test.tsx`)
- Verify accessibility compliance
- Test ARIA attributes
- Test keyboard navigation

### 18. Responsive Tests (`app/transactions/__tests__/responsive.test.tsx`)
- Verify responsive design
- Test breakpoint classes
- Test mobile layout

### 19. Dark Mode Tests (`app/transactions/__tests__/dark-mode.test.tsx`)
- Verify dark mode support
- Test background and text classes
- Test component dark mode variants

## Running Tests

```bash
# Run all tests
npm test

# Run specific test file
npm test -- --run lib/capabilities/__tests__/contract.test.ts

# Run tests in watch mode
npm test -- --watch
```

## Test Philosophy

- Tests verify capability contracts, not CSS or HTML structure
- Tests verify explainability and invariants
- Tests verify user behavior, not component implementation
- All tests use Vitest as the test runner
- All tests use React Testing Library for component tests