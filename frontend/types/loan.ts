/**
 * Loan Data Types
 */

// Loan
export interface Loan {
  id: number;
  bank: string;
  account_number: string;
  loan_type: string;
  principal_paise: number;
  outstanding_paise: number;
  emi_paise: number;
  tenure_months: number;
  interest_rate: number;
  start_date: string;
  end_date: string;
}

// Loans Response
export interface LoansResponse {
  loans: Loan[];
  total: number;
}