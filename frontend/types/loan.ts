/**
 * Loan Types
 * ==========
 *
 * TypeScript interfaces for loan management and payment tracking.
 * All monetary values are in paise (integer).
 */

// ============================================================
// Base Loan Types
// ============================================================

/**
 * Full loan record as returned by GET /api/loans/{loanId}
 * Includes payment history and computed fields
 */
export interface Loan {
  id: number;
  name: string;
  lender: string | null;
  loan_type: 'home' | 'car' | 'personal' | 'education' | 'credit_card' | 'gold' | 'other';
  principal_paise: number;
  outstanding_paise: number;
  interest_rate: number;
  emi_paise: number;
  tenure_months: number | null;
  start_date: string;
  end_date: string | null;
  linked_account_id: number | null;
  status: 'active' | 'closed' | 'defaulted';
  notes: string | null;
  created_at: string;
  updated_at: string;
  // Computed fields from GET /api/loans/{loanId}
  payments?: LoanPayment[];
  payment_count?: number;
  total_paid_paise?: number;
  total_interest_paid_paise?: number;
  remaining_payments?: number | null;
  // Optional field for next EMI date (computed by backend)
  next_emi_date?: string | null;
}

/**
 * Fields for creating a loan (matches backend Pydantic model)
 */
export interface LoanCreate {
  name: string;
  lender?: string | null;
  loan_type?: 'home' | 'car' | 'personal' | 'education' | 'credit_card' | 'gold' | 'other';
  principal_paise: number;
  outstanding_paise: number;
  interest_rate: number;
  emi_paise?: number;
  tenure_months?: number | null;
  start_date: string;
  end_date?: string | null;
  linked_account_id?: number | null;
  status?: 'active' | 'closed' | 'defaulted';
  notes?: string | null;
}

/**
 * Fields for updating a loan (all optional)
 */
export interface LoanUpdate {
  name?: string;
  lender?: string | null;
  loan_type?: 'home' | 'car' | 'personal' | 'education' | 'credit_card' | 'gold' | 'other';
  outstanding_paise?: number;
  interest_rate?: number;
  emi_paise?: number;
  status?: 'active' | 'closed' | 'defaulted';
  notes?: string | null;
}

// ============================================================
// Loan Payment Types
// ============================================================

/**
 * Single payment record from loan_payments table
 */
export interface LoanPayment {
  id: number;
  loan_id: number;
  transaction_id: number | null;
  principal_component_paise: number;
  interest_component_paise: number;
  payment_date: string;
  remaining_principal_paise: number;
  created_at: string;
}

/**
 * Fields for recording a loan payment
 */
export interface LoanPaymentCreate {
  loan_id?: number;
  transaction_id?: number | null;
  principal_component_paise?: number;
  interest_component_paise?: number;
  payment_date: string;
  remaining_principal_paise?: number;
}

// ============================================================
// Amortization Schedule Types
// ============================================================

/**
 * Single row of amortization schedule
 * Returned by GET /api/loans/{loanId}/amortization
 */
export interface AmortizationEntry {
  period: number;
  emi_date: string;
  emi_paise: number;
  interest_paise: number;
  principal_paise: number;
  remaining_principal_paise: number;
}

/**
 * Amortization schedule response
 */
export interface AmortizationSchedule {
  loan_id: number;
  emi_paise: number;
  total_periods: number;
  total_interest_paise: number;
  schedule: AmortizationEntry[];
}

// ============================================================
// Loan Summary Types
// ============================================================

/**
 * Comprehensive loan summary
 * Returned by GET /api/loans/{loanId}/summary
 */
export interface LoanSummary {
  loan_id: number;
  loan_name: string | null;
  lender: string | null;
  principal_original_paise: number;
  principal_remaining_paise: number;
  total_interest_paid_paise: number;
  future_interest_paise: number;
  total_interest_full_term_paise: number;
  completion_percent: number;
  projected_closure_date: string;
  days_to_close: number;
  is_closed: boolean;
  months_remaining: number;
  total_payments_made: number;
}

// ============================================================
// Prepayment Simulation Types
// ============================================================

/**
 * Request body for prepayment simulation
 */
export interface PrepaymentSimulationRequest {
  extra_payment_paise: number;
  extra_payment_date: string;
  strategy: 'REDUCE_TENURE' | 'REDUCE_EMI';
}

/**
 * Result of prepayment simulation
 * Returned by POST /api/loans/{loanId}/simulate-prepayment
 */
export interface PrepaymentResult {
  loan_id: number;
  loan_name: string | null;
  extra_payment_paise: number;
  extra_payment_date: string;
  strategy: 'REDUCE_TENURE' | 'REDUCE_EMI';
  interest_saved_paise: number;
  months_saved: number;
  new_closure_date: string;
  new_emi_paise: number;
  effective_annual_return_percent: number;
  original_closure_date: string;
  original_future_interest_paise: number;
  new_future_interest_paise: number;
  remaining_principal_after_prepayment_paise: number;
}

// ============================================================
// Response Types
// ============================================================

/**
 * Response from GET /api/loans
 */
export interface LoansResponse {
  loans: Loan[];
  total: number;
}

/**
 * Response from GET /api/loans/{loanId}/payments
 */
export interface LoanPaymentsResponse {
  payments: LoanPayment[];
  total: number;
}