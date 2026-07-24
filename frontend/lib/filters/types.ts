/**
 * Filter Types - Stage 3 Transaction Intelligence Workspace
 *
 * Type definitions for transaction filtering.
 */

// Date filter type
export interface DateFilter {
  from?: string; // ISO date string
  to?: string; // ISO date string
}

// Amount filter type
export interface AmountFilter {
  min?: number; // Minimum amount in paise
  max?: number; // Maximum amount in paise
}

// Status filter type
export type TransactionStatus = 'cleared' | 'pending' | 'adjusted' | 'rejected';

// Combined filter state
export interface TransactionFilters {
  searchQuery: string;
  dateFilter: DateFilter | null;
  categoryFilter: string[];
  merchantFilter: string[];
  amountFilter: AmountFilter | null;
  statusFilter: TransactionStatus[];
}

// Filter change event
export interface FilterChangeEvent {
  type: 'search' | 'date' | 'category' | 'merchant' | 'amount' | 'status';
  value: unknown;
}

// Filter validation result
export interface FilterValidationResult {
  valid: boolean;
  error?: string;
}