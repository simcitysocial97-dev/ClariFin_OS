/**
 * Group Types - Stage 3 Transaction Intelligence Workspace
 *
 * Type definitions for transaction grouping.
 */

// Group type
export type GroupType = 'date' | 'category' | 'merchant' | 'amount';

// Group order
export type GroupOrder = 'asc' | 'desc';

// Group key
export interface GroupKey {
  id: string;
  label: string;
  count: number;
  total: number;
}

// Grouped transaction
export interface GroupedTransaction {
  group: GroupKey;
  transactions: string[]; // Transaction IDs
}

// Group state
export interface GroupState {
  groupBy: GroupType | null;
  groupOrder: GroupOrder;
  groups: GroupedTransaction[];
  expandedGroups: Set<string>;
}