/**
 * API Response Types
 * 
 * These types define the structure of API responses from the FastAPI backend.
 */

import type { Transaction } from './transaction';

// Re-export all new types for convenience
export type {
  // Loan types
  Loan,
  LoanCreate,
  LoanUpdate,
  LoanPayment,
  LoanPaymentCreate,
  AmortizationEntry,
  AmortizationSchedule,
  LoanSummary,
  PrepaymentSimulationRequest,
  PrepaymentResult,
  LoansResponse,
  LoanPaymentsResponse,
} from './loan';

export type {
  // Investment types
  Investment,
  InvestmentCreate,
  InvestmentUpdate,
  InvestmentSummary,
  AssetAllocation,
  AssetAllocationResponse,
  InvestmentsResponse,
} from './investment';

export type {
  // Income source types
  IncomeSource,
  IncomeSourceCreate,
  IncomeSourceUpdate,
  IncomeSourcesResponse,
} from './income';

export type {
  // Recurring transaction types
  RecurringTransaction,
  RecurringTransactionCreate,
  RecurringTransactionUpdate,
  DetectedRecurring,
  RecurringDetectionResponse,
  RecurringTransactionsResponse,
} from './recurring';

export type {
  // Financial engine types
  MonthlyCashflow,
  CategoryBreakdown,
  AccountBreakdown,
  CashflowBreakdown,
  MonthInfo,
  CashflowSummary,
  AssetBreakdown,
  LiabilityBreakdown,
  NetWorth,
  NetWorthTrend,
  MonthlySnapshot,
  SnapshotData,
  ProjectionAssetBreakdown,
  NetWorthProjection,
  ProjectionAssumptions,
  ProjectionSummary,
  NetWorthProjectionResponse,
  GoalProjection,
  GoalProjectionRequest,
  WhatIfResult,
  WhatIfScenarioRequest,
  LoanPayoffProjection,
  MonthlyCashflowResponse,
  NetWorthTrendResponse,
  SnapshotsResponse,
  SnapshotBackfillResponse,
} from './financial';

// ===== Pagination Types =====

export interface Pagination {
  page: number;
  per_page: number;
  total: number;
  has_next: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: Pagination;
}

export interface PaginatedTransactionsResponse {
  transactions: Transaction[];
  pagination: Pagination;
}

// ===== Category Types =====

export interface CategorySummary {
  category: string;
  amount: number;
  amount_display: string;
  count: number;
  count_display: string;
  percentage: number;
  percentage_display: string;
}

export interface MonthlyBreakdown {
  month: string;
  amount: number;
}

export interface UncategorizedPattern {
  description: string;
  count: number;
  total: number;
  total_display?: string;
}

export interface CategoriesResponse {
  summary: CategorySummary[];
  monthly_breakdown: MonthlyBreakdown[];
  drill_transactions: Transaction[];
  uncategorized_patterns: UncategorizedPattern[];
}

// ===== Analytics Types =====

export interface DayOfWeekData {
  day: string;
  amount: number;
  count: number;
}

export interface MerchantData {
  name: string;
  merchant?: string;  // API may return either
  amount: number;
  amount_display: string;
  count: number;
  count_display?: string;
}

export interface RecurringCharge {
  description: string;
  frequency: number;
  frequency_display?: string;
  avg_amount: number;
  avg_display: string;
  annual_display: string;
}

export interface LargestTransaction {
  rank: number;
  id?: number | string;
  date: string;
  date_display: string;
  description: string;
  description_display?: string;
  amount: number;
  amount_display: string;
  bank: string;
}

export interface AnalyticsData {
  highest_month: string;
  highest_month_amount: string;
  avg_monthly: number;
  avg_monthly_display: string;
  biggest_txn_amount: string;
  biggest_txn_desc: string;
  unique_merchants: number;
  unique_merchants_display: string;
  transaction_count?: number;  // Used by analytics page for data check
  spending_trend: MonthlyBreakdown[];
  day_of_week_data: DayOfWeekData[];
  top_merchants: MerchantData[];
  recurring_charges: RecurringCharge[];
  largest_transactions: LargestTransaction[];
}

// ===== Chart Data Types =====

export interface ChartDataPoint {
  name: string;
  value: number;
  amount?: number;
  month?: string;
  bank?: string;
}

export interface SpendingTrendPoint {
  month: string;
  amount: number;
  average?: number;
}