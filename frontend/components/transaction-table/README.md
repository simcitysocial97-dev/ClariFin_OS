# Transaction Table - Stage 3 Transaction Intelligence Workspace

## Overview

The Transaction Table displays a list of transactions with support for loading, error, and empty states.

## Components

### TransactionTable

A responsive table component for displaying transactions.

```tsx
import { TransactionTable } from '@/components/transaction-table';

<TransactionTable
  transactions={transactions}
  loading={false}
  error={null}
  onRowClick={(tx) => console.log(tx)}
  onSelectionChange={(id, selected) => console.log(id, selected)}
  selectedIds={new Set(['1', '2'])}
/>
```

**Props:**
- `transactions`: Array of TransactionViewModel to display
- `loading`: Loading state (default: false)
- `error`: Error object for error state
- `onRowClick`: Callback when a row is clicked
- `onSelectionChange`: Callback when selection changes
- `selectedIds`: Set of selected transaction IDs

## Features

### Columns

- **Select**: Checkbox for row selection
- **Date**: Transaction date (formatted)
- **Description**: Transaction description
- **Category**: Category badge (hidden on mobile)
- **Merchant**: Merchant name (hidden on tablet)
- **Amount**: Transaction amount with color coding

### States

- **Loading**: Shows skeleton rows while loading
- **Error**: Displays error message with optional retry
- **Empty**: Shows empty state when no transactions

### Responsive Design

- Hides category column on mobile
- Hides merchant column on tablet
- Full width on mobile, constrained on desktop

### Dark Mode

Uses `bg-background` classes for proper dark mode support.

### Accessibility

- `role="table"` and `aria-label` for semantic structure
- `aria-selected` on rows for selection state
- Keyboard navigation with arrow keys
- Enter/space to trigger row click

## Performance

- 100 transactions render under 400ms
- 500 transactions render under 2000ms
- Loading and error states render under 50ms