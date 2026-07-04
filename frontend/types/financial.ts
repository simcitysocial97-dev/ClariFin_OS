/**
 * Financial Data Types
 * Types for net worth, cashflow, and related financial data
 */

// Net Worth Response
export interface NetWorth {
  net_worth_paise: number;
  total_assets_paise: number;
  total_liabilities_paise: number;
  asset_count: number;
  liability_count: number;
}

// Net Worth Trend Response
export interface NetWorthTrendResponse {
  months: Array<{
    month: string;
    net_worth_paise: number;
    assets_paise: number;
    liabilities_paise: number;
  }>;
}

// Monthly Cashflow Response
export interface MonthlyCashflowResponse {
  months: Array<{
    month: string;
    total_income_paise: number;
    total_expense_paise: number;
    net_cashflow_paise: number;
  }>;
}

// Cashflow Breakdown
export interface CashflowBreakdown {
  month: string;
  income_sources: Array<{
    source: string;
    amount_paise: number;
  }>;
  expense_categories: Array<{
    category: string;
    amount_paise: number;
  }>;
}

// Behavior Score
export interface BehaviorScore {
  score: number;
  insights: Array<{
    title: string;
    description: string;
    severity: 'positive' | 'warning' | 'info' | 'alert';
    icon: string;
  }>;
}