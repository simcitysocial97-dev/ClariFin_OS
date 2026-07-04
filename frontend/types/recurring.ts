/**
 * Recurring Transaction Types
 */

// Recurring Transaction
export interface RecurringTransaction {
  id: number;
  description: string;
  amount_paise: number;
  frequency: string;
  next_date: string;
  category: string;
  bank: string;
}

// Recurring Transactions Response
export interface RecurringTransactionsResponse {
  transactions: RecurringTransaction[];
  total: number;
}