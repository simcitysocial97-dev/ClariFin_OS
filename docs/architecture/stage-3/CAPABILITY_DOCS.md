# Capability Layer Documentation

## Overview

The Capability Layer owns orchestration, filtering, sorting, searching, grouping, and selection state for the Transaction Intelligence Workspace.

## Architecture Flow

```
React Query → Capability → Workspace → Components
```

## useTransactionCapability Hook

### State

```typescript
interface TransactionCapabilityState {
  // Data
  transactions: TransactionViewModel[];
  total: number;
  loading: boolean;
  error: Error | null;

  // Loading timeout
  loadingTimeout: boolean;
  loadingTimeoutMessage: string;

  // Error recovery
  errorRecoveryAttempts: number;
  isRecovering: boolean;

  // Filters
  searchQuery: string;
  dateFilter: { from?: string; to?: string } | null;
  categoryFilter: string[];
  merchantFilter: string[];
  amountFilter: { min?: number; max?: number } | null;
  statusFilter: TransactionStatus[];

  // Sorting
  sortField: 'date' | 'amount' | 'description' | 'category' | 'merchant' | null;
  sortDirection: 'asc' | 'desc';

  // Grouping
  groupBy: 'date' | 'category' | 'merchant' | 'amount' | null;
  groupOrder: 'asc' | 'desc';

  // Selection
  selectedIds: Set<string>;
  selectAll: boolean;

  // Pagination
  page: number;
  limit: number;
}
```

### Actions

```typescript
interface TransactionCapabilityActions {
  // Fetch
  fetchTransactions: () => Promise<void>;
  refresh: () => Promise<void>;
  recoverFromError: () => Promise<void>;

  // Filters
  setSearchQuery: (query: string) => void;
  setDateFilter: (filter: { from?: string; to?: string } | null) => void;
  setCategoryFilter: (categories: string[]) => void;
  setMerchantFilter: (merchants: string[]) => void;
  setAmountFilter: (filter: { min?: number; max?: number } | null) => void;
  setStatusFilter: (statuses: TransactionStatus[]) => void;
  clearFilters: () => void;
  applyFilters: () => Promise<void>;

  // Sorting
  setSortField: (field: 'date' | 'amount' | 'description' | 'category' | 'merchant' | null) => void;
  setSortDirection: (direction: 'asc' | 'desc') => void;
  sortTransactions: (field: 'date' | 'amount' | 'description' | 'category' | 'merchant') => void;

  // Grouping
  setGroupBy: (group: 'date' | 'category' | 'merchant' | 'amount' | null) => void;
  setGroupOrder: (order: 'asc' | 'desc') => void;
  groupTransactions: (group: 'date' | 'category' | 'merchant' | 'amount') => void;
  toggleGroup: () => void;

  // Selection
  toggleSelection: (id: string) => void;
  selectAllVisible: () => void;
  clearSelection: () => void;
  executeBulkAction: (action: 'categorize' | 'adjust' | 'delete', payload?: unknown) => Promise<void>;

  // Pagination
  setPage: (page: number) => void;
  setLimit: (limit: number) => void;
}
```

## React Query Integration

- Query key: `transactions`
- Stale time: 5 minutes
- GC time: 10 minutes
- Retry: 3 attempts with exponential backoff
- Cache invalidation on refresh