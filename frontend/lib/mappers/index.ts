/**
 * Mappers Index - Central export for all mapper functions
 *
 * This file provides clean import paths for all mappers.
 */

// Transaction mapper
export {
  TransactionMapper,
  transactionMapper,
  type ITransactionMapper,
} from './transaction-mapper';

// Net Worth mapper
export {
  NetWorthMapper,
  netWorthMapper,
  type INetWorthMapper,
} from './net-worth-mapper';

// Cashflow mapper
export {
  CashflowMapper,
  cashflowMapper,
  type ICashflowMapper,
} from './cashflow-mapper';

// Accounts mapper
export {
  AccountsMapper,
  accountsMapper,
  type IAccountsMapper,
} from './accounts-mapper';

// Loans mapper
export {
  LoansMapper,
  loansMapper,
  type ILoansMapper,
} from './loans-mapper';

// Credit Cards mapper
export {
  CreditCardsMapper,
  creditCardsMapper,
  type ICreditCardsMapper,
} from './credit-cards-mapper';

// Investments mapper
export {
  InvestmentsMapper,
  investmentsMapper,
  type IInvestmentsMapper,
} from './investments-mapper';

// Reconciliation mapper
export {
  ReconciliationMapper,
  reconciliationMapper,
  type IReconciliationMapper,
} from './reconciliation-mapper';

// Behaviour mapper
export {
  BehaviourMapper,
  behaviourMapper,
  type IBehaviourMapper,
} from './behaviour-mapper';

// Forecast mapper
export {
  ForecastMapper,
  forecastMapper,
  type IForecastMapper,
} from './forecast-mapper';
