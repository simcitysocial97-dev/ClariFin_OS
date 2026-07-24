/**
 * Capabilities Index - Central export for all capability modules
 *
 * This file provides clean import paths for all capability hooks.
 * Note: Context-based providers are not currently used - workspaces use hooks directly.
 */

// Transaction capability
export {
  useTransactionCapability,
  type TransactionCapabilityState,
  type TransactionCapabilityActions,
  type TransactionCapabilityReturn,
} from './use-transaction-capability';

// Net Worth capability
export {
  useNetWorthCapability,
  type NetWorthCapabilityState,
  type NetWorthCapabilityActions,
  type NetWorthCapabilityReturn,
} from './use-net-worth-capability';

// Accounts capability
export {
  useAccountsCapability,
  type AccountsCapabilityState,
  type AccountsCapabilityActions,
  type AccountsCapabilityReturn,
} from './use-accounts-capability';

// Loans capability
export {
  useLoansCapability,
  type LoansCapabilityState,
  type LoansCapabilityActions,
  type LoansCapabilityReturn,
} from './use-loans-capability';

// Credit Cards capability
export {
  useCreditCardsCapability,
  type CreditCardsCapabilityState,
  type CreditCardsCapabilityActions,
  type CreditCardsCapabilityReturn,
} from './use-credit-cards-capability';

// Investments capability
export {
  useInvestmentsCapability,
  type InvestmentsCapabilityState,
  type InvestmentsCapabilityActions,
  type InvestmentsCapabilityReturn,
} from './use-investments-capability';

// Reconciliation capability
export {
  useReconciliationCapability,
  type ReconciliationCapabilityState,
  type ReconciliationCapabilityActions,
  type ReconciliationCapabilityReturn,
} from './use-reconciliation-capability';

// Behaviour capability
export {
  useBehaviourCapability,
  type BehaviourCapabilityState,
  type BehaviourCapabilityActions,
  type BehaviourCapabilityReturn,
} from './use-behaviour-capability';

// Forecast capability
export {
  useForecastCapability,
  type ForecastCapabilityState,
  type ForecastCapabilityActions,
  type ForecastCapabilityReturn,
} from './use-forecast-capability';