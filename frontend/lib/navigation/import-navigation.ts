/**
 * Import Navigation - Stage 3 Transaction Intelligence Workspace
 *
 * Navigation utilities for import-based transaction views.
 */

import type { TransactionViewModel } from '@/types/transaction-view-model';

/**
 * Get the import workspace URL for a transaction
 */
export function getImportWorkspaceUrl(transaction: TransactionViewModel): string {
  const fileId = transaction.import_lineage?.file_id || 'unknown';
  return `/import/${encodeURIComponent(fileId)}/transactions`;
}

/**
 * Check if a transaction has import navigation
 */
export function hasImportNavigation(transaction: TransactionViewModel): boolean {
  return transaction.import_lineage !== undefined;
}