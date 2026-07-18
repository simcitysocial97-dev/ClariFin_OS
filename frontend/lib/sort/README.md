# Sort

## Overview

The Sort system provides transaction sorting functionality for the Transaction Intelligence Workspace.

## Components

### SortHeader

Sortable column header with sort indicator.

**Props:**
- `field: SortField` - Sort field
- `label: string` - Display label
- `currentField: SortField | null` - Currently sorted field
- `direction: SortDirection` - Sort direction
- `onSort: (field: SortField) => void` - Sort callback

## Types

### SortField
- `'date' | 'amount' | 'description' | 'category' | 'merchant'`

### SortDirection
- `'asc' | 'desc'`

### SortState
- `field: SortField | null` - Current sort field
- `direction: SortDirection` - Sort direction

### SortOption
- `field: SortField` - Sort field
- `label: string` - Display label

## Usage

```tsx
import { SortHeader } from '@/lib/sort';

function TransactionTable() {
  return (
    <SortHeader
      field="date"
      label="Date"
      currentField="date"
      direction="asc"
      onSort={(field) => console.log('Sort by', field)}
    />
  );
}
```

## Architecture

- Presentation-only components
- No data fetching
- No business logic
- Emits events via callbacks