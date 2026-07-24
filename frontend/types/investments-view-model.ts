/**
 * Investments ViewModel - Stage 4 Investments Intelligence Workspace
 *
 * This is the canonical ViewModel for the Investments Intelligence Workspace.
 * It follows the architecture flow: Backend → API → DTO → Mapper → ViewModel
 *
 * All amounts are in paise (₹1.00 = 100 paise) for financial determinism.
 * All returns are in basis points (1% = 100 bps).
 * This ViewModel is presentation-only and must be mapped from backend DTOs.
 */

// ===== Investment Types =====
export type InvestmentType = 'stocks' | 'mutual_funds' | 'bonds' | 'fd' | 'ppf' | 'gold' | 'other';
export type InvestmentStatus = 'active' | 'closed' | 'matured';

// ===== Performance Types =====
export interface PerformanceViewModel {
  /** Date (ISO format) */
  date: string;
  /** Portfolio value in paise */
  value_paise: number;
  /** Returns in basis points since inception */
  returns_bps: number;
  /** Day change in basis points */
  day_change_bps: number;
}

// ===== Asset Allocation Types =====
export interface AssetAllocationViewModel {
  /** Investment type */
  type: InvestmentType;
  /** Total value in paise */
  value_paise: number;
  /** Percentage of total (0-100) */
  percentage: number;
  /** Number of holdings */
  count: number;
}

// ===== Holding Types =====
export interface HoldingViewModel {
  /** Holding identifier */
  id: string;
  /** Holding name */
  name: string;
  /** Investment type */
  type: InvestmentType;
  /** Stock/mutual fund symbol */
  symbol?: string;
  /** Number of units held */
  quantity: number;
  /** Purchase price per unit in paise */
  purchase_price_paise: number;
  /** Current price per unit in paise */
  current_price_paise: number;
  /** Current value in paise */
  current_value_paise: number;
  /** Total invested in paise */
  invested_paise: number;
  /** Absolute returns in paise */
  returns_paise: number;
  /** Returns percentage */
  returns_percentage: number;
  /** Last updated timestamp (ISO) */
  last_updated: string;
}

// ===== Investment Summary Types =====
export interface InvestmentSummaryViewModel {
  /** Investment identifier */
  id: string;
  /** Investment name */
  name: string;
  /** Investment type */
  type: InvestmentType;
  /** Institution name */
  institution: string;
  /** Current value in paise */
  current_value_paise: number;
  /** Total invested in paise */
  invested_paise: number;
  /** Absolute returns in paise */
  returns_paise: number;
  /** Returns percentage */
  returns_percentage: number;
  /** Year-to-date returns in basis points */
  returns_ytd_bps: number;
  /** Investment status */
  status: InvestmentStatus;
}

// ===== Investment Insight Types =====
export type InvestmentInsightType = 'positive' | 'warning' | 'info' | 'alert';
export type InvestmentInsightSeverity = 'low' | 'medium' | 'high';

export interface InvestmentInsightViewModel {
  /** Insight type */
  type: InvestmentInsightType;
  /** Insight severity */
  severity: InvestmentInsightSeverity;
  /** Human-readable insight message */
  message: string;
  /** URL for detailed view or action */
  action_url?: string;
}

// ===== Investment Evidence Types =====
export interface InvestmentEvidenceItemViewModel {
  /** Evidence type (holding, price, calculation) */
  type: string;
  /** Human-readable summary */
  summary: string;
  /** Source reference */
  source: string;
  /** Confidence score (0-100) */
  confidence?: number;
}

export interface InvestmentCalculationStepViewModel {
  /** Step name */
  name: string;
  /** Step description */
  description: string;
  /** Input values for the step */
  inputs: Record<string, unknown>;
  /** Output values from the step */
  outputs: Record<string, unknown>;
}

export interface InvestmentEvidenceChainViewModel {
  /** Overall summary of the calculation */
  summary: string;
  /** List of evidence items */
  evidence: InvestmentEvidenceItemViewModel[];
  /** Calculation chain steps */
  calculation_steps: InvestmentCalculationStepViewModel[];
  /** Source references for traceability */
  source_references: string[];
  /** Overall confidence (0-100) */
  confidence_score: number;
}

// ===== Investment Filters Types =====
export interface InvestmentFiltersViewModel {
  /** Investment types filter */
  investment_types?: InvestmentType[];
  /** Institutions filter */
  institutions?: string[];
  /** Statuses filter */
  statuses?: InvestmentStatus[];
}

// ===== Investment Navigation Types =====
export interface InvestmentNavigationViewModel {
  /** Deep link to this view */
  deep_link: string;
  /** Cross-references to related workspaces */
  cross_references: {
    net_worth?: string;
    accounts?: string;
  };
}

// ===== Main Investments ViewModel =====
export interface InvestmentsViewModel {
  /** List of investment summaries */
  investments: InvestmentSummaryViewModel[];
  /** Total value across all investments in paise */
  total_value_paise: number;
  /** Total invested in paise */
  total_invested_paise: number;
  /** Total returns in paise */
  total_returns_paise: number;
  /** Total number of active investments */
  investment_count: number;
  /** Performance history */
  performance: PerformanceViewModel[];
  /** Asset allocation breakdown */
  allocation: AssetAllocationViewModel[];
  /** Investment holdings */
  holdings: HoldingViewModel[];
  /** List of insights about investments */
  insights: InvestmentInsightViewModel[];
  /** Evidence chain for explainability */
  evidence_chain?: InvestmentEvidenceChainViewModel;
  /** Filters for the view */
  filters: InvestmentFiltersViewModel;
  /** Navigation information */
  navigation: InvestmentNavigationViewModel;
}

// ===== Type Exports =====
export type InvestmentsViewModelId = string;