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