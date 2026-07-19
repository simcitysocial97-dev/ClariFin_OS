/**
 * Loans ViewModel - Stage 4 Loans Intelligence Workspace
 *
 * This is the canonical ViewModel for the Loans Intelligence Workspace.
 * It follows the architecture flow: Backend → API → DTO → Mapper → ViewModel
 *
 * All amounts are in paise (₹1.00 = 100 paise) for financial determinism.
 * All interest rates are in basis points (1% = 100 bps).
 * This ViewModel is presentation-only and must be mapped from backend DTOs.
 */

// ===== Loan Types =====
export type LoanType = 'personal' | 'home' | 'car' | 'education' | 'other';
export type LoanStatus = 'active' | 'closed' | 'defaulted';

// ===== Amortization Schedule Types =====
export interface AmortizationEntryViewModel {
  /** Payment number (1-based) */
  payment_number: number;
  /** Payment date (ISO format) */
  date: string;
  /** Principal component in paise */
  principal_paise: number;
  /** Interest component in paise */
  interest_paise: number;
  /** Total EMI in paise */
  emi_paise: number;
  /** Remaining balance in paise */
  balance_paise: number;
}

// ===== Loan Summary Types =====
export interface LoanSummaryViewModel {
  /** Loan identifier */
  id: string;
  /** Loan name */
  name: string;
  /** Loan type */
  type: LoanType;
  /** Lending institution */
  lender: string;
  /** Original loan amount in paise */
  original_amount_paise: number;
  /** Outstanding balance in paise */
  outstanding_paise: number;
  /** Annual interest rate in basis points */
  interest_rate_bps: number;
  /** Original tenure in months */
  tenure_months: number;
  /** Remaining tenure in months */
  remaining_months: number;
  /** Monthly EMI in paise */
  emi_paise: number;
  /** Loan status */
  status: LoanStatus;
  /** Loan start date (ISO format) */
  start_date: string;
  /** Loan end date (ISO format) */
  end_date?: string;
}

// ===== Payment Progress Types =====
export interface PaymentProgressViewModel {
  /** Loan identifier */
  loan_id: string;
  /** Total number of payments made */
  total_payments: number;
  /** Total principal paid in paise */
  total_principal_paise: number;
  /** Total interest paid in paise */
  total_interest_paise: number;
  /** Percentage of principal paid (0-100) */
  principal_percentage: number;
  /** Percentage of interest paid (0-100) */
  interest_percentage: number;
}

// ===== Interest Analysis Types =====
export interface InterestAnalysisViewModel {
  /** Loan identifier */
  loan_id: string;
  /** Total interest to be paid in paise */
  total_interest_paise: number;
  /** Interest paid so far in paise */
  paid_interest_paise: number;
  /** Interest remaining to be paid in paise */
  remaining_interest_paise: number;
  /** Interest to principal ratio */
  interest_ratio: number;
}

// ===== Loan Insight Types =====
export type LoanInsightType = 'positive' | 'warning' | 'info' | 'alert';
export type LoanInsightSeverity = 'low' | 'medium' | 'high';

export interface LoanInsightViewModel {
  /** Insight type */
  type: LoanInsightType;
  /** Insight severity */
  severity: LoanInsightSeverity;
  /** Human-readable insight message */
  message: string;
  /** URL for detailed view or action */
  action_url?: string;
}

// ===== Loan Evidence Types =====
export interface LoanEvidenceItemViewModel {
  /** Evidence type (payment, calculation, adjustment) */
  type: string;
  /** Human-readable summary */
  summary: string;
  /** Source reference */
  source: string;
  /** Confidence score (0-100) */
  confidence?: number;
}

export interface LoanCalculationStepViewModel {
  /** Step name */
  name: string;
  /** Step description */
  description: string;
  /** Input values for the step */
  inputs: Record<string, unknown>;
  /** Output values from the step */
  outputs: Record<string, unknown>;
}

export interface LoanEvidenceChainViewModel {
  /** Overall summary of the calculation */
  summary: string;
  /** List of evidence items */
  evidence: LoanEvidenceItemViewModel[];
  /** Calculation chain steps */
  calculation_steps: LoanCalculationStepViewModel[];
  /** Source references for traceability */
  source_references: string[];
  /** Overall confidence (0-100) */
  confidence_score: number;
}

// ===== Loan Filters Types =====
export interface LoanFiltersViewModel {
  /** Loan types filter */
  loan_types?: LoanType[];
  /** Lenders filter */
  lenders?: string[];
  /** Statuses filter */
  statuses?: LoanStatus[];
}

// ===== Loan Navigation Types =====
export interface LoanNavigationViewModel {
  /** Deep link to this view */
  deep_link: string;
  /** Cross-references to related workspaces */
  cross_references: {
    net_worth?: string;
    accounts?: string;
  };
}

// ===== Main Loans ViewModel =====
export interface LoansViewModel {
  /** List of loan summaries */
  loans: LoanSummaryViewModel[];
  /** Total outstanding across all loans in paise */
  total_outstanding_paise: number;
  /** Total monthly EMI in paise */
  total_emi_paise: number;
  /** Total number of active loans */
  loan_count: number;
  /** Amortization schedule entries */
  amortization: AmortizationEntryViewModel[];
  /** Payment progress for each loan */
  payment_progress: PaymentProgressViewModel[];
  /** Interest analysis for each loan */
  interest_analysis: InterestAnalysisViewModel[];
  /** List of insights about loans */
  insights: LoanInsightViewModel[];
  /** Evidence chain for explainability */
  evidence_chain?: LoanEvidenceChainViewModel;
  /** Filters for the view */
  filters: LoanFiltersViewModel;
  /** Navigation information */
  navigation: LoanNavigationViewModel;
}

// ===== Type Exports =====
export type LoansViewModelId = string;