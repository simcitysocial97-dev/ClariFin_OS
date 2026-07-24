/**
 * Adjustment Navigation - Stage 3 Transaction Intelligence Workspace
 *
 * Navigation utilities for adjustment-based transaction views.
 */

import type { TransactionViewModel } from '@/types/transaction-view-model';

/**
 * Get the adjustment workspace URL for a transaction
 */
export function getAdjustmentWorkspaceUrl(transaction: TransactionViewModel): string {
  const adjustmentId = transaction.adjustment_id || 'unknown';
  return `/adjustments/${encodeURIComponent(adjustmentId)}/transactions`;
}

/**
 * Check if a transaction has adjustment navigation
 */
export function hasAdjustmentNavigation(transaction: TransactionViewModel): boolean {
  return transaction.is_adjusted === true;
}