/**
 * useTransactionCapability Hook - Stage 3 Transaction Intelligence Workspace
 *
 * React hook for transaction state management and orchestration.
 * This is the canonical capability implementation for the Transaction Intelligence Workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useState, useCallback, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { TransactionViewModel } from '@/types/transaction-view-model';
import type { TransactionStatus } from '@/lib/filters/types';
import { transactionMapper } from '@/lib/mappers/transaction-mapper';
import { fetchTransactions } from '@/lib/api/client';

// Query key for React Query
const TRANSACTION_QUERY_KEY = 'transactions';

/**
 * Transaction capability state interface
 */
export interface TransactionCapabilityState {
  // Data
  transactions: TransactionViewModel[];
  total: number;
  loading: boolean;
  error: Error | null;

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

/**
 * Transaction capability actions interface
 */
export interface TransactionCapabilityActions {
  // Fetch
  fetchTransactions: () => Promise<void>;
  refresh: () => Promise<void>;

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

/**
 * Transaction capability return type
 */
export type TransactionCapabilityReturn = TransactionCapabilityState & TransactionCapabilityActions;

/**
 * useTransactionCapability Hook
 *
 * Provides transaction state management and orchestration for the Transaction Intelligence Workspace.
 * Uses React Query for data fetching and caching.
 */
export function useTransactionCapability(): TransactionCapabilityReturn {
  const queryClient = useQueryClient();

  // State
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [dateFilter, setDateFilter] = useState<{ from?: string; to?: string } | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string[]>([]);
  const [merchantFilter, setMerchantFilter] = useState<string[]>([]);
  const [amountFilter, setAmountFilter] = useState<{ min?: number; max?: number } | null>(null);
  const [statusFilter, setStatusFilter] = useState<TransactionStatus[]>([]);
  const [sortField, setSortField] = useState<'date' | 'amount' | 'description' | 'category' | 'merchant' | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [groupBy, setGroupBy] = useState<'date' | 'category' | 'merchant' | 'amount' | null>(null);
  const [groupOrder, setGroupOrder] = useState<'asc' | 'desc'>('asc');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [selectAll, setSelectAll] = useState<boolean>(false);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(50);

  // Build query parameters from state
  const queryParams = useMemo(() => ({
    search: searchQuery || undefined,
    category: categoryFilter.length > 0 ? categoryFilter[0] : undefined,
    limit,
    offset: (page - 1) * limit,
  }), [searchQuery, categoryFilter, limit, page]);

  // React Query for data fetching
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery<{ transactions: TransactionViewModel[]; total: number }>({
    queryKey: [TRANSACTION_QUERY_KEY, queryParams],
    queryFn: async () => {
      const result = await fetchTransactions(queryParams);
      return {
        transactions: transactionMapper.mapTransactions(result.transactions),
        total: result.total,
      };
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (React Query v5 uses gcTime instead of cacheTime)
  });

  // Actions
  const fetchTransactionsAction = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: [TRANSACTION_QUERY_KEY] });
  }, [queryClient]);

  const clearFilters = useCallback(() => {
    setSearchQuery('');
    setDateFilter(null);
    setCategoryFilter([]);
    setMerchantFilter([]);
    setAmountFilter(null);
    setStatusFilter([]);
    setPage(1);
  }, []);

  const applyFilters = useCallback(async () => {
    setPage(1);
    await refetch();
  }, [refetch]);

  const sortTransactions = useCallback((field: 'date' | 'amount' | 'description' | 'category' | 'merchant') => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  }, [sortField]);

  const groupTransactions = useCallback((group: 'date' | 'category' | 'merchant' | 'amount') => {
    if (groupBy === group) {
      setGroupBy(null);
    } else {
      setGroupBy(group);
    }
  }, [groupBy]);

  const toggleGroup = useCallback(() => {
    if (groupBy) {
      setGroupBy(null);
    } else {
      setGroupBy('date');
    }
  }, [groupBy]);

  const toggleSelection = useCallback((id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
    setSelectAll(false);
  }, []);

  const selectAllVisible = useCallback(() => {
    if (data?.transactions) {
      const allIds = new Set(data.transactions.map(t => t.id));
      setSelectedIds(allIds);
      setSelectAll(true);
    }
  }, [data]);

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
    setSelectAll(false);
  }, []);

  const executeBulkAction = useCallback(async (
    action: 'categorize' | 'adjust' | 'delete',
    payload?: unknown
  ) => {
    // Placeholder for bulk action implementation
    // This will be implemented when backend endpoints are available
    console.log('Bulk action:', action, 'on', Array.from(selectedIds), payload);
  }, [selectedIds]);

  // Return state and actions
  return {
    // Data
    transactions: data?.transactions ?? [],
    total: data?.total ?? 0,
    loading: isLoading,
    error: error as Error | null,

    // Filters
    searchQuery,
    dateFilter,
    categoryFilter,
    merchantFilter,
    amountFilter,
    statusFilter,

    // Sorting
    sortField,
    sortDirection,

    // Grouping
    groupBy,
    groupOrder,

    // Selection
    selectedIds,
    selectAll,

    // Pagination
    page,
    limit,

    // Actions
    fetchTransactions: fetchTransactionsAction,
    refresh,
    setSearchQuery,
    setDateFilter,
    setCategoryFilter,
    setMerchantFilter,
    setAmountFilter,
    setStatusFilter,
    clearFilters,
    applyFilters,
    setSortField,
    setSortDirection,
    sortTransactions,
    setGroupBy,
    setGroupOrder,
    groupTransactions,
    toggleGroup,
    toggleSelection,
    selectAllVisible,
    clearSelection,
    executeBulkAction,
    setPage,
    setLimit,
  };
}