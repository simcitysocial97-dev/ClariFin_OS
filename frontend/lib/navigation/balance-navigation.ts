/**
 * Balance Navigation - Stage 3 Transaction Intelligence Workspace
 *
 * Navigation utilities for balance-based transaction views.
 */

import type { TransactionViewModel } from '@/types/transaction-view-model';

/**
 * Get the balance workspace URL for a transaction
 */
export function getBalanceWorkspaceUrl(transaction: TransactionViewModel): string {
  const accountId = transaction.account_id || 'unknown';
  return `/accounts/${encodeURIComponent(accountId)}/balance`;
}

/**
 * Check if a transaction has balance navigation
 */
export function hasBalanceNavigation(transaction: TransactionViewModel): boolean {
  return transaction.account_id !== undefined && transaction.balance !== undefined;
}