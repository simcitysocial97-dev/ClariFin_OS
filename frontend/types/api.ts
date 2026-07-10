/**
 * API Response Types
 * 
 * These types define the structure of API responses from the FastAPI backend.
 */

import type { Transaction } from './transaction';

// ===== Category Types =====

export interface CategorySummary {
  category: string;
  // Canonical paise field
  amount_paise: number;
  // Deprecated rupees field (for backward compatibility)
  amount?: number;
  amount_display: string;
  count: number;
  count_display: string;
  percentage: number;
  percentage_display: string;
}

export interface MonthlyBreakdown {
  month: string;
  amount: number;
}

export interface UncategorizedPattern {
  description: string;
  count: number;
  total: number;
  total_display?: string;
}

export interface CategoriesResponse {
  summary: CategorySummary[];
  monthly_breakdown: MonthlyBreakdown[];
  drill_transactions: Transaction[];
  uncategorized_patterns: UncategorizedPattern[];
}

// ===== Analytics Types =====

export interface DayOfWeekData {
  day: string;
  amount_paise: number;
  count: number;
}

export interface MerchantData {
  merchant: string;
  amount_paise: number;
  count: number;
}

export interface RecurringCharge {
  description: string;
  frequency: number;
  avg_amount_paise: number;
  annual_amount_paise: number;
}

export interface LargestTransaction {
  rank: number;
  date_display: string;
  description: string;
  amount_paise: number;
  bank: string;
}

export interface AnalyticsData {
  highest_month: string;
  highest_month_amount_paise: number;
  avg_monthly_paise: number;
  biggest_transaction: {
    description: string;
    amount_paise: number;
    date: string;
    bank: string;
  } | null;
  unique_merchants: number;
  spending_trend: Array<{ month: string; amount_paise: number; average_paise: number }>;
  day_of_week: DayOfWeekData[];
  top_merchants: MerchantData[];
  recurring_charges: RecurringCharge[];
  largest_transactions: LargestTransaction[];
}

// ===== Chart Data Types =====

export interface ChartDataPoint {
  name: string;
  value: number;
  amount?: number;
  month?: string;
  bank?: string;
}

export interface SpendingTrendPoint {
  month: string;
  amount: number;
  average?: number;
}
// ===== Account Types =====

export interface Account {
  id: number;
  name: string;
  bank: string;
  account_type: string;
  balance_paise: number;
  account_number_last4?: string | null;
  credit_limit_paise?: number;
  currency?: string;
  color?: string;
  icon?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountsResponse {
  accounts: Account[];
  total: number;
}

// ===== Loan Types =====

export interface Loan {
  id: number;
  name: string;
  lender: string;
  loan_type: string;
  principal_paise: number;
  outstanding_paise: number;
  interest_rate: number;
  tenure_months?: number | null;
  emi_paise?: number | null;
  disbursed_date: string;
  next_emi_date?: string | null;
  gold_weight_grams?: number | null;
  gold_purity?: string | null;
  interest_type: string;
  is_active: boolean;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoansResponse {
  loans: Loan[];
  summary: {
    total_loans: number;
    total_outstanding_paise: number;
    total_principal_paise: number;
    total_monthly_emi_paise: number;
  };
}

// ===== Investment Types =====

export interface Investment {
  id: number;
  name: string;
  investment_type: string;
  platform?: string | null;
  invested_paise: number;
  current_value_paise: number;
  units?: number | null;
  buy_price_paise?: number | null;
  current_price_paise?: number | null;
  as_of_date?: string | null;
  is_active: boolean;
  notes?: string | null;
  last_updated?: string;
  created_at: string;
}

export interface InvestmentsResponse {
  investments: Investment[];
  summary: {
    total_investments: number;
    total_invested_paise: number;
    total_current_value_paise: number;
    total_gain_paise: number;
    gain_percent: number;
    allocation_by_type: Record<string, number>;
  };
}

// ===== Amortization Types =====

export interface AmortizationEntry {
  month_number: number;
  payment_date: string;
  emi_paise: number;
  principal_paise: number;
  interest_paise: number;
  balance_paise: number;
}

export interface AmortizationSchedule {
  loan_id: string;
  schedule: AmortizationEntry[];
  total_payments: number;
  total_interest_paise: number;
  total_payment_paise: number;
}

// ===== Prepayment Types =====

export interface PrepaymentRequest {
  prepayment_paise: number;
  mode: 'reduce_tenure' | 'reduce_emi';
}

export interface PrepaymentSimulation {
  prepayment_paise: number;
  mode: string;
  original_emi_paise: number;
  new_emi_paise: number;
  original_remaining_months: number;
  new_remaining_months: number;
  months_saved: number;
  interest_saved_paise: number;
  loan_closed: boolean;
}

// ===== Net Worth Types =====

export interface NetWorth {
  net_worth_paise: number;
  assets: {
    total_paise: number;
    accounts_paise: number;
    investments_paise: number;
    account_count: number;
    investment_count: number;
  };
  liabilities: {
    total_paise: number;
    loans_paise: number;
    cards_paise: number;
    loan_count: number;
    card_count: number;
  };
  is_partial: boolean;
  partial_reason?: string | null;
}
