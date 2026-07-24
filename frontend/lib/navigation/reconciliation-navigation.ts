/**
 * Reconciliation Navigation - Stage 3 Transaction Intelligence Workspace
 *
 * Navigation utilities for reconciliation-based transaction views.
 */

import type { TransactionViewModel } from '@/types/transaction-view-model';

/**
 * Get the reconciliation workspace URL for a transaction
 */
export function getReconciliationWorkspaceUrl(transaction: TransactionViewModel): string {
  const reconciliationId = transaction.reconciliation_id || 'unknown';
  return `/reconciliation/${encodeURIComponent(reconciliationId)}`;
}

/**
 * Check if a transaction has reconciliation navigation
 */
export function hasReconciliationNavigation(transaction: TransactionViewModel): boolean {
  return transaction.reconciliation_id !== undefined;
}