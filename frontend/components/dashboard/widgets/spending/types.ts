import type { WidgetStatus } from '@/types/widget';

// Spending widget specific types
export type SpendContext = 'good' | 'warning' | 'critical' | 'neutral';

export interface SpendingInsight {
  category: string;
  message: string;
  trend: 'up' | 'down' | 'stable';
  change_percent?: number;
}

export interface SpendingViewState {
  status: WidgetStatus;
  insight?: SpendingInsight;
}

// Merchant widget specific types  
export interface MerchantSpending {
  rank: number;
  merchant: string;
  amount_paise: number;
  amount_display: string;
  transaction_count: number;
}