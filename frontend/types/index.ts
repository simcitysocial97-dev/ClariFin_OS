/**
 * Types Index - Central export for all TypeScript types
 *
 * This file provides clean import paths for all ViewModels and types.
 * All types are exported from this single location.
 */

// Transaction ViewModel
export {
  type TransactionViewModel,
  type TransactionViewModelId,
  type TransactionSummary,
  type MoneyViewModel,
  type EvidenceItem,
  type EvidenceSource,
  type CalculationStep,
  type ImportLineage,
} from './transaction-view-model';

// Transaction types
export {
  type Transaction,
  type AccountBalance,
  type RunningBalanceEntry,
  type StatementValidation,
  type Metadata,
  type ParseResult,
  type Filters,
  isTransactionWithId,
  isTransactionFromAPI,
} from './transaction';

// Card types
export { type CreditCard } from './card';

// Financial types
export {
  type NetWorth,
  type NetWorthTrendResponse,
  type MonthlyCashflowResponse,
  type CashflowBreakdown,
  type BehaviorScore,
} from './financial';

// API types
export { type paths, type components, type operations } from './api-generated';