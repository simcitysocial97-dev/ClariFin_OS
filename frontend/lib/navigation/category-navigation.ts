/**
 * Category Navigation - Stage 3 Transaction Intelligence Workspace
 *
 * Navigation utilities for category-based transaction views.
 */

import type { TransactionViewModel } from '@/types/transaction-view-model';

/**
 * Get the category workspace URL for a transaction
 */
export function getCategoryWorkspaceUrl(transaction: TransactionViewModel): string {
  const categoryId = transaction.category_id || 'uncategorized';
  return `/transactions?category=${encodeURIComponent(categoryId)}`;
}

/**
 * Get the category workspace URL for a category name
 */
export function getCategoryWorkspaceUrlByName(categoryName: string): string {
  return `/transactions?category=${encodeURIComponent(categoryName)}`;
}

/**
 * Check if a transaction has category navigation
 */
export function hasCategoryNavigation(transaction: TransactionViewModel): boolean {
  return transaction.category_id !== undefined || transaction.category_name !== undefined;
}