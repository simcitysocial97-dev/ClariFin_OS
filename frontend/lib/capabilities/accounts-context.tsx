/**
 * Accounts Capability Context - Stage 4 Accounts Intelligence Workspace
 *
 * React context for accounts state management.
 * This is the canonical state container for the Accounts Intelligence Workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { createContext, useContext, ReactNode } from 'react';
import type { AccountsViewModel } from '@/types/accounts-view-model';

/**
 * Accounts capability state interface
 */
export interface AccountsCapabilityState {
  // Data
  accounts: AccountsViewModel | null;
  loading: boolean;
  error: Error | null;

  // Loading timeout
  loadingTimeout: boolean;
  loadingTimeoutMessage: string;

  // Error recovery
  errorRecoveryAttempts: number;
  isRecovering: boolean;

  // Filters
  accountTypes: string[];
  institutions: string[];
  statuses: string[];
  dateRange: { from?: string; to?: string } | null;
  balanceRange: { min?: number; max?: number } | null;

  // Evidence drawer
  isEvidenceDrawerOpen: boolean;

  // Selected account
  selectedAccountId: string | null;
}

/**
 * Accounts capability actions interface
 */
export interface AccountsCapabilityActions {
  // Fetch
  fetchAccounts: () => Promise<void>;
  refresh: () => Promise<void>;
  recoverFromError: () => Promise<void>;

  // Filters
  setAccountTypes: (types: string[]) => void;
  setInstitutions: (institutions: string[]) => void;
  setStatuses: (statuses: string[]) => void;
  setDateRange: (range: { from?: string; to?: string } | null) => void;
  setBalanceRange: (range: { min?: number; max?: number } | null) => void;
  clearFilters: () => void;
  applyFilters: () => Promise<void>;

  // Evidence drawer
  toggleEvidenceDrawer: () => void;

  // Selection
  selectAccount: (accountId: string | null) => void;
}

/**
 * Combined context type
 */
export type AccountsContextType = AccountsCapabilityState & AccountsCapabilityActions;

/**
 * Accounts Context
 */
export const AccountsContext = createContext<AccountsContextType | undefined>(undefined);

/**
 * Accounts Provider Props
 */
interface AccountsProviderProps {
  children: ReactNode;
}

/**
 * Accounts Provider
 * Provides accounts state and actions to child components
 */
export function AccountsProvider({ children }: AccountsProviderProps) {
  // This is a placeholder - the actual implementation will be in use-accounts-capability.ts
  // The context is defined here to establish the contract
  return (
    <AccountsContext.Provider value={null as unknown as AccountsContextType}>
      {children}
    </AccountsContext.Provider>
  );
}

/**
 * Hook to access accounts context
 * @throws Error if used outside of AccountsProvider
 */
export function useAccountsContext(): AccountsContextType {
  const context = useContext(AccountsContext);
  if (context === undefined) {
    throw new Error('useAccountsContext must be used within an AccountsProvider');
  }
  return context;
}