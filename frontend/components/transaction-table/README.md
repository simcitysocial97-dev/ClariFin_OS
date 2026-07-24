# Transaction Table - Stage 3 Transaction Intelligence Workspace

## Overview

The Transaction Table displays a list of transactions with support for loading, error, and empty states. Pagination is handled by the separate PaginationControls component.

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

### VirtualizedTable

A virtualized table component for efficient rendering of large transaction lists.

```tsx
import { VirtualizedTable } from '@/components/transaction-table';

<VirtualizedTable
  transactions={transactions}
  loading={false}
  error={null}
  onRowClick={(tx) => console.log(tx)}
  onSelectionChange={(id, selected) => console.log(id, selected)}
  selectedIds={new Set(['1', '2'])}
  rowHeight={48}
  visibleRows={10}
/>
```

**Props:**
- `transactions`: Array of TransactionViewModel to display
- `loading`: Loading state (default: false)
- `error`: Error object for error state
- `onRowClick`: Callback when a row is clicked
- `onSelectionChange`: Callback when selection changes
- `selectedIds`: Set of selected transaction IDs
- `rowHeight`: Height of each row in pixels (default: 48)
- `visibleRows`: Number of rows to render at once (default: 10)

### PaginationControls

A pagination component for navigating between pages of transactions.

```tsx
import { PaginationControls } from '@/components/transaction-table';

<PaginationControls
  page={1}
  limit={50}
  total={100}
  onPageChange={(page) => console.log(page)}
  onLimitChange={(limit) => console.log(limit)}
/>
```

**Props:**
- `page`: Current page number (default: 1)
- `limit`: Items per page (default: 50)
- `total`: Total number of items
- `onPageChange`: Callback when page changes
- `onLimitChange`: Callback when limit changes

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

### Pagination

- First/Previous/Next/Last page navigation
- Items per page selector (10, 25, 50, 100)
- Page info display (e.g., "1 / 2", "Showing 1 to 50 of 100")
- Buttons disabled appropriately on first/last page

### Virtualization

- Fixed height container (400px) with overflow scroll
- Only renders visible rows for performance
- Configurable row height and visible row count
- Spacer rows for proper scroll height

### Responsive Design

- Hides category column on mobile
- Hides merchant column on tablet
- Full width on mobile, constrained on desktop
- Pagination controls stack vertically on mobile

### Dark Mode

Uses `bg-background` classes for proper dark mode support.

### Accessibility

- `role="table"` and `aria-label` for semantic structure
- `aria-selected` on rows for selection state
- Keyboard navigation with arrow keys
- Enter/space to trigger row click
- ARIA labels on all pagination buttons

## Performance

- 100 transactions render under 400ms
- 500 transactions render under 2000ms
- Loading and error states render under 50ms