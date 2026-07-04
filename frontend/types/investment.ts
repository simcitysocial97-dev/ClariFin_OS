/**
 * Investment Data Types
 */

// Asset Allocation Response
export interface AssetAllocationResponse {
  total_value_paise: number;
  allocation: Array<{
    category: string;
    value_paise: number;
    percentage: number;
  }>;
}

// Investment Summary
export interface InvestmentSummary {
  total_value_paise: number;
  total_invested_paise: number;
  total_returns_paise: number;
  returns_percentage: number;
  holdings: Array<{
    symbol: string;
    name: string;
    quantity: number;
    avg_price_paise: number;
    current_price_paise: number;
    value_paise: number;
    returns_paise: number;
    returns_percentage: number;
  }>;
}