/**
 * Recurring Transaction Types
 * ===========================
 *
 * TypeScript interfaces for recurring transaction management.
 * All monetary values are in paise (integer).
 */

// ============================================================
// Base Recurring Transaction Types
// ============================================================

/**
 * Recurring transaction record from recurring_transactions table
 */
export interface RecurringTransaction {
  id: number;
  description: string;
  amount_paise: number;
  type: 'debit' | 'credit';
  category: string;
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annual';
  account_id: string | null;
  next_due_date: string | null;
  last_detected_date: string | null;
  occurrence_count: number;
  is_active: boolean;
  auto_detected: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Fields for creating a recurring transaction (matches backend Pydantic model)
 */
export interface RecurringTransactionCreate {
  description: string;
  amount_paise: number;
  type?: 'debit' | 'credit';
  category?: string;
  frequency?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annual';
  account_id?: string | null;
  next_due_date?: string | null;
  is_active?: boolean;
  notes?: string | null;
}

/**
 * Fields for updating a recurring transaction (all optional)
 */
export interface RecurringTransactionUpdate {
  description?: string;
  amount_paise?: number;
  type?: 'debit' | 'credit';
  category?: string;
  frequency?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annual';
  next_due_date?: string | null;
  is_active?: boolean;
  notes?: string | null;
}

// ============================================================
// Detected Recurring Types (from auto-detection engine)
// ============================================================

/**
 * Result from auto-detection engine
 * Returned by POST /api/recurring/detect
 */
export interface DetectedRecurring {
  description: string;
  normalized_description: string;
  amount_paise: number;
  type: 'debit' | 'credit';
  category: string;
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annual';
  occurrence_count: number;
  last_date: string;
  next_expected_date: string;
  confidence: number;
  transaction_ids: number[];
}

/**
 * Response from POST /api/recurring/detect
 */
export interface RecurringDetectionResponse {
  detected: DetectedRecurring[];
  new_saved: number;
}

// ============================================================
// Response Types
// ============================================================

/**
 * Response from GET /api/recurring
 */
export interface RecurringTransactionsResponse {
  recurring: RecurringTransaction[];
  total: number;
}