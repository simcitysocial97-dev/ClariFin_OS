/**
 * Financial Engine Types
 * ======================
 *
 * TypeScript interfaces for cashflow, net worth, projections, and snapshots.
 * All monetary values are in paise (integer).
 */

// ============================================================
// Cashflow Types
// ============================================================

/**
 * Single month cashflow data
 * From cashflow_engine.compute_monthly_cashflow
 */
export interface MonthlyCashflow {
  month: string;
  total_income_paise: number;
  total_expense_paise: number;
  net_cashflow_paise: number;
  savings_rate: number;
  transaction_count: number;
}

/**
 * Category breakdown item for cashflow
 */
export interface CategoryBreakdown {
  category: string;
  amount_paise: number;
}

/**
 * Account breakdown item for cashflow
 */
export interface AccountBreakdown {
  account: string;
  income_paise: number;
  expense_paise: number;
}

/**
 * Detailed breakdown for a month
 * From cashflow_engine.compute_cashflow_breakdown
 */
export interface CashflowBreakdown {
  month: string;
  total_income_paise: number;
  total_expense_paise: number;
  fixed_expenses_paise: number;
  variable_expenses_paise: number;
  income_by_source: CategoryBreakdown[];
  expense_by_category: CategoryBreakdown[];
  daily_burn_rate_paise: number;
  liquid_assets_paise: number;
  runway_months: number;
  days_in_month: number;
}

/**
 * Best/worst month info
 */
export interface MonthInfo {
  month: string;
  net_cashflow_paise: number;
}

/**
 * Comprehensive cashflow summary
 * From cashflow_engine.compute_cashflow_summary
 */
export interface CashflowSummary {
  avg_monthly_income_paise: number;
  avg_monthly_expense_paise: number;
  avg_savings_rate: number;
  best_month: MonthInfo | null;
  worst_month: MonthInfo | null;
  months_positive: number;
  months_negative: number;
  total_months: number;
  trend: 'improving' | 'declining' | 'stable';
}

// ============================================================
// Net Worth Types
// ============================================================

/**
 * Asset breakdown structure
 */
export interface AssetBreakdown {
  bank_accounts_paise: number;
  fixed_deposits_paise: number;
  investments_paise: number;
}

/**
 * Liability breakdown structure
 */
export interface LiabilityBreakdown {
  loans_paise: number;
  credit_cards_paise: number;
}

/**
 * Current net worth with breakdowns
 * From networth_engine.compute_net_worth
 */
export interface NetWorth {
  total_assets_paise: number;
  total_liabilities_paise: number;
  net_worth_paise: number;
  asset_breakdown: AssetBreakdown;
  liability_breakdown: LiabilityBreakdown;
}

/**
 * Single point in net worth history
 * From networth_engine.compute_net_worth_trend
 */
export interface NetWorthTrend {
  month: string;
  net_worth_paise: number;
  total_assets_paise: number;
  total_liabilities_paise: number;
}

// ============================================================
// Snapshot Types
// ============================================================

/**
 * Frozen monthly record from monthly_snapshots table
 */
export interface MonthlySnapshot {
  id: number;
  month: string;
  total_income_paise: number;
  total_expense_paise: number;
  total_emi_paise: number;
  total_investment_paise: number;
  net_cashflow_paise: number;
  net_worth_paise: number;
  savings_rate: number;
  data_json: string;
  created_at: string;
}

/**
 * Parsed data_json from MonthlySnapshot
 */
export interface SnapshotData {
  income_by_category: CategoryBreakdown[];
  expense_by_category: CategoryBreakdown[];
  account_breakdown: AccountBreakdown[];
  transaction_count: number;
  net_worth_breakdown: {
    total_assets_paise: number;
    total_liabilities_paise: number;
    asset_breakdown: AssetBreakdown;
    liability_breakdown: LiabilityBreakdown;
  };
}

// ============================================================
// Projection Types
// ============================================================

/**
 * Asset breakdown in projections
 */
export interface ProjectionAssetBreakdown {
  cash_paise: number;
  equity_paise: number;
  debt_paise: number;
}

/**
 * Single projected month
 * From projection_engine.project_net_worth
 */
export interface NetWorthProjection {
  month: string;
  projected_net_worth_paise: number;
  projected_assets_paise: number;
  projected_liabilities_paise: number;
  asset_breakdown: ProjectionAssetBreakdown;
}

/**
 * Assumptions used in projections
 */
export interface ProjectionAssumptions {
  equity_return_percent: number;
  debt_return_percent: number;
  savings_basis: string;
  monthly_compounding: boolean;
  loan_interest_calculation: string;
  months_projected: number;
  scenario_modifications?: {
    increased_savings_by_paise: number;
    extra_loan_payment_paise: number;
    extra_loan_payment_loan_id: number | null;
    new_sip_paise: number;
    new_sip_type: string;
  };
}

/**
 * Summary of projections
 */
export interface ProjectionSummary {
  starting_net_worth_paise: number;
  ending_net_worth_paise: number;
  net_worth_change_paise: number;
}

/**
 * Full net worth projection response
 */
export interface NetWorthProjectionResponse {
  projections: NetWorthProjection[];
  assumptions: ProjectionAssumptions;
  summary: ProjectionSummary;
}

/**
 * Goal calculator result
 * From projection_engine.project_goal
 */
export interface GoalProjection {
  months_needed: number | null;
  projected_date: string | null;
  total_contributed_paise: number;
  total_returns_paise: number;
  target_achievable: boolean;
  target_already_achieved?: boolean;
  final_projected_amount_paise?: number;
  reason?: string;
}

/**
 * Goal projection request
 */
export interface GoalProjectionRequest {
  monthly_savings_paise: number;
  target_paise: number;
  current_paise?: number;
  annual_return?: number;
}

/**
 * What-if scenario comparison result
 * From projection_engine.what_if_analysis
 */
export interface WhatIfResult {
  baseline: NetWorthProjection[];
  modified: NetWorthProjection[];
  difference_at_1y_paise: number;
  difference_at_3y_paise: number;
  difference_at_5y_paise: number;
  percentage_improvement_5y: number;
  baseline_summary: ProjectionSummary;
  modified_summary: ProjectionSummary;
  assumptions: ProjectionAssumptions;
}

/**
 * What-if scenario request
 */
export interface WhatIfScenarioRequest {
  increase_savings_by_paise?: number;
  extra_loan_payment_paise?: number;
  extra_loan_payment_loan_id?: number | null;
  new_sip_paise?: number;
  new_sip_type?: 'equity' | 'debt';
  equity_return_override_percent?: number | null;
}

/**
 * Loan payoff forecast
 * From projection_engine.project_loan_payoff
 */
export interface LoanPayoffProjection {
  loan_id?: number;
  loan_name?: string | null;
  lender?: string | null;
  payoff_date: string | null;
  remaining_months: number;
  total_remaining_interest_paise: number;
  remaining_principal_paise: number;
  is_closed: boolean;
  error?: string;
}

// ============================================================
// Response Types
// ============================================================

/**
 * Response from GET /api/cashflow/monthly
 */
export interface MonthlyCashflowResponse {
  months: MonthlyCashflow[];
  count: number;
}

/**
 * Response from GET /api/networth/trend
 */
export interface NetWorthTrendResponse {
  trend: NetWorthTrend[];
  count: number;
}

/**
 * Response from GET /api/snapshots
 */
export interface SnapshotsResponse {
  snapshots: MonthlySnapshot[];
  total: number;
}

/**
 * Response from POST /api/snapshots/backfill
 */
export interface SnapshotBackfillResponse {
  generated_count: number;
  message: string;
}