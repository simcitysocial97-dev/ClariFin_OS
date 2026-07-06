/**
 * Transaction Type - Single Source of Truth
 * 
 * This interface unifies local parser output and API responses.
 * All optional fields are populated by the API; core fields are always present.
 * 
 * Phase 2A: Added paise fields for financial determinism.
 * All amounts are stored as INTEGER paise (1 rupee = 100 paise).
 */

export interface Transaction {
  // ===== Core Fields (always present) =====
  id: string | number;
  date: string;
  description: string;
  type: 'debit' | 'credit';
  category: string;
  bank: string;
  cardId?: string;

  // ===== Canonical Monetary Fields (Phase 2) =====
  amount_paise: number;  // Canonical: amount in paise (INTEGER)
  // amount_rupees is DEPRECATED - for backward compatibility only
  amount_rupees?: number;  // Deprecated: use amount_paise instead

  // ===== Extended Fields (from API) =====
  sequence_num?: number;
  subcategory?: string;
  raw_description?: string;
  member?: string;
  statement_file?: string;
  statement_period_from?: string | null;
  statement_period_to?: string | null;

  // ===== Computed Display Fields (from API) =====
  parsed_date?: string;
  date_display?: string;
  month_key?: string;
  weekday?: string;
  amount_display?: string;
  description_display?: string;
  is_large?: boolean;
}


// ===== Phase 2A: Account Balance Interface =====

export interface AccountBalance {
  account_id: string;
  bank: string;
  transaction_count: number;
  total_debit_paise: number;
  total_credit_paise: number;
  balance_paise: number;
  balance_display: string;
}


// ===== Phase 2A: Running Balance Entry =====

export interface RunningBalanceEntry {
  transaction_id: number;
  date: string;
  date_ymd: string;
  description: string;
  debit_paise: number;
  credit_paise: number;
  balance_paise: number;
  bank: string;
}


// ===== Phase 2A: Statement Validation Result =====

export interface StatementValidation {
  statement_id: number;
  status: 'match' | 'mismatch';
  computed_balance_paise: number;
  computed_balance_display: string;
  claimed_balance_paise: number;
  claimed_balance_display: string;
  difference_paise: number;
  difference_display: string;
  transaction_count: number;
}

// ===== Type Guards =====

export function isTransactionWithId(txn: Transaction): txn is Transaction & { id: string } {
  return typeof txn.id === 'string';
}

export function isTransactionFromAPI(txn: Transaction): txn is Transaction & {
  sequence_num: number;
  date_display: string;
  amount_display: string;
} {
  return txn.sequence_num !== undefined;
}

// ===== Metadata Interface =====

export interface Metadata {
  bankName: string;
  cardNumber: string;
  creditLimit: number;
  totalAmountDue: number;
  minimumAmountDue: number;
  dueDate: string;
  billCycleStart: string;
  billCycleEnd: string;
  openingBalance?: number;
}

// ===== Parse Result Interface =====

export interface ParseResult {
  transactions: Transaction[];
  metadata: Metadata;
  validation: {
    isValid: boolean;
    message: string;
    calculatedTotal: number;
    expectedTotal: number;
    bankTotal: number;
    difference: number;
    totalDebits: number;
    totalCredits: number;
    transactionCount: number;
  };
  rawText: string;
}

// ===== Filters Interface =====

export interface Filters {
  search: string;
  category: string;
  type: 'all' | 'debit' | 'credit';
  cardId: string;
  dateRange: {
    from: Date | null;
    to: Date | null;
  };
}