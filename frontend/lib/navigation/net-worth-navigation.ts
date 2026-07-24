/**
 * Net Worth Navigation - Stage 4 Net Worth Intelligence Workspace
 *
 * Enables navigation from net worth to related workspaces.
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
 * Navigation target for an investment
 */
export function navigateToInvestment(investmentId: string): string {
  return `/investments?highlight=${investmentId}`;
}

/**
 * Navigation target for a loan
 */
export function navigateToLoan(loanId: string): string {
  return `/loans?highlight=${loanId}`;
}

/**
 * Navigation target for a credit card
 */
export function navigateToCreditCard(cardId: string): string {
  return `/cards?highlight=${cardId}`;
}

/**
 * Get cross-navigation links for net worth
 */
export function getCrossNavigationLinks(): Record<string, string> {
  return {
    accounts: '/accounts',
    investments: '/investments',
    loans: '/loans',
    creditCards: '/cards',
  };
}

/**
 * Create deep link to net worth with context
 */
export function createDeepLink(context?: {
  dateRange?: { from: string; to: string };
  accountTypes?: string[];
}): string {
  const params = new URLSearchParams();
  if (context?.dateRange) {
    params.set('from', context.dateRange.from);
    params.set('to', context.dateRange.to);
  }
  if (context?.accountTypes?.length) {
    params.set('types', context.accountTypes.join(','));
  }
  const queryString = params.toString();
  return queryString ? `/net-worth?${queryString}` : '/net-worth';
}