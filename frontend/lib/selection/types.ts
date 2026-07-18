/**
 * Selection Types - Stage 3 Transaction Intelligence Workspace
 *
 * Type definitions for transaction selection.
 */

// Selection state
export interface SelectionState {
  selectedIds: Set<string>;
  isAllSelected: boolean;
  isPageSelected: boolean;
}

// Selection mode
export type SelectionMode = 'single' | 'multiple';

// Selection action
export interface SelectionAction {
  type: 'toggle' | 'select' | 'deselect' | 'clear' | 'selectAll';
  transactionId?: string;
}

// Selection summary
export interface SelectionSummary {
  count: number;
  total: number;
  hasSelected: boolean;
}