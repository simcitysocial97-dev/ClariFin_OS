/**
 * Accounts ViewModel - Stage 4 Accounts Intelligence Workspace
 *
 * This is the canonical ViewModel for the Accounts Intelligence Workspace.
 * It follows the architecture flow: Backend → API → DTO → Mapper → ViewModel
 *
 * All amounts are in paise (₹1.00 = 100 paise) for financial determinism.
 * This ViewModel is presentation-only and must be mapped from backend DTOs.
 */

// ===== Account Types =====
export type AccountType = 'savings' | 'current' | 'credit_card' | 'investment' | 'loan' | 'other';
export type AccountStatus = 'active' | 'inactive' | 'closed';

// ===== Account Detail Types =====
export interface AccountDetailViewModel {
  /** Account identifier */
  id: string;
  /** Account name */
  name: string;
  /** Account type */
  type: AccountType;
  /** Bank or institution name */
  institution: string;
  /** Current balance in paise */
  balance_paise: number;
  /** Currency code */
  currency: string;
  /** Account status */
  status: AccountStatus;
  /** Last 4 digits of account number */
  account_number_last4?: string;
  /** Account opening date (ISO) */
  opened_date?: string;
  /** Account closing date (ISO) */
  closed_date?: string;
}

// ===== Balance History Types =====
export interface BalanceHistoryViewModel {
  /** Date of balance (ISO format) */
  date: string;
  /** Balance in paise on this date */
  balance_paise: number;
  /** Account identifier */
  account_id: string;
}

// ===== Account Transaction Types =====
export interface AccountTransactionViewModel {
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

// ===== Account Type Breakdown Types =====
export interface AccountTypeBreakdownViewModel {
  /** Account type */
  type: AccountType;
  /** Number of accounts of this type */
  count: number;
  /** Total balance for this type in paise */
  total_balance_paise: number;
  /** Percentage of total balance (0-100) */
  percentage: number;
}

// ===== Account Insight Types =====
export type AccountInsightType = 'positive' | 'warning' | 'info' | 'alert';
export type AccountInsightSeverity = 'low' | 'medium' | 'high';

export interface AccountInsightViewModel {
  /** Insight type */
  type: AccountInsightType;
  /** Insight severity */
  severity: AccountInsightSeverity;
  /** Human-readable insight message */
  message: string;
  /** URL for detailed view or action */
  action_url?: string;
}

// ===== Account Evidence Types =====
export interface AccountEvidenceItemViewModel {
  /** Evidence type (transaction, balance, adjustment) */
  type: string;
  /** Human-readable summary */
  summary: string;
  /** Source reference */
  source: string;
  /** Confidence score (0-100) */
  confidence?: number;
}

export interface AccountCalculationStepViewModel {
  /** Step name */
  name: string;
  /** Step description */
  description: string;
  /** Input values for the step */
  inputs: Record<string, unknown>;
  /** Output values from the step */
  outputs: Record<string, unknown>;
}

export interface AccountEvidenceChainViewModel {
  /** Overall summary of the calculation */
  summary: string;
  /** List of evidence items */
  evidence: AccountEvidenceItemViewModel[];
  /** Calculation chain steps */
  calculation_steps: AccountCalculationStepViewModel[];
  /** Source references for traceability */
  source_references: string[];
  /** Overall confidence (0-100) */
  confidence_score: number;
}

// ===== Account Filters Types =====
export interface AccountFiltersViewModel {
  /** Account types filter */
  account_types?: AccountType[];
  /** Institutions filter */
  institutions?: string[];
  /** Statuses filter */
  statuses?: AccountStatus[];
  /** Date range filter */
  date_range?: {
    from: string;
    to: string;
  };
  /** Balance range filter */
  balance_range?: {
    min: number;
    max: number;
  };
}

// ===== Account Navigation Types =====
export interface AccountNavigationViewModel {
  /** Deep link to this view */
  deep_link: string;
  /** Cross-references to related workspaces */
  cross_references: {
    net_worth?: string;
    transactions?: string;
  };
}

// ===== Main Accounts ViewModel =====
export interface AccountsViewModel {
  /** List of account details */
  accounts: AccountDetailViewModel[];
  /** Total balance across all accounts in paise */
  total_balance_paise: number;
  /** Total number of accounts */
  account_count: number;
  /** Account type breakdown */
  type_breakdown: AccountTypeBreakdownViewModel[];
  /** Balance history entries */
  balance_history: BalanceHistoryViewModel[];
  /** Transactions list */
  transactions: AccountTransactionViewModel[];
  /** List of insights about accounts */
  insights: AccountInsightViewModel[];
  /** Evidence chain for explainability */
  evidence_chain?: AccountEvidenceChainViewModel;
  /** Filters for the view */
  filters: AccountFiltersViewModel;
  /** Navigation information */
  navigation: AccountNavigationViewModel;
}

// ===== Type Exports =====
export type AccountsViewModelId = string;