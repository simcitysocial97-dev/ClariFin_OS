/**
 * Date Navigation - Stage 3 Transaction Intelligence Workspace
 *
 * Navigation utilities for date-based transaction views.
 */

import type { TransactionViewModel } from '@/types/transaction-view-model';

/**
 * Get the date workspace URL for a transaction
 */
export function getDateWorkspaceUrl(transaction: TransactionViewModel): string {
  const date = transaction.date || 'unknown';
  return `/transactions?date=${encodeURIComponent(date)}`;
}

/**
 * Get the month workspace URL for a transaction
 */
export function getMonthWorkspaceUrl(transaction: TransactionViewModel): string {
  const monthKey = transaction.month_key || 'unknown';
  return `/transactions?month=${encodeURIComponent(monthKey)}`;
}

/**
 * Check if a transaction has date navigation
 */
export function hasDateNavigation(transaction: TransactionViewModel): boolean {
  return transaction.date !== undefined || transaction.month_key !== undefined;
}