/**
 * Sort Types - Stage 3 Transaction Intelligence Workspace
 *
 * Type definitions for transaction sorting.
 */

// Sort field
export type SortField = 'date' | 'amount' | 'description' | 'category' | 'merchant';

// Sort direction
export type SortDirection = 'asc' | 'desc';

// Sort state
export interface SortState {
  field: SortField | null;
  direction: SortDirection;
}

// Sort option
export interface SortOption {
  field: SortField;
  label: string;
}