/**
 * Net Worth ViewModel - Stage 4 Net Worth Intelligence Workspace
 *
 * This is the canonical ViewModel for the Net Worth Intelligence Workspace.
 * It follows the architecture flow: Backend → API → DTO → Mapper → ViewModel
 *
 * All amounts are in paise (₹1.00 = 100 paise) for financial determinism.
 * This ViewModel is presentation-only and must be mapped from backend DTOs.
 */

// ===== Money Type (matches backend MoneyDTO) =====
export interface MoneyViewModel {
  paise: number;  // Total paise (e.g., 123456 = ₹1,234.56)
  rupees: number;  // Derived rupees value for display
}

// ===== Net Worth Composition Types =====
export interface NetWorthBreakdownItemViewModel {
  /** Unique account or asset identifier */
  id: string;
  /** Account or asset name for display */
  name: string;
  /** Account type (savings, current, investment, loan, credit_card) */
  type: string;
  /** Balance in paise (can be negative for liabilities) */
  balance_paise: number;
  /** Percentage of total net worth (0-100) */
  percentage: number;
  /** Contribution to net worth in paise */
  contribution_paise: number;
}

export interface NetWorthCompositionViewModel {
  /** Total assets in paise */
  total_assets_paise: number;
  /** Total liabilities in paise */
  total_liabilities_paise: number;
  /** List of asset accounts with their contributions */
  asset_breakdown: NetWorthBreakdownItemViewModel[];
  /** List of liability accounts with their contributions */
  liability_breakdown: NetWorthBreakdownItemViewModel[];
}

// ===== Net Worth Historical Snapshot Types =====
export interface NetWorthHistoricalSnapshotViewModel {
  /** Snapshot date (ISO format YYYY-MM-DD) */
  date: string;
  /** Net worth in paise on this date */
  net_worth_paise: number;
  /** Total assets in paise on this date */
  assets_paise: number;
  /** Total liabilities in paise on this date */
  liabilities_paise: number;
}

// ===== Net Worth Trend Types =====
export type NetWorthTrendDirection = 'up' | 'down' | 'flat';

export interface NetWorthTrendViewModel {
  /** Trend direction (up/down/flat) */
  direction: NetWorthTrendDirection;
  /** Percentage change from previous period */
  percentage_change: number;
  /** Time period for comparison (e.g., '1M', '3M', '1Y') */
  period: string;
}

// ===== Net Worth Insight Types =====
export type NetWorthInsightType = 'positive' | 'warning' | 'info' | 'alert';
export type NetWorthInsightSeverity = 'low' | 'medium' | 'high';

export interface NetWorthInsightViewModel {
  /** Insight type */
  type: NetWorthInsightType;
  /** Insight severity */
  severity: NetWorthInsightSeverity;
  /** Human-readable insight message */
  message: string;
  /** URL for detailed view or action */
  action_url?: string;
}

// ===== Net Worth Evidence Types =====
export interface NetWorthEvidenceItemViewModel {
  /** Evidence type (account, calculation, adjustment) */
  type: string;
  /** Human-readable summary */
  summary: string;
  /** Source reference */
  source: string;
  /** Confidence score (0-100) */
  confidence?: number;
}

export interface NetWorthCalculationStepViewModel {
  /** Step name */
  name: string;
  /** Step description */
  description: string;
  /** Input values for the step */
  inputs: Record<string, unknown>;
  /** Output values from the step */
  outputs: Record<string, unknown>;
}

export interface NetWorthEvidenceChainViewModel {
  /** Overall summary of the calculation */
  summary: string;
  /** List of evidence items */
  evidence: NetWorthEvidenceItemViewModel[];
  /** Calculation chain steps */
  calculation_steps: NetWorthCalculationStepViewModel[];
  /** Source references for traceability */
  source_references: string[];
  /** Overall confidence (0-100) */
  confidence_score: number;
}

// ===== Net Worth Filters Types =====
export interface NetWorthFiltersViewModel {
  /** Date range filter */
  date_range?: {
    from: string;
    to: string;
  };
  /** Account types filter */
  account_types?: string[];
  /** Period for comparison */
  period?: string;
}

// ===== Net Worth Navigation Types =====
export interface NetWorthNavigationViewModel {
  /** Deep link to this view */
  deep_link: string;
  /** Cross-references to related workspaces */
  cross_references: {
    accounts?: string;
    investments?: string;
    loans?: string;
    credit_cards?: string;
  };
}

// ===== Main Net Worth ViewModel =====
export interface NetWorthViewModel {
  /** Net worth in paise (assets - liabilities) */
  total_net_worth_paise: number;
  /** Total assets in paise */
  total_assets_paise: number;
  /** Total liabilities in paise */
  total_liabilities_paise: number;
  /** Asset and liability composition breakdown */
  composition: NetWorthCompositionViewModel;
  /** Net worth trend information */
  trend?: NetWorthTrendViewModel;
  /** List of insights about net worth */
  insights: NetWorthInsightViewModel[];
  /** Evidence chain for explainability */
  evidence_chain?: NetWorthEvidenceChainViewModel;
  /** Filters for the view */
  filters: NetWorthFiltersViewModel;
  /** Navigation information */
  navigation: NetWorthNavigationViewModel;
}

// ===== Type Exports =====
export type NetWorthViewModelId = string;