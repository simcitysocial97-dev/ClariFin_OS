/**
 * Forecast ViewModel - Stage 4 Forecast Intelligence Workspace
 *
 * This is the canonical ViewModel for the Forecast Intelligence Workspace.
 * It follows the architecture flow: Backend → API → DTO → Mapper → ViewModel
 *
 * All amounts are in paise (₹1.00 = 100 paise) for financial determinism.
 * All confidence levels are in basis points (0-10000 for 0-100%).
 * This ViewModel is presentation-only and must be mapped from backend DTOs.
 */

// ===== Forecast Projection Types =====
export interface NetWorthProjectionViewModel {
  /** Projection date (ISO format) */
  date: string;
  /** Projected net worth in paise */
  projected_paise: number;
  /** Lower confidence bound in paise */
  lower_bound_paise: number;
  /** Upper confidence bound in paise */
  upper_bound_paise: number;
}

export interface CashflowProjectionViewModel {
  /** Month label (e.g., '2026-08') */
  month: string;
  /** Projected income in paise */
  income_paise: number;
  /** Projected expenses in paise */
  expenses_paise: number;
  /** Projected net cashflow in paise */
  net_paise: number;
}

// ===== Forecast Scenario Types =====
export interface ForecastScenarioViewModel {
  /** Scenario name */
  name: string;
  /** Scenario description */
  description: string;
  /** Probability in basis points (0-10000) */
  probability_bps: number;
  /** Net worth projections for this scenario */
  net_worth_projections: NetWorthProjectionViewModel[];
  /** Cashflow projections for this scenario */
  cashflow_projections: CashflowProjectionViewModel[];
}

// ===== Confidence Interval Types =====
export type ConfidenceLevel = 90 | 95 | 99;

export interface ConfidenceIntervalViewModel {
  /** Confidence level (90, 95, or 99) */
  level: ConfidenceLevel;
  /** Lower bound in paise */
  lower_paise: number;
  /** Upper bound in paise */
  upper_paise: number;
}

// ===== Forecast Summary Types =====
export interface ForecastSummaryViewModel {
  /** Forecast horizon in months */
  horizon_months: number;
  /** Current net worth in paise */
  current_net_worth_paise: number;
  /** Final projected net worth in paise */
  projected_net_worth_paise: number;
  /** Projected growth in paise */
  projected_growth_paise: number;
  /** Projected growth percentage */
  projected_growth_percentage: number;
}

// ===== Forecast Insight Types =====
export type ForecastInsightType = 'positive' | 'warning' | 'info' | 'alert';
export type ForecastInsightSeverity = 'low' | 'medium' | 'high';

export interface ForecastInsightViewModel {
  /** Insight type */
  type: ForecastInsightType;
  /** Insight severity */
  severity: ForecastInsightSeverity;
  /** Human-readable insight message */
  message: string;
  /** URL for detailed view or action */
  action_url?: string;
}

// ===== Forecast Evidence Types =====
export interface ForecastEvidenceItemViewModel {
  /** Evidence type (historical, model, assumption) */
  type: string;
  /** Human-readable summary */
  summary: string;
  /** Source reference */
  source: string;
  /** Confidence score (0-100) */
  confidence?: number;
}

export interface ForecastCalculationStepViewModel {
  /** Step name */
  name: string;
  /** Step description */
  description: string;
  /** Input values for the step */
  inputs: Record<string, unknown>;
  /** Output values from the step */
  outputs: Record<string, unknown>;
}

export interface ForecastEvidenceChainViewModel {
  /** Overall summary of the calculation */
  summary: string;
  /** List of evidence items */
  evidence: ForecastEvidenceItemViewModel[];
  /** Calculation chain steps */
  calculation_steps: ForecastCalculationStepViewModel[];
  /** Source references for traceability */
  source_references: string[];
  /** Overall confidence (0-100) */
  confidence_score: number;
}

// ===== Forecast Filters Types =====
export interface ForecastFiltersViewModel {
  /** Forecast horizon in months */
  horizon?: number;
  /** Scenarios filter */
  scenarios?: string[];
  /** Metric types filter */
  metric_types?: string[];
}

// ===== Forecast Navigation Types =====
export interface ForecastNavigationViewModel {
  /** Deep link to this view */
  deep_link: string;
  /** Cross-references to related workspaces */
  cross_references: {
    net_worth?: string;
    cashflow?: string;
  };
}

// ===== Main Forecast ViewModel =====
export interface ForecastViewModel {
  /** Forecast summary */
  summary: ForecastSummaryViewModel;
  /** Net worth projections */
  net_worth_projections: NetWorthProjectionViewModel[];
  /** Cashflow projections */
  cashflow_projections: CashflowProjectionViewModel[];
  /** Forecast scenarios */
  scenarios: ForecastScenarioViewModel[];
  /** Confidence intervals */
  confidence_intervals: ConfidenceIntervalViewModel[];
  /** List of insights about forecast */
  insights: ForecastInsightViewModel[];
  /** Evidence chain for explainability */
  evidence_chain?: ForecastEvidenceChainViewModel;
  /** Filters for the view */
  filters: ForecastFiltersViewModel;
  /** Navigation information */
  navigation: ForecastNavigationViewModel;
}

// ===== Type Exports =====
export type ForecastViewModelId = string;