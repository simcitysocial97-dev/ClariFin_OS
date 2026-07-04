/**
 * Income Source Types
 * ===================
 *
 * TypeScript interfaces for income source management.
 * All monetary values are in paise (integer).
 */

// ============================================================
// Base Income Source Types
// ============================================================

/**
 * Income source record from income_sources table
 */
export interface IncomeSource {
  id: number;
  name: string;
  type: 'salary' | 'freelance' | 'business' | 'rental' | 'dividend' | 'interest' | 'other';
  account_id: number | null;
  amount_paise: number;
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annual' | 'irregular';
  start_date: string | null;
  end_date: string | null;
  is_active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Fields for creating an income source (matches backend Pydantic model)
 */
export interface IncomeSourceCreate {
  name: string;
  type?: 'salary' | 'freelance' | 'business' | 'rental' | 'dividend' | 'interest' | 'other';
  account_id?: number | null;
  amount_paise?: number;
  frequency?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annual' | 'irregular';
  start_date?: string | null;
  end_date?: string | null;
  is_active?: boolean;
  notes?: string | null;
}

/**
 * Fields for updating an income source (all optional)
 */
export interface IncomeSourceUpdate {
  name?: string;
  type?: 'salary' | 'freelance' | 'business' | 'rental' | 'dividend' | 'interest' | 'other';
  account_id?: number | null;
  amount_paise?: number;
  frequency?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annual' | 'irregular';
  start_date?: string | null;
  end_date?: string | null;
  is_active?: boolean;
  notes?: string | null;
}

// ============================================================
// Response Types
// ============================================================

/**
 * Response from GET /api/income-sources
 */
export interface IncomeSourcesResponse {
  sources: IncomeSource[];
  total: number;
}