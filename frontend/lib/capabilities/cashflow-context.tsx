/**
 * Cashflow Capability Context - Stage 4 Cashflow Truth Workspace
 *
 * React context for cashflow state management.
 * This is the canonical state container for the Cashflow Truth Workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { createContext, useContext, ReactNode } from 'react';
import type { CashflowViewModel } from '@/types/cashflow-view-model';

/**
 * Cashflow capability state interface
 */
export interface CashflowCapabilityState {
  // Data
  cashflow: CashflowViewModel | null;
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
  categories: string[];
  merchants: string[];
  amountRange: { min?: number; max?: number } | null;

  // Evidence drawer
  isEvidenceDrawerOpen: boolean;
}

/**
 * Cashflow capability actions interface
 */
export interface CashflowCapabilityActions {
  // Fetch
  fetchCashflow: () => Promise<void>;
  refresh: () => Promise<void>;
  recoverFromError: () => Promise<void>;

  // Filters
  setDateRange: (filter: { from?: string; to?: string } | null) => void;
  setCategories: (categories: string[]) => void;
  setMerchants: (merchants: string[]) => void;
  setAmountRange: (range: { min?: number; max?: number } | null) => void;
  clearFilters: () => void;
  applyFilters: () => Promise<void>;

  // Evidence drawer
  toggleEvidenceDrawer: () => void;
}

/**
 * Combined context type
 */
export type CashflowContextType = CashflowCapabilityState & CashflowCapabilityActions;

/**
 * Cashflow Context
 */
export const CashflowContext = createContext<CashflowContextType | undefined>(undefined);

/**
 * Cashflow Provider Props
 */
interface CashflowProviderProps {
  children: ReactNode;
}

/**
 * Cashflow Provider
 * Provides cashflow state and actions to child components
 */
export function CashflowProvider({ children }: CashflowProviderProps) {
  // This is a placeholder - the actual implementation will be in use-cashflow-capability.ts
  // The context is defined here to establish the contract
  return (
    <CashflowContext.Provider value={null as unknown as CashflowContextType}>
      {children}
    </CashflowContext.Provider>
  );
}

/**
 * Hook to access cashflow context
 * @throws Error if used outside of CashflowProvider
 */
export function useCashflowContext(): CashflowContextType {
  const context = useContext(CashflowContext);
  if (context === undefined) {
    throw new Error('useCashflowContext must be used within a CashflowProvider');
  }
  return context;
}