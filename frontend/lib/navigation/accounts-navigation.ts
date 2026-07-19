/**
 * Accounts Navigation - Stage 4 Accounts Intelligence Workspace
 *
 * Cross-navigation utilities for accounts workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import type { AccountNavigationViewModel } from '@/types/accounts-view-model';

/**
 * Get cross-navigation links for accounts workspace
 */
export function getAccountsNavigation(): AccountNavigationViewModel {
  return {
    deep_link: '/accounts',
    cross_references: {
      net_worth: '/net-worth',
      transactions: '/transactions',
    },
  };
}

/**
 * Navigation links for accounts workspace
 */
export const ACCOUNTS_NAVIGATION = {
  self: '/accounts',
  netWorth: '/net-worth',
  transactions: '/transactions',
  loans: '/loans',
  creditCards: '/cards',
  investments: '/investments',
  behaviour: '/behaviour',
  forecast: '/forecast',
} as const;

/**
 * Get navigation label for a path
 */
export function getNavigationLabel(path: string): string {
  const labels: Record<string, string> = {
    [ACCOUNTS_NAVIGATION.self]: 'Accounts',
    [ACCOUNTS_NAVIGATION.netWorth]: 'Net Worth',
    [ACCOUNTS_NAVIGATION.transactions]: 'Transactions',
    [ACCOUNTS_NAVIGATION.loans]: 'Loans',
    [ACCOUNTS_NAVIGATION.creditCards]: 'Credit Cards',
    [ACCOUNTS_NAVIGATION.investments]: 'Investments',
    [ACCOUNTS_NAVIGATION.behaviour]: 'Behaviour',
    [ACCOUNTS_NAVIGATION.forecast]: 'Forecast',
  };
  return labels[path] || path;
}