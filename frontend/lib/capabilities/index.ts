/**
 * Capabilities Index - Central export for all capability modules
 *
 * This file provides clean import paths for all capability hooks and context.
 */

// Transaction capability
export {
  useTransactionCapability,
  type TransactionCapabilityState,
  type TransactionCapabilityActions,
  type TransactionCapabilityReturn,
} from './use-transaction-capability';

// Re-export context
export {
  TransactionContext,
  TransactionProvider,
  useTransactionContext,
  type TransactionContextType,
} from './transaction-context';

// Net Worth capability
export {
  useNetWorthCapability,
  type NetWorthCapabilityState,
  type NetWorthCapabilityActions,
  type NetWorthCapabilityReturn,
} from './use-net-worth-capability';

// Re-export context
export {
  NetWorthContext,
  NetWorthProvider,
  useNetWorthContext,
  type NetWorthContextType,
} from './net-worth-context';

// Accounts capability
export {
  useAccountsCapability,
  type AccountsCapabilityState,
  type AccountsCapabilityActions,
  type AccountsCapabilityReturn,
} from './use-accounts-capability';

// Re-export context
export {
  AccountsContext,
  AccountsProvider,
  useAccountsContext,
  type AccountsContextType,
} from './accounts-context';
