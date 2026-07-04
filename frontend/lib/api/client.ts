/**
 * FastAPI Client
 * Typed functions for every FastAPI endpoint
 */

import type { Transaction } from '@/types/transaction';
import type {
  CategoriesResponse,
  AnalyticsData,
  CategorySummary,
  MonthlyBreakdown,
  UncategorizedPattern,
} from '@/types/api';
import type {
  NetWorth,
  NetWorthTrendResponse,
  MonthlyCashflowResponse,
  CashflowBreakdown,
  BehaviorScore,
} from '@/types/financial';
import type {
  AssetAllocationResponse,
  InvestmentSummary,
} from '@/types/investment';
import type {
  LoansResponse,
} from '@/types/loan';
import type {
  RecurringTransactionsResponse,
} from '@/types/recurring';
import type { ImportListResponse } from '@/types/v2';

// Re-export Transaction for convenience
export type { Transaction } from '@/types/transaction';
export type { CategorySummary, MonthlyBreakdown, UncategorizedPattern } from '@/types/api';
export type { NetWorth, NetWorthTrendResponse, MonthlyCashflowResponse, CashflowBreakdown, BehaviorScore } from '@/types/financial';
export type { AssetAllocationResponse, InvestmentSummary } from '@/types/investment';
export type { LoansResponse } from '@/types/loan';
export type { RecurringTransactionsResponse } from '@/types/recurring';
export type { ImportListResponse } from '@/types/v2';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// TYPES
// ============================================================================

export interface OverviewData {
  total_spend: number;
  total_spend_display: string;
  this_month: number;
  this_month_display: string;
  last_month: number;
  last_month_display: string;
  month_change: string;
  transaction_count: number;
  card_count: number;
  months_of_data: number;
  monthly_average: number;
  monthly_average_display: string;
  above_below_avg: string;
  above_avg_is_bad: boolean;
  monthly_chart: Array<{ month: string; amount: number }>;
  category_chart: Array<{ name: string; value: number }>;
  bank_chart: Array<{ bank: string; amount: number }>;
  recent_transactions: Transaction[];
  behavioral_insights: Array<{
    title: string;
    description: string;
    severity: 'positive' | 'warning' | 'info' | 'alert';
    icon: string;
  }>;
}

export interface Statement {
  id: number;
  bank: string;
  file_name: string;
  card_last4: string;
  card_display: string;
  period_from: string;
  period_to: string;
  period_display: string;
  transaction_count: number;
  total_debit: number;
  total_credit: number;
  total_debit_display: string;
  total_credit_display: string;
  total_due: number;
  total_due_display: string;
  extracted_net_display: string;
  min_due_display: string;
  due_date: string;
  validation_status: string;
  validation_difference: number;
  badge_text: string;
  badge_color: string;
}

export interface Member {
  id: number;
  name: string;
  color: string;
  created_at: string;
}

export interface UploadResult {
  success: boolean;
  bank: string;
  transaction_count: number;
  validation_status: string;
  metadata: {
    bank_name: string;
    card_number: string;
    credit_limit: number;
    total_amount_due: number;
    minimum_amount_due: number;
    due_date: string;
    bill_cycle_start: string;
    bill_cycle_end: string;
    opening_balance: number;
  };
  log: string[];
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

/**
 * Fetch overview data with optional filters
 */
export async function fetchOverview(params?: {
  exclude_transfers?: boolean;
  member?: string;
}): Promise<OverviewData> {
  const query = new URLSearchParams();
  if (params?.exclude_transfers !== undefined)
    query.set('exclude_transfers', String(params.exclude_transfers));
  if (params?.member) query.set('member', params.member);
  
  const res = await fetch(`${API_BASE}/api/overview?${query}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/**
 * Fetch transactions with filtering and pagination
 */
export async function fetchTransactions(params?: {
  search?: string;
  bank?: string;
  category?: string;
  type?: string;
  member?: string;
  limit?: number;
  offset?: number;
}): Promise<{ transactions: Transaction[]; total: number }> {
  const query = new URLSearchParams();
  if (params?.search) query.set('search', params.search);
  if (params?.bank && params.bank !== 'All') query.set('bank', params.bank);
  if (params?.category && params.category !== 'All') query.set('category', params.category);
  if (params?.type && params.type !== 'All') query.set('type', params.type);
  if (params?.member && params.member !== 'All') query.set('member', params.member);
  if (params?.limit) query.set('limit', String(params.limit));
  if (params?.offset) query.set('offset', String(params.offset));
  
  const res = await fetch(`${API_BASE}/api/transactions?${query}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/**
 * Fetch all statements
 */
export async function fetchStatements(): Promise<Statement[]> {
  const res = await fetch(`${API_BASE}/api/statements`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/**
 * Fetch category data with optional drill-down
 */
export async function fetchCategories(params?: {
  exclude_transfers?: boolean;
  member?: string;
  drill_category?: string;
}): Promise<CategoriesResponse> {
  const query = new URLSearchParams();
  if (params?.exclude_transfers !== undefined)
    query.set('exclude_transfers', String(params.exclude_transfers));
  if (params?.member) query.set('member', params.member);
  if (params?.drill_category) query.set('drill_category', params.drill_category);
  
  const res = await fetch(`${API_BASE}/api/categories?${query}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/**
 * Fetch analytics data
 */
export async function fetchAnalytics(params?: {
  exclude_transfers?: boolean;
  member?: string;
}): Promise<AnalyticsData> {
  const query = new URLSearchParams();
  if (params?.exclude_transfers !== undefined)
    query.set('exclude_transfers', String(params.exclude_transfers));
  if (params?.member) query.set('member', params.member);
  
  const res = await fetch(`${API_BASE}/api/analytics?${query}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/**
 * Fetch list of banks
 */
export async function fetchBanks(): Promise<{ banks: string[] }> {
  const res = await fetch(`${API_BASE}/api/banks`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/**
 * Fetch list of categories
 */
export async function fetchCategoryList(): Promise<{ categories: string[] }> {
  const res = await fetch(`${API_BASE}/api/categories/list`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/**
 * Fetch list of members
 */
export async function fetchMembers(): Promise<{ members: Member[] }> {
  const res = await fetch(`${API_BASE}/api/members`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/**
 * Upload a statement PDF
 */
export async function uploadStatement(
  file: File,
  member: string = 'Self'
): Promise<UploadResult> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('member', member);
  
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload error: ${res.status}`);
  return res.json();
}

/**
 * Update transaction category
 */
export async function updateTransactionCategory(
  id: number,
  category: string,
  subcategory?: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/transactions/${id}/category`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ category, subcategory }),
  });
  if (!res.ok) throw new Error(`Update error: ${res.status}`);
}

/**
 * Delete a statement
 */
export async function deleteStatement(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/statements/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(`Delete error: ${res.status}`);
}

/**
 * Export transactions as CSV
 */
export async function exportCSV(params?: {
  search?: string;
  bank?: string;
  category?: string;
  type?: string;
}): Promise<Blob> {
  const query = new URLSearchParams();
  if (params?.search) query.set('search', params.search);
  if (params?.bank) query.set('bank', params.bank);
  if (params?.category) query.set('category', params.category);
  if (params?.type) query.set('type', params.type);
  
  const res = await fetch(`${API_BASE}/api/export/csv?${query}`);
  if (!res.ok) throw new Error(`Export error: ${res.status}`);
  return res.blob();
}

// ============================================================================
// NET WORTH API FUNCTIONS
// ============================================================================

/**
 * Fetch net worth data
 */
export async function fetchNetWorth(): Promise<NetWorth> {
  const res = await fetch(`${API_BASE}/api/networth`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/**
 * Fetch net worth trend
 */
export async function fetchNetWorthTrend(months?: number): Promise<NetWorthTrendResponse> {
  const query = new URLSearchParams();
  if (months) query.set('months', String(months));
  const res = await fetch(`${API_BASE}/api/networth/trend?${query}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ============================================================================
// CASHFLOW API FUNCTIONS
// ============================================================================

/**
 * Fetch monthly cashflow data
 */
export async function fetchMonthlyCashflow(months?: number): Promise<MonthlyCashflowResponse> {
  const query = new URLSearchParams();
  if (months) query.set('months', String(months));
  const res = await fetch(`${API_BASE}/api/cashflow/monthly?${query}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/**
 * Fetch cashflow breakdown for a specific month
 */
export async function fetchCashflowBreakdown(month?: string): Promise<CashflowBreakdown> {
  const query = new URLSearchParams();
  if (month) query.set('month', month);
  const res = await fetch(`${API_BASE}/api/cashflow/breakdown?${query}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ============================================================================
// INVESTMENT API FUNCTIONS
// ============================================================================

/**
 * Fetch asset allocation
 */
export async function fetchAssetAllocation(): Promise<AssetAllocationResponse> {
  const res = await fetch(`${API_BASE}/api/investments/allocation`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/**
 * Fetch investment summary
 */
export async function fetchInvestmentSummary(): Promise<InvestmentSummary> {
  const res = await fetch(`${API_BASE}/api/investments/summary`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ============================================================================
// LOAN API FUNCTIONS
// ============================================================================

/**
 * Fetch loans
 */
export async function fetchLoans(status?: string): Promise<LoansResponse> {
  const query = new URLSearchParams();
  if (status) query.set('status', status);
  const res = await fetch(`${API_BASE}/api/loans?${query}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ============================================================================
// RECURRING API FUNCTIONS
// ============================================================================

/**
 * Fetch recurring transactions
 */
export async function fetchRecurringTransactions(activeOnly?: boolean): Promise<RecurringTransactionsResponse> {
  const query = new URLSearchParams();
  if (activeOnly !== undefined) query.set('active_only', String(activeOnly));
  const res = await fetch(`${API_BASE}/api/recurring?${query}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ============================================================================
// BEHAVIOR API FUNCTIONS
// ============================================================================

/**
 * Fetch behavior score
 */
export async function fetchBehaviorScore(): Promise<BehaviorScore> {
  const res = await fetch(`${API_BASE}/api/behavior/score`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ============================================================================
// V2 IMPORT API FUNCTIONS
// ============================================================================

/**
 * Fetch V2 imports list
 */
export async function fetchV2Imports(params?: {
  status?: string;
  page?: number;
  per_page?: number;
}): Promise<ImportListResponse> {
  const query = new URLSearchParams();
  if (params?.status) query.set('status', params.status);
  if (params?.page) query.set('page', String(params.page));
  if (params?.per_page) query.set('per_page', String(params.per_page));
  const res = await fetch(`${API_BASE}/api/v2/imports?${query}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ============================================================================
// IMPORT TYPES
// ============================================================================

export interface ImportDetectResult {
  columns: string[];
  sample_rows: Record<string, string>[];
  detected_mapping: {
    date_column?: string;
    description_column?: string;
    amount_column?: string;
    type_column?: string;
    date_format?: string;
  };
  row_count: number;
}

export interface ImportMapping {
  date_column: string;
  description_column: string;
  amount_column: string;
  type_column?: string;
  bank_name: string;
  member: string;
  date_format: string;
}

export interface ImportExecuteResult {
  success: boolean;
  imported: number;
  skipped: number;
  errors: string[];
}

// ============================================================================
// IMPORT API FUNCTIONS
// ============================================================================

/**
 * Detect columns in a CSV/Excel file
 */
export async function detectImportColumns(file: File): Promise<ImportDetectResult> {
  const formData = new FormData();
  formData.append('file', file);
  
  const res = await fetch(`${API_BASE}/api/import/detect`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`Import detect error: ${res.status}`);
  return res.json();
}

/**
 * Execute import with mapping
 */
export async function executeImport(
  filename: string,
  mapping: ImportMapping
): Promise<ImportExecuteResult> {
  const res = await fetch(`${API_BASE}/api/import/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename, mapping }),
  });
  if (!res.ok) throw new Error(`Import execute error: ${res.status}`);
  return res.json();
}

/**
 * Create a new member
 */
export async function createMember(name: string, color: string): Promise<Member> {
  const res = await fetch(`${API_BASE}/api/members`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, color }),
  });
  if (!res.ok) throw new Error(`Create member error: ${res.status}`);
  return res.json();
}
