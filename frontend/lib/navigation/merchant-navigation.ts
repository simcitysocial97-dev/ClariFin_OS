/**
 * Merchant Navigation - Stage 3 Transaction Intelligence Workspace
 *
 * Navigation utilities for merchant-based transaction views.
 */

import type { TransactionViewModel } from '@/types/transaction-view-model';

/**
 * Get the merchant workspace URL for a transaction
 */
export function getMerchantWorkspaceUrl(transaction: TransactionViewModel): string {
  const merchantId = transaction.merchant_id || 'unknown';
  return `/transactions?merchant=${encodeURIComponent(merchantId)}`;
}

/**
 * Get the merchant workspace URL for a merchant name
 */
export function getMerchantWorkspaceUrlByName(merchantName: string): string {
  return `/transactions?merchant=${encodeURIComponent(merchantName)}`;
}

/**
 * Check if a transaction has merchant navigation
 */
export function hasMerchantNavigation(transaction: TransactionViewModel): boolean {
  return transaction.merchant_id !== undefined || transaction.merchant_name !== undefined;
}