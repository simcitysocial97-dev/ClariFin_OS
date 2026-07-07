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
  emi_paise?: number | null;
  tenure_months?: number | null;
  start_date: string;
  end_date?: string | null;
  linked_account_id?: number | null;
  status: string;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoansResponse {
  loans: Loan[];
  total: number;
}

// ===== Investment Types =====

export interface Investment {
  id: number;
  name: string;
  type: string;
  platform?: string | null;
  invested_paise: number;
  current_value_paise: number;
  units?: number | null;
  purchase_date?: string | null;
  maturity_date?: string | null;
  linked_account_id?: number | null;
  is_active: boolean;
  notes?: string | null;
  last_updated: string;
  created_at: string;
}

export interface InvestmentsResponse {
  investments: Investment[];
  total: number;
}

// ===== Net Worth Types =====

export interface NetWorth {
  total_assets_paise: number;
  total_liabilities_paise: number;
  net_worth_paise: number;
  accounts_total_paise: number;
  loans_total_paise: number;
  investments_total_paise: number;
}
