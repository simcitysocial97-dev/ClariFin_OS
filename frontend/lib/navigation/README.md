# Navigation - Stage 3 Transaction Intelligence Workspace

## Overview

Navigation utilities for the Transaction Intelligence Workspace. These functions enable cross-navigation between the transaction workspace and other workspaces (category, merchant, account, balance, reconciliation, import, adjustment).

## Usage

```tsx
import {
  getCategoryWorkspaceUrl,
  getMerchantWorkspaceUrl,
  getDateWorkspaceUrl,
  getAccountWorkspaceUrl,
  getBalanceWorkspaceUrl,
  getReconciliationWorkspaceUrl,
  getImportWorkspaceUrl,
  getAdjustmentWorkspaceUrl,
} from '@/lib/navigation';

// Navigation components
import { Breadcrumb, BackButton } from '@/components/navigation';
```

## Functions

### Category Navigation

- `getCategoryWorkspaceUrl(transaction)` - Get URL for transaction's category
- `getCategoryWorkspaceUrlByName(categoryName)` - Get URL for category by name
- `hasCategoryNavigation(transaction)` - Check if transaction has category navigation

### Merchant Navigation

- `getMerchantWorkspaceUrl(transaction)` - Get URL for transaction's merchant
- `getMerchantWorkspaceUrlByName(merchantName)` - Get URL for merchant by name
- `hasMerchantNavigation(transaction)` - Check if transaction has merchant navigation

### Date Navigation

- `getDateWorkspaceUrl(transaction)` - Get URL for transaction's date
- `getMonthWorkspaceUrl(year, month)` - Get URL for month
- `hasDateNavigation(transaction)` - Check if transaction has date navigation

### Account Navigation

- `getAccountWorkspaceUrl(transaction)` - Get URL for transaction's account
- `hasAccountNavigation(transaction)` - Check if transaction has account navigation

### Balance Navigation

- `getBalanceWorkspaceUrl(transaction)` - Get URL for transaction's balance
- `hasBalanceNavigation(transaction)` - Check if transaction has balance navigation

### Reconciliation Navigation

- `getReconciliationWorkspaceUrl(transaction)` - Get URL for transaction's reconciliation
- `hasReconciliationNavigation(transaction)` - Check if transaction has reconciliation navigation

### Import Navigation

- `getImportWorkspaceUrl(transaction)` - Get URL for transaction's import
- `hasImportNavigation(transaction)` - Check if transaction has import navigation

### Adjustment Navigation

- `getAdjustmentWorkspaceUrl(transaction)` - Get URL for transaction's adjustment
- `hasAdjustmentNavigation(transaction)` - Check if transaction has adjustment navigation

## Components

### Breadcrumb

Displays navigation path with clickable items.

```tsx
import { Breadcrumb } from '@/components/navigation';

<Breadcrumb
  items={[
    { label: 'Home', href: '/' },
    { label: 'Transactions' },
  ]}
/>
```

### BackButton

Navigates back in browser history or to fallback URL.

```tsx
import { BackButton } from '@/components/navigation';

<BackButton label="Back to Transactions" fallbackHref="/transactions" />
```

## Hooks

### useNavigationState

Get current navigation state from URL.

```tsx
import { useNavigationState } from '@/lib/navigation';

const state = useNavigationState();
// { category: 'food', date: '2024-01-15', ... }
```

### useNavigationKeyboardShortcuts

Handle Alt+Arrow key navigation shortcuts.

```tsx
import { useNavigationKeyboardShortcuts } from '@/lib/navigation';

useNavigationKeyboardShortcuts({
  onBack: () => router.back(),
  onForward: () => router.forward(),
});
```

## Error Handling

- `createNavigationError(type, message, originalPath)` - Create a navigation error
- `getNavigationErrorMessage(error)` - Get user-friendly error message
- `isNavigationErrorRecoverable(error)` - Check if error is recoverable

## Example

```tsx
// Navigate to category workspace when category is clicked
const handleCategoryClick = (tx: TransactionViewModel) => {
  if (tx.category_id) {
    window.location.href = getCategoryWorkspaceUrl(tx);
  }
};
```

## Features

- **Responsive**: URLs work on all screen sizes
- **Dark Mode**: Components support dark mode with proper theme classes
- **Accessibility**: Includes ARIA labels and keyboard navigation
- **Error Handling**: Functions handle missing data gracefully
