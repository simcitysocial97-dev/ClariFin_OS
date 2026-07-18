# Selection

## Overview

The Selection system provides transaction selection functionality for the Transaction Intelligence Workspace.

## Components

### SelectionCheckbox

Checkbox for selecting individual transactions.

**Props:**
- `transactionId: string` - Transaction ID
- `selectionState: SelectionState` - Current selection state
- `onToggle: (id: string) => void` - Toggle callback

## Types

### SelectionState
- `selectedIds: Set<string>` - Selected transaction IDs
- `isAllSelected: boolean` - All transactions selected
- `isPageSelected: boolean` - Current page selected

### SelectionMode
- `'single' | 'multiple'`

### SelectionAction
- `type: 'toggle' | 'select' | 'deselect' | 'clear' | 'selectAll'`
- `transactionId?: string`

### SelectionSummary
- `count: number` - Number of selected transactions
- `total: number` - Total amount in paise
- `hasSelected: boolean` - Has any selection

## Usage

```tsx
import { SelectionCheckbox } from '@/lib/selection';

function TransactionRow({ transaction }) {
  return (
    <SelectionCheckbox
      transactionId={transaction.id}
      selectionState={selectionState}
      onToggle={handleToggle}
    />
  );
}
```

## Architecture

- Presentation-only components
- No data fetching
- No business logic
- Emits events via callbacks