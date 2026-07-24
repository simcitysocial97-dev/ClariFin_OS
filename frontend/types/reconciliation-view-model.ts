/**
 * Reconciliation ViewModel - Stage 4 Reconciliation Intelligence Workspace
 *
 * This is the canonical ViewModel for the Reconciliation Intelligence Workspace.
 * It follows the architecture flow: Backend → API → DTO → Mapper → ViewModel
 *
 * All amounts are in paise (₹1.00 = 100 paise) for financial determinism.
 * This ViewModel is presentation-only and must be mapped from backend DTOs.
 */

// ===== Reconciliation Types =====
export type ReconciliationStatus = 'pending' | 'confirmed' | 'rejected' | 'disputed';

// ===== Discrepancy Types =====
export interface DiscrepancyViewModel {
  /** Discrepancy identifier */
  id: number;
  /** Transaction identifier */
  transaction_id: number;
  /** Statement identifier */
  statement_id: number;
  /** Discrepancy type (amount, date, description) */
  type: string;
  /** Expected amount in paise */
  expected_paise: number;
  /** Actual amount in paise */
  actual_paise: number;
  /** Difference in paise */
  difference_paise: number;
  /** Discrepancy status */
  status: ReconciliationStatus;
  /** Additional notes */
  notes?: string;
}

// ===== Status Overview Types =====
export interface StatusOverviewViewModel {
  /** Total transactions */
  total_transactions: number;
  /** Number of reconciled transactions */
  reconciled: number;
  /** Number of pending reconciliations */
  pending: number;
  /** Number of discrepancies */
  discrepancies: number;
  /** Match rate percentage (0-100) */
  match_rate: number;
}

// ===== Audit Trail Types =====
export interface AuditTrailEntryViewModel {
  /** Audit entry identifier */
  id: number;
  /** Transaction identifier */
  transaction_id: number;
  /** Action taken (reconcile, reject, dispute) */
  action: string;
  /** User who performed the action */
  user: string;
  /** Action timestamp (ISO format) */
  timestamp: string;
  /** Action notes */
  notes?: string;
}

// ===== Reconciliation Summary Types =====
export interface ReconciliationSummaryViewModel {
  /** Statement identifier */
  statement_id: number;
  /** Bank name */
  bank: string;
  /** Statement period start */
  period_from: string;
  /** Statement period end */
  period_to: string;
  /** Total debit in paise */
  total_debit_paise: number;
  /** Total credit in paise */
  total_credit_paise: number;
  /** Number of transactions */
  transaction_count: number;
  /** Number of reconciled transactions */
  reconciled_count: number;
  /** Overall status */
  status: ReconciliationStatus;
}

// ===== Reconciliation Insight Types =====
export type ReconciliationInsightType = 'positive' | 'warning' | 'info' | 'alert';
export type ReconciliationInsightSeverity = 'low' | 'medium' | 'high';

export interface ReconciliationInsightViewModel {
  /** Insight type */
  type: ReconciliationInsightType;
  /** Insight severity */
  severity: ReconciliationInsightSeverity;
  /** Human-readable insight message */
  message: string;
  /** URL for detailed view or action */
  action_url?: string;
}

// ===== Reconciliation Evidence Types =====
export interface ReconciliationEvidenceItemViewModel {
  /** Evidence type (transaction, statement, match) */
  type: string;
  /** Human-readable summary */
  summary: string;
  /** Source reference */
  source: string;
  /** Confidence score (0-100) */
  confidence?: number;
}

export interface ReconciliationCalculationStepViewModel {
  /** Step name */
  name: string;
  /** Step description */
  description: string;
  /** Input values for the step */
  inputs: Record<string, unknown>;
  /** Output values from the step */
  outputs: Record<string, unknown>;
}

export interface ReconciliationEvidenceChainViewModel {
  /** Overall summary of the calculation */
  summary: string;
  /** List of evidence items */
  evidence: ReconciliationEvidenceItemViewModel[];
  /** Calculation chain steps */
  calculation_steps: ReconciliationCalculationStepViewModel[];
  /** Source references for traceability */
  source_references: string[];
  /** Overall confidence (0-100) */
  confidence_score: number;
}

// ===== Reconciliation Filters Types =====
export interface ReconciliationFiltersViewModel {
  /** Status filter */
  status?: ReconciliationStatus[];
  /** Banks filter */
  banks?: string[];
  /** Date range filter */
  date_range?: {
    from: string;
    to: string;
  };
}

// ===== Reconciliation Navigation Types =====
export interface ReconciliationNavigationViewModel {
  /** Deep link to this view */
  deep_link: string;
  /** Cross-references to related workspaces */
  cross_references: {
    accounts?: string;
    transactions?: string;
  };
}

// ===== Main Reconciliation ViewModel =====
export interface ReconciliationViewModel {
  /** List of statement summaries */
  statements: ReconciliationSummaryViewModel[];
  /** List of discrepancies */
  discrepancies: DiscrepancyViewModel[];
  /** Reconciliation status overview */
  status_overview: StatusOverviewViewModel;
  /** Audit trail entries */
  audit_trail: AuditTrailEntryViewModel[];
  /** List of insights about reconciliation */
  insights: ReconciliationInsightViewModel[];
  /** Evidence chain for explainability */
  evidence_chain?: ReconciliationEvidenceChainViewModel;
  /** Filters for the view */
  filters: ReconciliationFiltersViewModel;
  /** Navigation information */
  navigation: ReconciliationNavigationViewModel;
}

// ===== Type Exports =====
export type ReconciliationViewModelId = string;