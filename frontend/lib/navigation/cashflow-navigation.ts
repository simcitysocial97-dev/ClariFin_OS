/**
 * Cashflow Navigation - Stage 4 Cashflow Truth Workspace
 *
 * Enables navigation from cashflow to related workspaces.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

/**
 * Navigation target for an account
 */
export function navigateToAccount(accountId: string): string {
  return `/accounts?highlight=${accountId}`;
}

/**
 * Navigation target for a transaction
 */
export function navigateToTransaction(transactionId: string): string {
  return `/transactions?highlight=${transactionId}`;
}

/**
 * Get cross-navigation links for cashflow
 */
export function getCrossNavigationLinks(): Record<string, string> {
  return {
    accounts: '/accounts',
    transactions: '/transactions',
  };
}

/**
 * Create deep link to cashflow with context
 */
export function createDeepLink(context?: {
  dateRange?: { from: string; to: string };
  categories?: string[];
  merchants?: string[];
}): string {
  const params = new URLSearchParams();
  if (context?.dateRange) {
    params.set('from', context.dateRange.from);
    params.set('to', context.dateRange.to);
  }
  if (context?.categories?.length) {
    params.set('categories', context.categories.join(','));
  }
  if (context?.merchants?.length) {
    params.set('merchants', context.merchants.join(','));
  }
  const queryString = params.toString();
  return queryString ? `/cashflow?${queryString}` : '/cashflow';
}