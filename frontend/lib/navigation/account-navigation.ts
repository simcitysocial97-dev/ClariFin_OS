/**
 * Account Navigation - Stage 3 Transaction Intelligence Workspace
 *
 * Navigation utilities for account-based transaction views.
 */

import type { TransactionViewModel } from '@/types/transaction-view-model';

/**
 * Get the account workspace URL for a transaction
 */
export function getAccountWorkspaceUrl(transaction: TransactionViewModel): string {
  const accountId = transaction.account_id || 'unknown';
  return `/accounts/${encodeURIComponent(accountId)}/transactions`;
}

/**
 * Check if a transaction has account navigation
 */
export function hasAccountNavigation(transaction: TransactionViewModel): boolean {
  return transaction.account_id !== undefined;
}