/**
 * Reconciliation Types
 * ====================
 *
 * TypeScript interfaces for transaction reconciliation and matching.
 */

// ============================================================
// Base Reconciliation Types
// ============================================================

/**
 * Reconciliation record from reconciliations table
 */
export interface Reconciliation {
  id: number;
  debit_txn_id: number;
  credit_txn_id: number;
  debit_account_id: string;
  credit_account_id: string;
  amount: number;
  date_diff_days: number;
  match_confidence: number;
  match_type: 'auto' | 'manual' | 'confirmed';
  status: 'pending' | 'confirmed' | 'rejected';
  created_at: string;
  updated_at: string;
}

/**
 * Potential match from reconciliation engine scan
 */
export interface PotentialMatch {
  debit_txn_id: number;
  credit_txn_id: number;
  debit_account_id: string;
  credit_account_id: string;
  debit_date: string;
  credit_date: string;
  debit_description: string;
  credit_description: string;
  amount: number;
  date_diff_days: number;
  match_confidence: number;
}

// ============================================================
// Request Types
// ============================================================

/**
 * Request to create a reconciliation
 */
export interface CreateReconciliationRequest {
  debit_txn_id: number;
  credit_txn_id: number;
  amount: number;
}

/**
 * Request for batch reconciliation insert
 */
export interface BatchReconciliationRequest {
  matches: {
    debit_txn_id: number;
    credit_txn_id: number;
    debit_account_id?: string;
    credit_account_id?: string;
    amount: number;
    date_diff_days?: number;
    match_confidence?: number;
    match_type?: string;
  }[];
}

// ============================================================
// Response Types
// ============================================================

/**
 * Response from GET /api/reconciliations/scan
 */
export interface ReconciliationScanResponse {
  potential_matches: PotentialMatch[];
  count: number;
}

/**
 * Response from GET /api/reconciliations
 */
export interface ReconciliationsResponse {
  reconciliations: Reconciliation[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    has_next: boolean;
  };
}

/**
 * Response from GET /api/reconciliations/pending
 */
export interface PendingReconciliationsResponse {
  reconciliations: Reconciliation[];
}

/**
 * Response from POST /api/reconciliations/create
 */
export interface CreateReconciliationResponse {
  created: Reconciliation;
}

/**
 * Response from POST /api/reconciliations/batch-insert
 */
export interface BatchReconciliationResponse {
  inserted: number;
}

/**
 * Response from confirm/reject actions
 */
export interface ReconciliationActionResponse {
  success: boolean;
}
