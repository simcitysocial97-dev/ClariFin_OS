/**
 * Behaviour ViewModel - Stage 4 Behaviour Intelligence Workspace
 *
 * This is the canonical ViewModel for the Behaviour Intelligence Workspace.
 * It follows the architecture flow: Backend → API → DTO → Mapper → ViewModel
 *
 * All amounts are in paise (₹1.00 = 100 paise) for financial determinism.
 * All scores are in basis points (0-10000 for 0-100%).
 * This ViewModel is presentation-only and must be mapped from backend DTOs.
 */

// ===== Behaviour Score Types =====
export interface BehaviourScoreViewModel {
  /** Score in basis points (0-10000) */
  score: number;
  /** Score label (e.g., 'Healthy', 'Warning') */
  label: string;
  /** Factors contributing to score */
  factors: string[];
}

// ===== Spending Pattern Types =====
export interface SpendingPatternViewModel {
  /** Category name */
  category: string;
  /** Total spending in paise */
  amount_paise: number;
  /** Percentage of total spending (0-100) */
  percentage: number;
  /** Trend direction (increasing, decreasing, stable) */
  trend: string;
  /** Month-over-month change percentage */
  month_over_month_change: number;
}

// ===== Savings Rate Types =====
export interface SavingsRateViewModel {
  /** Savings rate in basis points (0-10000) */
  savings_rate_bps: number;
  /** Total income in paise */
  income_paise: number;
  /** Total savings in paise */
  savings_paise: number;
  /** Analysis period (e.g., '1M', '3M', '1Y') */
  period: string;
}

// ===== Debt Health Types =====
export interface DebtHealthViewModel {
  /** Debt-to-income ratio in basis points */
  debt_to_income_bps: number;
  /** Total debt in paise */
  total_debt_paise: number;
  /** Total income in paise */
  total_income_paise: number;
  /** Health score in basis points (0-10000) */
  health_score: number;
}

// ===== Wellness Radar Types =====
export interface WellnessRadarViewModel {
  /** Dimension name (e.g., 'Savings', 'Debt', 'Income') */
  dimension: string;
  /** Score in basis points (0-10000) */
  score: number;
  /** Maximum possible score */
  max_score: number;
}

// ===== Behaviour Insight Types =====
export type BehaviourInsightType = 'positive' | 'warning' | 'info' | 'alert';
export type BehaviourInsightSeverity = 'low' | 'medium' | 'high';

export interface BehaviourInsightViewModel {
  /** Insight type */
  type: BehaviourInsightType;
  /** Insight severity */
  severity: BehaviourInsightSeverity;
  /** Human-readable insight message */
  message: string;
  /** URL for detailed view or action */
  action_url?: string;
}

// ===== Behaviour Evidence Types =====
export interface BehaviourEvidenceItemViewModel {
  /** Evidence type (transaction, pattern, score) */
  type: string;
  /** Human-readable summary */
  summary: string;
  /** Source reference */
  source: string;
  /** Confidence score (0-100) */
  confidence?: number;
}

export interface BehaviourCalculationStepViewModel {
  /** Step name */
  name: string;
  /** Step description */
  description: string;
  /** Input values for the step */
  inputs: Record<string, unknown>;
  /** Output values from the step */
  outputs: Record<string, unknown>;
}

export interface BehaviourEvidenceChainViewModel {
  /** Overall summary of the calculation */
  summary: string;
  /** List of evidence items */
  evidence: BehaviourEvidenceItemViewModel[];
  /** Calculation chain steps */
  calculation_steps: BehaviourCalculationStepViewModel[];
  /** Source references for traceability */
  source_references: string[];
  /** Overall confidence (0-100) */
  confidence_score: number;
}

// ===== Behaviour Filters Types =====
export interface BehaviourFiltersViewModel {
  /** Period filter */
  period?: string;
}

// ===== Behaviour Navigation Types =====
export interface BehaviourNavigationViewModel {
  /** Deep link to this view */
  deep_link: string;
  /** Cross-references to related workspaces */
  cross_references: {
    cashflow?: string;
    net_worth?: string;
  };
}

// ===== Main Behaviour ViewModel =====
export interface BehaviourViewModel {
  /** Overall wellness score */
  wellness_score: BehaviourScoreViewModel;
  /** Spending pattern analysis */
  spending_patterns: SpendingPatternViewModel[];
  /** Savings rate analysis */
  savings_rate?: SavingsRateViewModel;
  /** Debt health analysis */
  debt_health?: DebtHealthViewModel;
  /** Wellness radar data */
  wellness_radar: WellnessRadarViewModel[];
  /** List of insights about behaviour */
  insights: BehaviourInsightViewModel[];
  /** Evidence chain for explainability */
  evidence_chain?: BehaviourEvidenceChainViewModel;
  /** Filters for the view */
  filters: BehaviourFiltersViewModel;
  /** Navigation information */
  navigation: BehaviourNavigationViewModel;
}

// ===== Type Exports =====
export type BehaviourViewModelId = string;