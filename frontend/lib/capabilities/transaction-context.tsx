/**
 * Transaction Capability Context - Stage 3 Transaction Intelligence Workspace
 *
 * React context for transaction state management.
 * This is the canonical state container for the Transaction Intelligence Workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { createContext, useContext, ReactNode } from 'react';
import type { TransactionViewModel } from '@/types/transaction-view-model';

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
  statusFilter: string[];

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
  setStatusFilter: (statuses: string[]) => void;
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
 * Combined context type
 */
export type TransactionContextType = TransactionCapabilityState & TransactionCapabilityActions;

/**
 * Transaction Context
 */
export const TransactionContext = createContext<TransactionContextType | undefined>(undefined);

/**
 * Transaction Provider Props
 */
interface TransactionProviderProps {
  children: ReactNode;
}

/**
 * Transaction Provider
 * Provides transaction state and actions to child components
 */
export function TransactionProvider({ children }: TransactionProviderProps) {
  // This is a placeholder - the actual implementation will be in use-transaction-capability.ts
  // The context is defined here to establish the contract
  return (
    <TransactionContext.Provider value={null as unknown as TransactionContextType}>
      {children}
    </TransactionContext.Provider>
  );
}

/**
 * Hook to access transaction context
 * @throws Error if used outside of TransactionProvider
 */
export function useTransactionContext(): TransactionContextType {
  const context = useContext(TransactionContext);
  if (context === undefined) {
    throw new Error('useTransactionContext must be used within a TransactionProvider');
  }
  return context;
}
