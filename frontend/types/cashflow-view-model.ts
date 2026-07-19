/**
 * Cashflow ViewModel - Stage 4 Cashflow Truth Workspace
 *
 * This is the canonical ViewModel for the Cashflow Truth Workspace.
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

// ===== Cashflow Trend Types =====
export type CashflowTrendDirection = 'up' | 'down' | 'flat';

export interface CashflowTrendViewModel {
  /** Trend direction (up/down/flat) */
  direction: CashflowTrendDirection;
  /** Percentage change from previous period */
  percentage_change: number;
  /** Time period for comparison (e.g., '1M', '3M', '1Y') */
  period: string;
  /** Volatility score (0-100) */
  volatility_score: number;
}

// ===== Cashflow Monthly Types =====
export interface CashflowMonthlyViewModel {
  /** Month label (e.g., '2026-07') */
  month: string;
  /** Total income in paise */
  income_paise: number;
  /** Total expenses in paise */
  expenses_paise: number;
  /** Net cashflow in paise (income - expenses) */
  net_paise: number;
  /** Number of transactions in this month */
  transaction_count: number;
}

// ===== Cashflow Category Types =====
export interface CashflowCategoryViewModel {
  /** Category identifier */
  category_id: string;
  /** Category name for display */
  category_name: string;
  /** Total amount in paise */
  amount_paise: number;
  /** Percentage of total (0-100) */
  percentage: number;
  /** Number of transactions in this category */
  transaction_count: number;
}

// ===== Cashflow Transaction Types =====
export interface CashflowTransactionViewModel {
  /** Transaction identifier */
  id: string;
  /** Transaction date (ISO format) */
  date: string;
  /** Transaction description */
  description: string;
  /** Transaction amount in paise */
  amount_paise: number;
  /** Category name */
  category: string;
  /** Merchant name if available */
  merchant?: string;
}

// ===== Cashflow Insight Types =====
export type CashflowInsightType = 'positive' | 'warning' | 'info' | 'alert';
export type CashflowInsightSeverity = 'low' | 'medium' | 'high';

export interface CashflowInsightViewModel {
  /** Insight type */
  type: CashflowInsightType;
  /** Insight severity */
  severity: CashflowInsightSeverity;
  /** Human-readable insight message */
  message: string;
  /** URL for detailed view or action */
  action_url?: string;
}

// ===== Cashflow Evidence Types =====
export interface CashflowEvidenceItemViewModel {
  /** Evidence type (transaction, categorization, adjustment) */
  type: string;
  /** Human-readable summary */
  summary: string;
  /** Source reference */
  source: string;
  /** Confidence score (0-100) */
  confidence?: number;
}

export interface CashflowCalculationStepViewModel {
  /** Step name */
  name: string;
  /** Step description */
  description: string;
  /** Input values for the step */
  inputs: Record<string, unknown>;
  /** Output values from the step */
  outputs: Record<string, unknown>;
}

export interface CashflowEvidenceChainViewModel {
  /** Overall summary of the calculation */
  summary: string;
  /** List of evidence items */
  evidence: CashflowEvidenceItemViewModel[];
  /** Calculation chain steps */
  calculation_steps: CashflowCalculationStepViewModel[];
  /** Source references for traceability */
  source_references: string[];
  /** Overall confidence (0-100) */
  confidence_score: number;
}

// ===== Cashflow Filters Types =====
export interface CashflowFiltersViewModel {
  /** Date range filter */
  date_range?: {
    from: string;
    to: string;
  };
  /** Category multi-select filter */
  categories?: string[];
  /** Merchant filter */
  merchants?: string[];
  /** Amount range filter */
  amount_range?: {
    min: number;
    max: number;
  };
}

// ===== Cashflow Navigation Types =====
export interface CashflowNavigationViewModel {
  /** Deep link to this view */
  deep_link: string;
  /** Cross-references to related workspaces */
  cross_references: {
    accounts?: string;
    transactions?: string;
  };
}

// ===== Main Cashflow ViewModel =====
export interface CashflowViewModel {
  /** Total income in paise */
  total_income_paise: number;
  /** Total expenses in paise */
  total_expenses_paise: number;
  /** Net cashflow in paise (income - expenses) */
  net_cashflow_paise: number;
  /** Total number of transactions */
  transaction_count: number;
  /** Cashflow trend information */
  trend?: CashflowTrendViewModel;
  /** Monthly cashflow summaries */
  monthly: CashflowMonthlyViewModel[];
  /** Category breakdowns */
  categories: CashflowCategoryViewModel[];
  /** Transactions list */
  transactions: CashflowTransactionViewModel[];
  /** List of insights about cashflow */
  insights: CashflowInsightViewModel[];
  /** Evidence chain for explainability */
  evidence_chain?: CashflowEvidenceChainViewModel;
  /** Filters for the view */
  filters: CashflowFiltersViewModel;
  /** Navigation information */
  navigation: CashflowNavigationViewModel;
}

// ===== Type Exports =====
export type CashflowViewModelId = string;