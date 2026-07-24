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

// Net Worth ViewModel
export {
  type NetWorthViewModel,
  type NetWorthViewModelId,
  type NetWorthCompositionViewModel,
  type NetWorthBreakdownItemViewModel,
  type NetWorthHistoricalSnapshotViewModel,
  type NetWorthTrendViewModel,
  type NetWorthInsightViewModel,
  type NetWorthEvidenceChainViewModel,
  type NetWorthFiltersViewModel,
  type NetWorthNavigationViewModel,
} from './net-worth-view-model';

// Cashflow ViewModel
export {
  type CashflowViewModel,
  type CashflowViewModelId,
  type CashflowTrendViewModel,
  type CashflowMonthlyViewModel,
  type CashflowCategoryViewModel,
  type CashflowTransactionViewModel,
  type CashflowInsightViewModel,
  type CashflowEvidenceChainViewModel,
  type CashflowFiltersViewModel,
  type CashflowNavigationViewModel,
} from './cashflow-view-model';

// Accounts ViewModel
export {
  type AccountsViewModel,
  type AccountsViewModelId,
  type AccountDetailViewModel,
  type AccountType,
  type AccountStatus,
  type BalanceHistoryViewModel,
  type AccountTransactionViewModel,
  type AccountTypeBreakdownViewModel,
  type AccountInsightViewModel,
  type AccountEvidenceChainViewModel,
  type AccountFiltersViewModel,
  type AccountNavigationViewModel,
} from './accounts-view-model';

// Loans ViewModel
export {
  type LoansViewModel,
  type LoansViewModelId,
  type LoanType,
  type LoanStatus,
  type AmortizationEntryViewModel,
  type LoanSummaryViewModel,
  type PaymentProgressViewModel,
  type InterestAnalysisViewModel,
  type LoanInsightViewModel,
  type LoanEvidenceChainViewModel,
  type LoanFiltersViewModel,
  type LoanNavigationViewModel,
} from './loans-view-model';

// Credit Cards ViewModel
export {
  type CreditCardsViewModel,
  type CreditCardsViewModelId,
  type CreditCardStatus,
  type StatementHistoryViewModel,
  type UtilizationViewModel,
  type SpendingByCategoryViewModel,
  type CreditCardSummaryViewModel,
  type CreditCardInsightViewModel,
  type CreditCardEvidenceChainViewModel,
  type CreditCardFiltersViewModel,
  type CreditCardNavigationViewModel,
} from './credit-cards-view-model';

// Investments ViewModel
export {
  type InvestmentsViewModel,
  type InvestmentsViewModelId,
  type InvestmentType,
  type InvestmentStatus,
  type PerformanceViewModel,
  type AssetAllocationViewModel,
  type HoldingViewModel,
  type InvestmentSummaryViewModel,
  type InvestmentInsightViewModel,
  type InvestmentEvidenceChainViewModel,
  type InvestmentFiltersViewModel,
  type InvestmentNavigationViewModel,
} from './investments-view-model';

// Reconciliation ViewModel
export {
  type ReconciliationViewModel,
  type ReconciliationViewModelId,
  type ReconciliationStatus,
  type DiscrepancyViewModel,
  type StatusOverviewViewModel,
  type AuditTrailEntryViewModel,
  type ReconciliationSummaryViewModel,
  type ReconciliationInsightViewModel,
  type ReconciliationEvidenceChainViewModel,
  type ReconciliationFiltersViewModel,
  type ReconciliationNavigationViewModel,
} from './reconciliation-view-model';

// Behaviour ViewModel
export {
  type BehaviourViewModel,
  type BehaviourViewModelId,
  type BehaviourScoreViewModel,
  type SpendingPatternViewModel,
  type SavingsRateViewModel,
  type DebtHealthViewModel,
  type WellnessRadarViewModel,
  type BehaviourInsightViewModel,
  type BehaviourEvidenceChainViewModel,
  type BehaviourFiltersViewModel,
  type BehaviourNavigationViewModel,
} from './behaviour-view-model';

// Forecast ViewModel
export {
  type ForecastViewModel,
  type ForecastViewModelId,
  type NetWorthProjectionViewModel,
  type CashflowProjectionViewModel,
  type ForecastScenarioViewModel,
  type ConfidenceLevel,
  type ConfidenceIntervalViewModel,
  type ForecastSummaryViewModel,
  type ForecastInsightViewModel,
  type ForecastEvidenceChainViewModel,
  type ForecastFiltersViewModel,
  type ForecastNavigationViewModel,
} from './forecast-view-model';

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