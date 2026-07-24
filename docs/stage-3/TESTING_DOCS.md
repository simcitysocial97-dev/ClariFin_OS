# Testing Documentation

## Overview

Stage 3 uses a comprehensive testing approach covering contracts, explainability, invariants, user behavior, and performance.

## Test Types

### Contract Tests
Verify the capability API contract is maintained.
- Location: `frontend/lib/capabilities/__tests__/contract.test.ts`
- Tests: 6

### Explainability Tests
Verify evidence system provides proper explainability.
- Location: `frontend/lib/evidence/__tests__/explainability.test.ts`
- Tests: 19

### Invariant Tests
Verify data consistency and invariants.
- Location: `frontend/types/__tests__/invariants.test.ts`
- Tests: 22

### User Behavior Tests
Verify user interactions with the workspace.
- Location: `frontend/app/transactions/__tests__/user-behavior.test.tsx`
- Tests: 16

### Filter Logic Tests
Verify filter logic and combinations.
- Location: `frontend/lib/filters/__tests__/filter-logic.test.ts`
- Tests: 11

### Search Logic Tests
Verify search logic and behavior.
- Location: `frontend/lib/search/__tests__/search-logic.test.ts`
- Tests: 14

### Group Logic Tests
Verify grouping logic and behavior.
- Location: `frontend/lib/groups/__tests__/group-logic.test.ts`
- Tests: 17

### Sort Logic Tests
Verify sorting logic and behavior.
- Location: `frontend/lib/sort/__tests__/sort-logic.test.ts`
- Tests: 17

### Selection Logic Tests
Verify selection logic and behavior.
- Location: `frontend/lib/selection/__tests__/selection-logic.test.ts`
- Tests: 16

### Navigation Tests
Verify navigation logic and behavior.
- Location: `frontend/lib/navigation/__tests__/navigation.test.ts`
- Tests: 37

### Performance Tests
Verify performance requirements.
- Location: `frontend/lib/capabilities/__tests__/performance.test.ts`
- Tests: 11

### Integration Tests
Verify end-to-end flow.
- Location: `frontend/app/transactions/__tests__/integration.test.tsx`
- Tests: 9

### Accessibility Tests
Verify accessibility compliance.
- Location: `frontend/app/transactions/__tests__/accessibility.test.tsx`
- Tests: 11

### Responsive Tests
Verify responsive design.
- Location: `frontend/app/transactions/__tests__/responsive.test.tsx`
- Tests: 10

### Dark Mode Tests
Verify dark mode support.
- Location: `frontend/app/transactions/__tests__/dark-mode.test.tsx`
- Tests: 8

## Running Tests

```bash
# Run all tests
npm run test

# Run with coverage
npm run test:coverage

# Run specific test file
npx vitest run path/to/test.ts
```

## Test Coverage

- 46 test files
- 442 total tests
- All tests passing