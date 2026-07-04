/**
 * Investment Types
 * ================
 *
 * TypeScript interfaces for investment management and portfolio tracking.
 * All monetary values are in paise (integer).
 */

// ============================================================
// Base Investment Types
// ============================================================

/**
 * Investment record from investments table
 */
export interface Investment {
  id: number;
  name: string;
  type: 'mutual_fund' | 'stock' | 'fd' | 'ppf' | 'epf' | 'nps' | 'gold' | 'real_estate' | 'crypto' | 'other';
  platform: string | null;
  invested_paise: number;
  current_value_paise: number;
  units: number;
  purchase_date: string | null;
  maturity_date: string | null;
  linked_account_id: number | null;
  is_active: boolean;
  notes: string | null;
  last_updated: string;
  created_at: string;
}

/**
 * Fields for creating an investment (matches backend Pydantic model)
 */
export interface InvestmentCreate {
  name: string;
  type?: 'mutual_fund' | 'stock' | 'fd' | 'ppf' | 'epf' | 'nps' | 'gold' | 'real_estate' | 'crypto' | 'other';
  platform?: string | null;
  invested_paise?: number;
  current_value_paise?: number;
  units?: number;
  purchase_date?: string | null;
  maturity_date?: string | null;
  linked_account_id?: number | null;
  is_active?: boolean;
  notes?: string | null;
}

/**
 * Fields for updating an investment (all optional)
 */
export interface InvestmentUpdate {
  name?: string;
  type?: 'mutual_fund' | 'stock' | 'fd' | 'ppf' | 'epf' | 'nps' | 'gold' | 'real_estate' | 'crypto' | 'other';
  platform?: string | null;
  invested_paise?: number;
  current_value_paise?: number;
  units?: number;
  is_active?: boolean;
  notes?: string | null;
}

// ============================================================
// Investment Summary Types
// ============================================================

/**
 * Aggregate summary of all active investments
 * Returned by GET /api/investments/summary
 */
export interface InvestmentSummary {
  count: number;
  total_invested_paise: number;
  total_current_value_paise: number;
  total_gain_loss_paise: number;
  gain_loss_percent: number;
}

// ============================================================
// Asset Allocation Types
// ============================================================

/**
 * Single allocation bucket with category, value, percentage
 * From networth_engine.compute_asset_allocation
 */
export interface AssetAllocation {
  category: string;
  value_paise: number;
  percentage: number;
}

/**
 * Asset allocation response
 */
export interface AssetAllocationResponse {
  allocation: AssetAllocation[];
  count: number;
}

// ============================================================
// Response Types
// ============================================================

/**
 * Response from GET /api/investments
 */
export interface InvestmentsResponse {
  investments: Investment[];
  total: number;
}