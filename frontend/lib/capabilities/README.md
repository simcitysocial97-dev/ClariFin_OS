# Transaction Capability

## Overview

The Transaction Capability provides state management and orchestration for the Transaction Intelligence Workspace.

## Architecture

```
Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
```

## Hook: useTransactionCapability

### State

| Property | Type | Description |
|----------|------|-------------|
| `transactions` | `TransactionViewModel[]` | Array of mapped transactions |
| `total` | `number` | Total count of transactions |
| `loading` | `boolean` | Loading state for data fetch |
| `error` | `Error \| null` | Error state if fetch failed |
| `searchQuery` | `string` | Current search query |
| `dateFilter` | `{ from?: string; to?: string } \| null` | Date range filter |
| `categoryFilter` | `string[]` | Selected categories |
| `merchantFilter` | `string[]` | Selected merchants |
| `amountFilter` | `{ min?: number; max?: number } \| null` | Amount range filter |
| `statusFilter` | `string[]` | Transaction status filter |
| `sortField` | `'date' \| 'amount' \| 'description' \| 'category' \| 'merchant' \| null` | Current sort field |
| `sortDirection` | `'asc' \| 'desc'` | Current sort direction |
| `groupBy` | `'date' \| 'category' \| 'merchant' \| 'amount' \| null` | Current grouping |
| `groupOrder` | `'asc' \| 'desc'` | Group sort order |
| `selectedIds` | `Set<string>` | Set of selected transaction IDs |
| `selectAll` | `boolean` | Whether all visible are selected |
| `page` | `number` | Current page number |
| `limit` | `number` | Items per page |

### Actions

#### Fetch Actions

- `fetchTransactions()` - Fetch transactions with current filters
- `refresh()` - Invalidate cache and refetch

#### Filter Actions

- `setSearchQuery(query: string)` - Set search query
- `setDateFilter(filter)` - Set date range filter
- `setCategoryFilter(categories)` - Set category filter
- `setMerchantFilter(merchants)` - Set merchant filter
- `setAmountFilter(filter)` - Set amount range filter
- `setStatusFilter(statuses)` - Set status filter
- `clearFilters()` - Reset all filters to defaults
- `applyFilters()` - Apply current filters and refetch

#### Sort Actions

- `setSortField(field)` - Set sort field directly
- `setSortDirection(direction)` - Set sort direction directly
- `sortTransactions(field)` - Toggle sort on a field

#### Group Actions

- `setGroupBy(group)` - Set grouping type
- `setGroupOrder(order)` - Set group order
- `groupTransactions(group)` - Toggle grouping
- `toggleGroup()` - Toggle grouping on/off

#### Selection Actions

- `toggleSelection(id)` - Toggle single transaction selection
- `selectAllVisible()` - Select all visible transactions
- `clearSelection()` - Clear all selections
- `executeBulkAction(action, payload)` - Execute bulk action

#### Pagination Actions

- `setPage(page)` - Set current page
- `setLimit(limit)` - Set items per page

## Usage

```tsx
import { useTransactionCapability } from '@/lib/capabilities';

function TransactionWorkspace() {
  const capability = useTransactionCapability();

  return (
    <div>
      <input
        value={capability.searchQuery}
        onChange={(e) => capability.setSearchQuery(e.target.value)}
      />
      <button onClick={() => capability.sortTransactions('date')}>
        Sort by Date
      </button>
    </div>
  );
}
```

## React Query Integration

The capability uses React Query for:
- Data caching (5 minutes stale, 10 minutes cache)
- Automatic refetching
- Cache invalidation on refresh

Query key: `TRANSACTION_QUERY_KEY`