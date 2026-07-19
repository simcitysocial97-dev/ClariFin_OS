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
- **Dark Mode**: No UI components, so no dark mode support needed
- **Accessibility**: URL generation is accessible by default
- **Error Handling**: Functions handle missing data gracefully