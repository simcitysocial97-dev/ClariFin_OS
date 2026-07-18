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
