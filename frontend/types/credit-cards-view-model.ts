/**
 * Credit Cards ViewModel - Stage 4 Credit Cards Intelligence Workspace
 *
 * This is the canonical ViewModel for the Credit Cards Intelligence Workspace.
 * It follows the architecture flow: Backend → API → DTO → Mapper → ViewModel
 *
 * All amounts are in paise (₹1.00 = 100 paise) for financial determinism.
 * This ViewModel is presentation-only and must be mapped from backend DTOs.
 */

// ===== Credit Card Types =====
export type CreditCardStatus = 'active' | 'inactive' | 'closed';

// ===== Statement History Types =====
export interface StatementHistoryViewModel {
  /** Statement identifier */
  id: number;
  /** Credit card identifier */
  card_id: string;
  /** Statement period start (ISO format) */
  period_from: string;
  /** Statement period end (ISO format) */
  period_to: string;
  /** Total amount due in paise */
  total_due_paise: number;
  /** Minimum amount due in paise */
  min_due_paise: number;
  /** Total payment made in paise */
  total_payment_paise: number;
  /** Payment date (ISO format) */
  payment_date?: string;
  /** Payment status (paid, pending, overdue) */
  status: string;
}

// ===== Utilization Types =====
export interface UtilizationViewModel {
  /** Credit card identifier */
  card_id: string;
  /** Credit limit in paise */
  credit_limit_paise: number;
  /** Current balance in paise */
  current_balance_paise: number;
  /** Utilization percentage (0-100) */
  utilization_percentage: number;
  /** Available credit in paise */
  available_paise: number;
}

// ===== Spending by Category Types =====
export interface SpendingByCategoryViewModel {
  /** Credit card identifier */
  card_id: string;
  /** Category name */
  category: string;
  /** Spending amount in paise */
  amount_paise: number;
  /** Percentage of total spending (0-100) */
  percentage: number;
  /** Number of transactions in this category */
  transaction_count: number;
}

// ===== Credit Card Summary Types =====
export interface CreditCardSummaryViewModel {
  /** Credit card identifier */
  id: string;
  /** Card name */
  name: string;
  /** Issuing bank */
  bank: string;
  /** Last 4 digits of card */
  card_number_last4: string;
  /** Credit limit in paise */
  credit_limit_paise: number;
  /** Current balance in paise */
  current_balance_paise: number;
  /** Available credit in paise */
  available_paise: number;
  /** Minimum due in paise */
  min_due_paise: number;
  /** Total due in paise */
  total_due_paise: number;
  /** Payment due date (ISO format) */
  due_date: string;
  /** Card status */
  status: CreditCardStatus;
  /** Reward points balance */
  reward_points: number;
}

// ===== Credit Card Insight Types =====
export type CreditCardInsightType = 'positive' | 'warning' | 'info' | 'alert';
export type CreditCardInsightSeverity = 'low' | 'medium' | 'high';

export interface CreditCardInsightViewModel {
  /** Insight type */
  type: CreditCardInsightType;
  /** Insight severity */
  severity: CreditCardInsightSeverity;
  /** Human-readable insight message */
  message: string;
  /** URL for detailed view or action */
  action_url?: string;
}

// ===== Credit Card Evidence Types =====
export interface CreditCardEvidenceItemViewModel {
  /** Evidence type (statement, transaction, adjustment) */
  type: string;
  /** Human-readable summary */
  summary: string;
  /** Source reference */
  source: string;
  /** Confidence score (0-100) */
  confidence?: number;
}

export interface CreditCardCalculationStepViewModel {
  /** Step name */
  name: string;
  /** Step description */
  description: string;
  /** Input values for the step */
  inputs: Record<string, unknown>;
  /** Output values from the step */
  outputs: Record<string, unknown>;
}

export interface CreditCardEvidenceChainViewModel {
  /** Overall summary of the calculation */
  summary: string;
  /** List of evidence items */
  evidence: CreditCardEvidenceItemViewModel[];
  /** Calculation chain steps */
  calculation_steps: CreditCardCalculationStepViewModel[];
  /** Source references for traceability */
  source_references: string[];
  /** Overall confidence (0-100) */
  confidence_score: number;
}

// ===== Credit Card Filters Types =====
export interface CreditCardFiltersViewModel {
  /** Card statuses filter */
  statuses?: CreditCardStatus[];
  /** Banks filter */
  banks?: string[];
}

// ===== Credit Card Navigation Types =====
export interface CreditCardNavigationViewModel {
  /** Deep link to this view */
  deep_link: string;
  /** Cross-references to related workspaces */
  cross_references: {
    net_worth?: string;
    accounts?: string;
  };
}

// ===== Main Credit Cards ViewModel =====
export interface CreditCardsViewModel {
  /** List of credit card summaries */
  cards: CreditCardSummaryViewModel[];
  /** Total balance across all cards in paise */
  total_balance_paise: number;
  /** Total due across all cards in paise */
  total_due_paise: number;
  /** Total available credit in paise */
  total_available_paise: number;
  /** Total number of active cards */
  card_count: number;
  /** Statement history entries */
  statements: StatementHistoryViewModel[];
  /** Utilization data for each card */
  utilization: UtilizationViewModel[];
  /** Spending breakdown by category */
  spending: SpendingByCategoryViewModel[];
  /** List of insights about credit cards */
  insights: CreditCardInsightViewModel[];
  /** Evidence chain for explainability */
  evidence_chain?: CreditCardEvidenceChainViewModel;
  /** Filters for the view */
  filters: CreditCardFiltersViewModel;
  /** Navigation information */
  navigation: CreditCardNavigationViewModel;
}

// ===== Type Exports =====
export type CreditCardsViewModelId = string;