# Groups

## Overview

The Groups system provides transaction grouping functionality for the Transaction Intelligence Workspace.

## Components

### GroupHeader

Displays group summary with expand/collapse toggle.

**Props:**
- `group: GroupKey` - Group data
- `isExpanded: boolean` - Expansion state
- `onToggle: () => void` - Toggle callback

## Types

### GroupType
- `'date' | 'category' | 'merchant' | 'amount'`

### GroupOrder
- `'asc' | 'desc'`

### GroupKey
- `id: string` - Unique identifier
- `label: string` - Display label
- `count: number` - Transaction count
- `total: number` - Total amount in paise

### GroupedTransaction
- `group: GroupKey` - Group metadata
- `transactions: string[]` - Transaction IDs

### GroupState
- `groupBy: GroupType | null` - Current grouping
- `groupOrder: GroupOrder` - Sort order
- `groups: GroupedTransaction[]` - All groups
- `expandedGroups: Set<string>` - Expanded group IDs

## Usage

```tsx
import { GroupHeader } from '@/lib/groups';

function GroupedList() {
  return (
    <GroupHeader
      group={{ id: 'groceries', label: 'Groceries', count: 5, total: 50000 }}
      isExpanded={true}
      onToggle={() => {}}
    />
  );
}
```

## Architecture

- Presentation-only components
- No data fetching
- No business logic
- Emits events via callbacks