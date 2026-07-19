/**
 * Net Worth Capability Context - Stage 4 Net Worth Intelligence Workspace
 *
 * React context for net worth state management.
 * This is the canonical state container for the Net Worth Intelligence Workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { createContext, useContext, ReactNode } from 'react';
import type { NetWorthViewModel } from '@/types/net-worth-view-model';

/**
 * Net Worth capability state interface
 */
export interface NetWorthCapabilityState {
  // Data
  netWorth: NetWorthViewModel | null;
  loading: boolean;
  error: Error | null;

  // Loading timeout
  loadingTimeout: boolean;
  loadingTimeoutMessage: string;

  // Error recovery
  errorRecoveryAttempts: number;
  isRecovering: boolean;

  // Filters
  dateRange: { from?: string; to?: string } | null;
  accountTypes: string[];
  period: string;

  // Evidence drawer
  isEvidenceDrawerOpen: boolean;
}

/**
 * Net Worth capability actions interface
 */
export interface NetWorthCapabilityActions {
  // Fetch
  fetchNetWorth: () => Promise<void>;
  refresh: () => Promise<void>;
  recoverFromError: () => Promise<void>;

  // Filters
  setDateRange: (filter: { from?: string; to?: string } | null) => void;
  setAccountTypes: (types: string[]) => void;
  setPeriod: (period: string) => void;
  clearFilters: () => void;
  applyFilters: () => Promise<void>;

  // Evidence drawer
  toggleEvidenceDrawer: () => void;
}

/**
 * Combined context type
 */
export type NetWorthContextType = NetWorthCapabilityState & NetWorthCapabilityActions;

/**
 * Net Worth Context
 */
export const NetWorthContext = createContext<NetWorthContextType | undefined>(undefined);

/**
 * Net Worth Provider Props
 */
interface NetWorthProviderProps {
  children: ReactNode;
}

/**
 * Net Worth Provider
 * Provides net worth state and actions to child components
 */
export function NetWorthProvider({ children }: NetWorthProviderProps) {
  // This is a placeholder - the actual implementation will be in use-net-worth-capability.ts
  // The context is defined here to establish the contract
  return (
    <NetWorthContext.Provider value={null as unknown as NetWorthContextType}>
      {children}
    </NetWorthContext.Provider>
  );
}

/**
 * Hook to access net worth context
 * @throws Error if used outside of NetWorthProvider
 */
export function useNetWorthContext(): NetWorthContextType {
  const context = useContext(NetWorthContext);
  if (context === undefined) {
    throw new Error('useNetWorthContext must be used within a NetWorthProvider');
  }
  return context;
}