/**
 * useTransactionCapability Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Unit tests for the transaction capability hook.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTransactionCapability } from '../use-transaction-capability';
import * as api from '@/lib/api/client';
import { transactionMapper } from '@/lib/mappers/transaction-mapper';

// Mock the API client
vi.mock('@/lib/api/client', () => ({
  fetchTransactions: vi.fn(),
}));

// Mock the mapper
vi.mock('@/lib/mappers/transaction-mapper', () => ({
  transactionMapper: {
    mapTransactions: vi.fn(),
  },
}));

// Mock React Query
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(() => ({
    data: { transactions: [], total: 0 },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  })),
  useQueryClient: vi.fn(() => ({
    invalidateQueries: vi.fn(),
  })),
}));

describe('useTransactionCapability', () => {
  const mockFetchTransactions = vi.mocked(api.fetchTransactions);
  const mockMapTransactions = vi.mocked(transactionMapper.mapTransactions);

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchTransactions.mockResolvedValue({ transactions: [], total: 0 });
    mockMapTransactions.mockReturnValue([]);
  });

  it('should return initial state with default values', () => {
    const { result } = renderHook(() => useTransactionCapability());

    expect(result.current.transactions).toEqual([]);
    expect(result.current.total).toBe(0);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.searchQuery).toBe('');
    expect(result.current.dateFilter).toBeNull();
    expect(result.current.categoryFilter).toEqual([]);
    expect(result.current.merchantFilter).toEqual([]);
    expect(result.current.amountFilter).toBeNull();
    expect(result.current.statusFilter).toEqual([]);
    expect(result.current.sortField).toBeNull();
    expect(result.current.sortDirection).toBe('asc');
    expect(result.current.groupBy).toBeNull();
    expect(result.current.groupOrder).toBe('asc');
    expect(result.current.selectedIds).toBeInstanceOf(Set);
    expect(result.current.selectAll).toBe(false);
    expect(result.current.page).toBe(1);
    expect(result.current.limit).toBe(50);
  });

  it('should have all required action functions', () => {
    const { result } = renderHook(() => useTransactionCapability());

    // Fetch actions
    expect(typeof result.current.fetchTransactions).toBe('function');
    expect(typeof result.current.refresh).toBe('function');

    // Filter actions
    expect(typeof result.current.setSearchQuery).toBe('function');
    expect(typeof result.current.setDateFilter).toBe('function');
    expect(typeof result.current.setCategoryFilter).toBe('function');
    expect(typeof result.current.setMerchantFilter).toBe('function');
    expect(typeof result.current.setAmountFilter).toBe('function');
    expect(typeof result.current.setStatusFilter).toBe('function');
    expect(typeof result.current.clearFilters).toBe('function');
    expect(typeof result.current.applyFilters).toBe('function');

    // Sort actions
    expect(typeof result.current.setSortField).toBe('function');
    expect(typeof result.current.setSortDirection).toBe('function');
    expect(typeof result.current.sortTransactions).toBe('function');

    // Group actions
    expect(typeof result.current.setGroupBy).toBe('function');
    expect(typeof result.current.setGroupOrder).toBe('function');
    expect(typeof result.current.groupTransactions).toBe('function');
    expect(typeof result.current.toggleGroup).toBe('function');

    // Selection actions
    expect(typeof result.current.toggleSelection).toBe('function');
    expect(typeof result.current.selectAllVisible).toBe('function');
    expect(typeof result.current.clearSelection).toBe('function');
    expect(typeof result.current.executeBulkAction).toBe('function');

    // Pagination actions
    expect(typeof result.current.setPage).toBe('function');
    expect(typeof result.current.setLimit).toBe('function');
  });

  it('should update search query', () => {
    const { result } = renderHook(() => useTransactionCapability());

    act(() => {
      result.current.setSearchQuery('test search');
    });

    expect(result.current.searchQuery).toBe('test search');
  });

  it('should update date filter', () => {
    const { result } = renderHook(() => useTransactionCapability());

    act(() => {
      result.current.setDateFilter({ from: '2026-01-01', to: '2026-12-31' });
    });

    expect(result.current.dateFilter).toEqual({ from: '2026-01-01', to: '2026-12-31' });
  });

  it('should update category filter', () => {
    const { result } = renderHook(() => useTransactionCapability());

    act(() => {
      result.current.setCategoryFilter(['Food', 'Shopping']);
    });

    expect(result.current.categoryFilter).toEqual(['Food', 'Shopping']);
  });

  it('should update merchant filter', () => {
    const { result } = renderHook(() => useTransactionCapability());

    act(() => {
      result.current.setMerchantFilter(['Amazon', 'Swiggy']);
    });

    expect(result.current.merchantFilter).toEqual(['Amazon', 'Swiggy']);
  });

  it('should update amount filter', () => {
    const { result } = renderHook(() => useTransactionCapability());

    act(() => {
      result.current.setAmountFilter({ min: 100, max: 10000 });
    });

    expect(result.current.amountFilter).toEqual({ min: 100, max: 10000 });
  });

  it('should update status filter', () => {
    const { result } = renderHook(() => useTransactionCapability());

    act(() => {
      result.current.setStatusFilter(['cleared', 'pending']);
    });

    expect(result.current.statusFilter).toEqual(['cleared', 'pending']);
  });

  it('should clear all filters', () => {
    const { result } = renderHook(() => useTransactionCapability());

    // Set some filters first
    act(() => {
      result.current.setSearchQuery('test');
      result.current.setCategoryFilter(['Food']);
      result.current.setMerchantFilter(['Amazon']);
    });

    // Clear filters
    act(() => {
      result.current.clearFilters();
    });

    expect(result.current.searchQuery).toBe('');
    expect(result.current.dateFilter).toBeNull();
    expect(result.current.categoryFilter).toEqual([]);
    expect(result.current.merchantFilter).toEqual([]);
    expect(result.current.amountFilter).toBeNull();
    expect(result.current.statusFilter).toEqual([]);
  });

  it('should toggle sort direction when same field is sorted', () => {
    const { result } = renderHook(() => useTransactionCapability());

    act(() => {
      result.current.sortTransactions('date');
    });

    expect(result.current.sortField).toBe('date');
    expect(result.current.sortDirection).toBe('asc');

    act(() => {
      result.current.sortTransactions('date');
    });

    expect(result.current.sortDirection).toBe('desc');
  });

  it('should set new sort field when different field is sorted', () => {
    const { result } = renderHook(() => useTransactionCapability());

    act(() => {
      result.current.sortTransactions('date');
    });

    act(() => {
      result.current.sortTransactions('amount');
    });

    expect(result.current.sortField).toBe('amount');
    expect(result.current.sortDirection).toBe('asc');
  });

  it('should toggle group on/off', () => {
    const { result } = renderHook(() => useTransactionCapability());

    act(() => {
      result.current.groupTransactions('date');
    });

    expect(result.current.groupBy).toBe('date');

    act(() => {
      result.current.groupTransactions('date');
    });

    expect(result.current.groupBy).toBeNull();
  });

  it('should toggle selection for a transaction', () => {
    const { result } = renderHook(() => useTransactionCapability());

    act(() => {
      result.current.toggleSelection('tx-1');
    });

    expect(result.current.selectedIds.has('tx-1')).toBe(true);

    act(() => {
      result.current.toggleSelection('tx-1');
    });

    expect(result.current.selectedIds.has('tx-1')).toBe(false);
  });

  it('should clear selection', () => {
    const { result } = renderHook(() => useTransactionCapability());

    act(() => {
      result.current.toggleSelection('tx-1');
      result.current.toggleSelection('tx-2');
    });

    act(() => {
      result.current.clearSelection();
    });

    expect(result.current.selectedIds.size).toBe(0);
    expect(result.current.selectAll).toBe(false);
  });

  it('should update page and limit', () => {
    const { result } = renderHook(() => useTransactionCapability());

    act(() => {
      result.current.setPage(2);
      result.current.setLimit(100);
    });

    expect(result.current.page).toBe(2);
    expect(result.current.limit).toBe(100);
  });
});