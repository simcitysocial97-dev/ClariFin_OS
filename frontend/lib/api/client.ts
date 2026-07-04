/**
 * FastAPI Client
 * Typed functions for every FastAPI endpoint
 */

import type { Transaction } from '@/types/transaction';
import type {
  CategoriesResponse,
  AnalyticsData,
  Pagination,
} from '@/types/api';

// Import new types
import type {
  Loan,
  LoanCreate,
  LoanUpdate,
  LoanPayment,
  LoanPaymentCreate,
  AmortizationSchedule,
  LoanSummary,
  PrepaymentSimulationRequest,
  PrepaymentResult,
  LoansResponse,
  LoanPaymentsResponse,
} from '@/types/loan';

import type {
  Investment,
  InvestmentCreate,
  InvestmentUpdate,
  InvestmentSummary,
  AssetAllocationResponse,
  InvestmentsResponse,
} from '@/types/investment';

import type {
  IncomeSource,
  IncomeSourceCreate,
  IncomeSourceUpdate,
  IncomeSourcesResponse,
} from '@/types/income';

import type {
  RecurringTransaction,
  RecurringTransactionCreate,
  RecurringTransactionUpdate,
  RecurringDetectionResponse,
  RecurringTransactionsResponse,
} from '@/types/recurring';

import type {
  MonthlyCashflowResponse,
  CashflowBreakdown,
  CashflowSummary,
  NetWorth,
  NetWorthTrendResponse,
  NetWorthProjectionResponse,
  GoalProjection,
  GoalProjectionRequest,
  WhatIfResult,
  WhatIfScenarioRequest,
  LoanPayoffProjection,
  MonthlySnapshot,
  SnapshotsResponse,
  SnapshotBackfillResponse,
} from '@/types/financial';

// Re-export Transaction for convenience
export type { Transaction } from '@/types/transaction';
export type { Pagination } from '@/types/api';

// Re-export new types for convenience
export type {
  Loan,
  LoanCreate,
  LoanUpdate,
  LoanPayment,
  LoanPaymentCreate,
  AmortizationSchedule,
  LoanSummary,
  PrepaymentSimulationRequest,
  PrepaymentResult,
  Investment,
  InvestmentCreate,
  InvestmentUpdate,
  InvestmentSummary,
  IncomeSource,
  IncomeSourceCreate,
  IncomeSourceUpdate,
  RecurringTransaction,
  RecurringTransactionCreate,
  RecurringTransactionUpdate,
  CashflowBreakdown,
  CashflowSummary,
  NetWorth,
  MonthlySnapshot,
  NetWorthProjectionResponse,
  GoalProjection,
  GoalProjectionRequest,
  WhatIfResult,
  WhatIfScenarioRequest,
  LoanPayoffProjection,
} from '@/types/api';

// Re-export V2 types
export type {
  Job,
  JobStatus,
  JobCreateRequest,
  JobCreateResponse,
  ImportStatus,
  ImportValidation,
  ImportCommittedInfo,
  ImportItem,
  ImportPdfResponse,
  ImportListResponse,
  ImportStatusResponse,
  CommitResponse,
  DiscardResponse,
  RevalidateResponse,
} from '@/types/v2';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// ERROR HANDLING
// ============================================================================

/**
 * Structured API error response from backend
 */
interface ApiErrorResponse {
  error: string;
  error_code: string;
  detail: string | null;
  path: string;
  timestamp: string;
}

/**
 * Typed API Error class
 * Thrown when API returns non-OK status with structured error body
 */
export class ApiError extends Error {
  status: number;
  errorCode: string;
  detail: string | null;
  path: string;
  timestamp: string;

  constructor(response: ApiErrorResponse & { status: number }) {
    super(response.error);
    this.name = 'ApiError';
    this.status = response.status;
    this.errorCode = response.error_code;
    this.detail = response.detail;
    this.path = response.path;
    this.timestamp = response.timestamp;
  }
}

/**
 * Handle API response and throw typed ApiError on failure
 */
async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorBody: ApiErrorResponse;
    try {
      errorBody = await res.json();
    } catch {
      // Fallback if response body is not valid JSON
      errorBody = {
        error: res.statusText || 'Unknown error',
        error_code: 'UNKNOWN',
        detail: null,
        path: res.url,
        timestamp: new Date().toISOString(),
      };
    }
    throw new ApiError({ ...errorBody, status: res.status });
  }
  return res.json();
}

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
  imported_at: string;
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
 * Fetch overview data
 */
export async function fetchOverview(): Promise<OverviewData> {
  const res = await fetch(`${API_BASE}/api/overview`);
  return handleResponse<OverviewData>(res);
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
  min_amount?: number;
  max_amount?: number;
  recurring?: boolean;
  page?: number;
  per_page?: number;
}): Promise<{ transactions: Transaction[]; pagination: Pagination }> {
  const query = new URLSearchParams();
  if (params?.search) query.set('search', params.search);
  if (params?.bank && params.bank !== 'All') query.set('bank', params.bank);
  if (params?.category && params.category !== 'All') query.set('category', params.category);
  if (params?.type && params.type !== 'All') query.set('type', params.type);
  if (params?.member && params.member !== 'All') query.set('member', params.member);
  if (params?.min_amount !== undefined) query.set('min_amount', String(params.min_amount));
  if (params?.max_amount !== undefined) query.set('max_amount', String(params.max_amount));
  if (params?.recurring) query.set('recurring', 'true');
  if (params?.page !== undefined) query.set('page', String(params.page));
  if (params?.per_page !== undefined) query.set('per_page', String(params.per_page));
  
  const res = await fetch(`${API_BASE}/api/transactions?${query}`);
  return handleResponse<{ transactions: Transaction[]; pagination: Pagination }>(res);
}

/**
 * Fetch all statements
 */
export async function fetchStatements(): Promise<{ statements: Statement[]; pagination: Pagination }> {
  const res = await fetch(`${API_BASE}/api/statements`);
  return handleResponse<{ statements: Statement[]; pagination: Pagination }>(res);
}

/**
 * Fetch category data with optional drill-down
 */
export async function fetchCategories(params?: {
  drill_category?: string;
}): Promise<CategoriesResponse> {
  const query = new URLSearchParams();
  if (params?.drill_category) query.set('drill_category', params.drill_category);
  
  const res = await fetch(`${API_BASE}/api/categories?${query}`);
  return handleResponse<CategoriesResponse>(res);
}

/**
 * Fetch analytics data
 */
export async function fetchAnalytics(): Promise<AnalyticsData> {
  const res = await fetch(`${API_BASE}/api/analytics`);
  return handleResponse<AnalyticsData>(res);
}

/**
 * Fetch list of banks
 */
export async function fetchBanks(): Promise<{ banks: string[] }> {
  const res = await fetch(`${API_BASE}/api/banks`);
  return handleResponse<{ banks: string[] }>(res);
}

/**
 * Fetch list of categories
 */
export async function fetchCategoryList(): Promise<{ categories: string[] }> {
  const res = await fetch(`${API_BASE}/api/categories/list`);
  return handleResponse<{ categories: string[] }>(res);
}

/**
 * Fetch list of members
 */
export async function fetchMembers(): Promise<{ members: Member[] }> {
  const res = await fetch(`${API_BASE}/api/members`);
  return handleResponse<{ members: Member[] }>(res);
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
  return handleResponse<UploadResult>(res);
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
  return handleResponse<void>(res);
}

/**
 * Delete a statement
 */
export async function deleteStatement(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/statements/${id}`, {
    method: 'DELETE',
  });
  return handleResponse<void>(res);
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
  if (!res.ok) {
    // For blob responses, we need to handle errors differently
    let errorBody: ApiErrorResponse;
    try {
      errorBody = await res.json();
    } catch {
      errorBody = {
        error: res.statusText || 'Export error',
        error_code: 'UNKNOWN',
        detail: null,
        path: res.url,
        timestamp: new Date().toISOString(),
      };
    }
    throw new ApiError({ ...errorBody, status: res.status });
  }
  return res.blob();
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
  return handleResponse<ImportDetectResult>(res);
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
  return handleResponse<ImportExecuteResult>(res);
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
  return handleResponse<Member>(res);
}

// ============================================================================
// ACCOUNT TYPES
// ============================================================================

export interface Account {
  id: number;
  name: string;
  bank_name: string;
  account_type: 'savings' | 'current' | 'credit_card' | 'fd' | 'wallet' | 'loan';
  account_number_masked: string;
  balance_paise: number;
  balance_display: string;
  credit_limit_paise: number;
  credit_limit_display: string | null;
  currency: string;
  color: string;
  icon: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Card {
  id: number;
  account_id: number | null;
  card_name: string;
  card_type: 'visa' | 'mastercard' | 'rupay' | 'amex' | 'diners';
  issuer: string;
  last_four: string;
  cardholder_name: string;
  credit_limit_paise: number;
  credit_limit_display: string;
  outstanding_paise: number;
  minimum_due_paise: number;
  billing_date: number;
  payment_due_date: number;
  apr: number;
  reward_type: string;
  linked_account_id: number | null;
  card_color: string;
  card_gradient: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// ACCOUNT API FUNCTIONS
// ============================================================================

/**
 * Fetch all accounts
 */
export async function fetchAccounts(): Promise<{ accounts: Account[]; total: number }> {
  const res = await fetch(`${API_BASE}/api/accounts`);
  return handleResponse<{ accounts: Account[]; total: number }>(res);
}

/**
 * Fetch a single account
 */
export async function fetchAccount(id: number): Promise<Account> {
  const res = await fetch(`${API_BASE}/api/accounts/${id}`);
  return handleResponse<Account>(res);
}

/**
 * Create a new account
 */
export interface AccountCreateInput {
  name: string;
  bank_name: string;
  account_type: 'savings' | 'current' | 'credit_card' | 'fd' | 'wallet' | 'loan';
  account_number_masked: string;
  balance: number;  // in rupees
  credit_limit: number;  // in rupees
  currency: string;
  color: string;
  icon: string;
}

export async function createAccount(account: AccountCreateInput): Promise<Account> {
  const res = await fetch(`${API_BASE}/api/accounts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(account),
  });
  return handleResponse<Account>(res);
}

/**
 * Update an account
 */
export interface AccountUpdateInput {
  name?: string;
  bank_name?: string;
  account_type?: 'savings' | 'current' | 'credit_card' | 'fd' | 'wallet' | 'loan';
  account_number_masked?: string;
  balance?: number;  // in rupees
  credit_limit?: number;  // in rupees
  currency?: string;
  color?: string;
  icon?: string;
}

export async function updateAccount(id: number, account: AccountUpdateInput): Promise<Account> {
  const res = await fetch(`${API_BASE}/api/accounts/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(account),
  });
  return handleResponse<Account>(res);
}

/**
 * Delete an account
 */
export async function deleteAccount(id: number): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/api/accounts/${id}`, {
    method: 'DELETE',
  });
  return handleResponse<{ success: boolean; message: string }>(res);
}

// ============================================================================
// CARD API FUNCTIONS
// ============================================================================

/**
 * Fetch all cards
 */
export async function fetchCards(accountId?: number): Promise<{ cards: Card[]; total: number }> {
  const query = new URLSearchParams();
  if (accountId) query.set('account_id', String(accountId));
  
  const res = await fetch(`${API_BASE}/api/cards?${query}`);
  return handleResponse<{ cards: Card[]; total: number }>(res);
}

/**
 * Fetch a single card
 */
export async function fetchCard(id: number): Promise<Card> {
  const res = await fetch(`${API_BASE}/api/cards/${id}`);
  return handleResponse<Card>(res);
}

/**
 * Create a new card
 */
export async function createCard(card: Omit<Card, 'id' | 'created_at' | 'updated_at' | 'credit_limit_display' | 'is_active'>): Promise<Card> {
  const res = await fetch(`${API_BASE}/api/cards`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(card),
  });
  return handleResponse<Card>(res);
}

/**
 * Update a card
 */
export async function updateCard(id: number, card: Partial<Omit<Card, 'id' | 'created_at' | 'updated_at' | 'credit_limit_display' | 'is_active'>>): Promise<Card> {
  const res = await fetch(`${API_BASE}/api/cards/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(card),
  });
  return handleResponse<Card>(res);
}

/**
 * Delete a card
 */
export async function deleteCard(id: number): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/api/cards/${id}`, {
    method: 'DELETE',
  });
  return handleResponse<{ success: boolean; message: string }>(res);
}

// ============================================================================
// LOAN API FUNCTIONS
// ============================================================================

/**
 * Fetch all loans
 */
export async function fetchLoans(status?: string): Promise<LoansResponse> {
  const query = new URLSearchParams();
  if (status) query.set('status', status);
  
  const res = await fetch(`${API_BASE}/api/loans?${query}`);
  return handleResponse<LoansResponse>(res);
}

/**
 * Fetch a single loan
 */
export async function fetchLoan(loanId: number): Promise<Loan> {
  const res = await fetch(`${API_BASE}/api/loans/${loanId}`);
  return handleResponse<Loan>(res);
}

/**
 * Create a new loan
 */
export async function createLoan(data: LoanCreate): Promise<Loan> {
  const res = await fetch(`${API_BASE}/api/loans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<Loan>(res);
}

/**
 * Update an existing loan
 */
export async function updateLoan(loanId: number, data: LoanUpdate): Promise<Loan> {
  const res = await fetch(`${API_BASE}/api/loans/${loanId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<Loan>(res);
}

/**
 * Delete a loan
 */
export async function deleteLoan(loanId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/loans/${loanId}`, {
    method: 'DELETE',
  });
  return handleResponse<void>(res);
}

/**
 * Fetch loan payments
 */
export async function fetchLoanPayments(loanId: number): Promise<LoanPaymentsResponse> {
  const res = await fetch(`${API_BASE}/api/loans/${loanId}/payments`);
  return handleResponse<LoanPaymentsResponse>(res);
}

/**
 * Create a loan payment
 */
export async function createLoanPayment(loanId: number, data: LoanPaymentCreate): Promise<LoanPayment> {
  const res = await fetch(`${API_BASE}/api/loans/${loanId}/payments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<LoanPayment>(res);
}

/**
 * Fetch amortization schedule
 */
export async function fetchAmortizationSchedule(loanId: number): Promise<AmortizationSchedule> {
  const res = await fetch(`${API_BASE}/api/loans/${loanId}/amortization`);
  return handleResponse<AmortizationSchedule>(res);
}

/**
 * Fetch loan summary
 */
export async function fetchLoanSummary(loanId: number): Promise<LoanSummary> {
  const res = await fetch(`${API_BASE}/api/loans/${loanId}/summary`);
  return handleResponse<LoanSummary>(res);
}

/**
 * Simulate prepayment
 */
export async function simulatePrepayment(
  loanId: number,
  data: PrepaymentSimulationRequest
): Promise<PrepaymentResult> {
  const res = await fetch(`${API_BASE}/api/loans/${loanId}/simulate-prepayment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<PrepaymentResult>(res);
}

// ============================================================================
// INVESTMENT API FUNCTIONS
// ============================================================================

/**
 * Fetch all investments
 */
export async function fetchInvestments(activeOnly?: boolean): Promise<InvestmentsResponse> {
  const query = new URLSearchParams();
  if (activeOnly !== undefined) query.set('active_only', String(activeOnly));
  
  const res = await fetch(`${API_BASE}/api/investments?${query}`);
  return handleResponse<InvestmentsResponse>(res);
}

/**
 * Fetch a single investment
 */
export async function fetchInvestment(id: number): Promise<Investment> {
  const res = await fetch(`${API_BASE}/api/investments/${id}`);
  return handleResponse<Investment>(res);
}

/**
 * Create a new investment
 */
export async function createInvestment(data: InvestmentCreate): Promise<Investment> {
  const res = await fetch(`${API_BASE}/api/investments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<Investment>(res);
}

/**
 * Update an investment
 */
export async function updateInvestment(id: number, data: InvestmentUpdate): Promise<Investment> {
  const res = await fetch(`${API_BASE}/api/investments/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<Investment>(res);
}

/**
 * Delete an investment
 */
export async function deleteInvestment(id: number): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/api/investments/${id}`, {
    method: 'DELETE',
  });
  return handleResponse<{ success: boolean; message: string }>(res);
}

/**
 * Fetch investment summary
 */
export async function fetchInvestmentSummary(): Promise<InvestmentSummary> {
  const res = await fetch(`${API_BASE}/api/investments/summary`);
  return handleResponse<InvestmentSummary>(res);
}

// ============================================================================
// INCOME SOURCE API FUNCTIONS
// ============================================================================

/**
 * Fetch all income sources
 */
export async function fetchIncomeSources(activeOnly?: boolean): Promise<IncomeSourcesResponse> {
  const query = new URLSearchParams();
  if (activeOnly !== undefined) query.set('active_only', String(activeOnly));
  
  const res = await fetch(`${API_BASE}/api/income-sources?${query}`);
  return handleResponse<IncomeSourcesResponse>(res);
}

/**
 * Create a new income source
 */
export async function createIncomeSource(data: IncomeSourceCreate): Promise<IncomeSource> {
  const res = await fetch(`${API_BASE}/api/income-sources`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<IncomeSource>(res);
}

/**
 * Update an income source
 */
export async function updateIncomeSource(id: number, data: IncomeSourceUpdate): Promise<IncomeSource> {
  const res = await fetch(`${API_BASE}/api/income-sources/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<IncomeSource>(res);
}

/**
 * Delete an income source
 */
export async function deleteIncomeSource(id: number): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/api/income-sources/${id}`, {
    method: 'DELETE',
  });
  return handleResponse<{ success: boolean; message: string }>(res);
}

// ============================================================================
// RECURRING TRANSACTION API FUNCTIONS
// ============================================================================

/**
 * Fetch all recurring transactions
 */
export async function fetchRecurringTransactions(activeOnly?: boolean): Promise<RecurringTransactionsResponse> {
  const query = new URLSearchParams();
  if (activeOnly !== undefined) query.set('active_only', String(activeOnly));
  
  const res = await fetch(`${API_BASE}/api/recurring?${query}`);
  return handleResponse<RecurringTransactionsResponse>(res);
}

/**
 * Create a new recurring transaction
 */
export async function createRecurringTransaction(data: RecurringTransactionCreate): Promise<RecurringTransaction> {
  const res = await fetch(`${API_BASE}/api/recurring`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<RecurringTransaction>(res);
}

/**
 * Update a recurring transaction
 */
export async function updateRecurringTransaction(
  id: number,
  data: RecurringTransactionUpdate
): Promise<RecurringTransaction> {
  const res = await fetch(`${API_BASE}/api/recurring/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<RecurringTransaction>(res);
}

/**
 * Delete a recurring transaction
 */
export async function deleteRecurringTransaction(id: number): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/api/recurring/${id}`, {
    method: 'DELETE',
  });
  return handleResponse<{ success: boolean; message: string }>(res);
}

/**
 * Detect recurring transactions
 */
export async function detectRecurringTransactions(): Promise<RecurringDetectionResponse> {
  const res = await fetch(`${API_BASE}/api/recurring/detect`, {
    method: 'POST',
  });
  return handleResponse<RecurringDetectionResponse>(res);
}

// ============================================================================
// CASHFLOW API FUNCTIONS
// ============================================================================

/**
 * Fetch monthly cashflow
 */
export async function fetchMonthlyCashflow(months?: number): Promise<MonthlyCashflowResponse> {
  const query = new URLSearchParams();
  if (months !== undefined) query.set('months', String(months));
  
  const res = await fetch(`${API_BASE}/api/cashflow/monthly?${query}`);
  return handleResponse<MonthlyCashflowResponse>(res);
}

/**
 * Fetch cashflow breakdown for a month
 */
export async function fetchCashflowBreakdown(month?: string): Promise<CashflowBreakdown> {
  const query = new URLSearchParams();
  if (month) query.set('month', month);
  
  const res = await fetch(`${API_BASE}/api/cashflow/breakdown?${query}`);
  return handleResponse<CashflowBreakdown>(res);
}

/**
 * Fetch cashflow summary
 */
export async function fetchCashflowSummary(): Promise<CashflowSummary> {
  const res = await fetch(`${API_BASE}/api/cashflow/summary`);
  return handleResponse<CashflowSummary>(res);
}

// ============================================================================
// NET WORTH API FUNCTIONS
// ============================================================================

/**
 * Fetch current net worth
 */
export async function fetchNetWorth(): Promise<NetWorth> {
  const res = await fetch(`${API_BASE}/api/networth`);
  return handleResponse<NetWorth>(res);
}

/**
 * Fetch net worth trend
 */
export async function fetchNetWorthTrend(months?: number): Promise<NetWorthTrendResponse> {
  const query = new URLSearchParams();
  if (months !== undefined) query.set('months', String(months));
  
  const res = await fetch(`${API_BASE}/api/networth/trend?${query}`);
  return handleResponse<NetWorthTrendResponse>(res);
}

/**
 * Fetch asset allocation
 */
export async function fetchAssetAllocation(): Promise<AssetAllocationResponse> {
  const res = await fetch(`${API_BASE}/api/networth/allocation`);
  return handleResponse<AssetAllocationResponse>(res);
}

// ============================================================================
// PROJECTION API FUNCTIONS
// ============================================================================

/**
 * Fetch net worth projection
 */
export async function fetchNetWorthProjection(
  months?: number,
  equityReturn?: number,
  debtReturn?: number
): Promise<NetWorthProjectionResponse> {
  const query = new URLSearchParams();
  if (months !== undefined) query.set('months', String(months));
  if (equityReturn !== undefined) query.set('equity_return', String(equityReturn));
  if (debtReturn !== undefined) query.set('debt_return', String(debtReturn));
  
  const res = await fetch(`${API_BASE}/api/projections/networth?${query}`);
  return handleResponse<NetWorthProjectionResponse>(res);
}

/**
 * Fetch loan payoff projection
 */
export async function fetchLoanPayoffProjection(loanId: number): Promise<LoanPayoffProjection> {
  const res = await fetch(`${API_BASE}/api/projections/loan/${loanId}`);
  return handleResponse<LoanPayoffProjection>(res);
}

/**
 * Calculate goal projection
 */
export async function calculateGoal(data: GoalProjectionRequest): Promise<GoalProjection> {
  const res = await fetch(`${API_BASE}/api/projections/goal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<GoalProjection>(res);
}

/**
 * Calculate what-if scenario
 */
export async function calculateWhatIf(data: WhatIfScenarioRequest): Promise<WhatIfResult> {
  const res = await fetch(`${API_BASE}/api/projections/what-if`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<WhatIfResult>(res);
}

// ============================================================================
// SNAPSHOT API FUNCTIONS
// ============================================================================

/**
 * Fetch all monthly snapshots
 */
export async function fetchSnapshots(limit?: number): Promise<SnapshotsResponse> {
  const query = new URLSearchParams();
  if (limit !== undefined) query.set('limit', String(limit));
  
  const res = await fetch(`${API_BASE}/api/snapshots?${query}`);
  return handleResponse<SnapshotsResponse>(res);
}

/**
 * Fetch a single monthly snapshot
 */
export async function fetchSnapshot(month: string): Promise<MonthlySnapshot> {
  const res = await fetch(`${API_BASE}/api/snapshots/${month}`);
  return handleResponse<MonthlySnapshot>(res);
}

/**
 * Generate a monthly snapshot
 */
export async function generateSnapshot(month?: string): Promise<MonthlySnapshot> {
  const query = new URLSearchParams();
  if (month) query.set('month', month);
  
  const res = await fetch(`${API_BASE}/api/snapshots/generate?${query}`, {
    method: 'POST',
  });
  return handleResponse<MonthlySnapshot>(res);
}

/**
 * Backfill snapshots for all months
 */
export async function backfillSnapshots(): Promise<SnapshotBackfillResponse> {
  const res = await fetch(`${API_BASE}/api/snapshots/backfill`, {
    method: 'POST',
  });
  return handleResponse<SnapshotBackfillResponse>(res);
}

// ============================================================================
// EXPORT/IMPORT API FUNCTIONS
// ============================================================================

/**
 * Export database as JSON
 */
export async function exportJSON(): Promise<unknown> {
  const res = await fetch(`${API_BASE}/api/export/json`);
  if (!res.ok) {
    let errorBody: ApiErrorResponse;
    try {
      errorBody = await res.json();
    } catch {
      errorBody = {
        error: res.statusText || 'Export error',
        error_code: 'UNKNOWN',
        detail: null,
        path: res.url,
        timestamp: new Date().toISOString(),
      };
    }
    throw new ApiError({ ...errorBody, status: res.status });
  }
  return res.json();
}

/**
 * Import backup data
 */
export async function importBackup(data: unknown, confirm?: boolean): Promise<{ 
  success: boolean; 
  message: string; 
  imported_counts: Record<string, number>;
  errors: string[] | null;
  total_imported: number;
}> {
  const query = new URLSearchParams();
  if (confirm) query.set('confirm', 'true');
  
  const res = await fetch(`${API_BASE}/api/import/backup?${query}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

// ============================================================================
// BEHAVIOR API FUNCTIONS
// ============================================================================

export interface BehaviorScore {
  score: number;
  grade: string;
  factors: string[];
}

/**
 * Fetch behavior score
 */
export async function fetchBehaviorScore(): Promise<BehaviorScore> {
  const res = await fetch(`${API_BASE}/api/behavior/score`);
  return handleResponse<BehaviorScore>(res);
}

// ============================================================================
// HEALTH/DIAGNOSTICS API FUNCTIONS
// ============================================================================

export interface HealthCheck {
  check: string;
  status: 'pass' | 'fail' | 'warn';
  detail: string;
}

export interface HealthDetailedResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: HealthCheck[];
  timestamp: string;
}

export interface DiagnosticIssue {
  severity: 'error' | 'warning' | 'info';
  category: string;
  message: string;
  file: string | null;
  line: number | null;
  fix_hint: string | null;
}

export interface DiagnosticsResponse {
  status: 'pass' | 'fail';
  error_count: number;
  warning_count: number;
  info_count: number;
  issues: DiagnosticIssue[];
}

/**
 * Fetch detailed health check
 */
export async function fetchHealthDetailed(): Promise<HealthDetailedResponse> {
  const res = await fetch(`${API_BASE}/api/health/detailed`);
  return handleResponse<HealthDetailedResponse>(res);
}

/**
 * Fetch diagnostics
 */
export async function fetchDiagnostics(): Promise<DiagnosticsResponse> {
  const res = await fetch(`${API_BASE}/api/diagnostics`);
  return handleResponse<DiagnosticsResponse>(res);
}

// ============================================================================
// V2 API FUNCTIONS - Jobs, Imports
// ============================================================================

import type {
  Job,
  JobCreateRequest,
  JobCreateResponse,
  ImportPdfResponse,
  ImportListResponse,
  ImportStatusResponse,
  CommitResponse,
  DiscardResponse,
  RevalidateResponse,
} from '@/types/v2';

// Import reconciliation types
import type {
  ReconciliationScanResponse,
  ReconciliationsResponse,
  PendingReconciliationsResponse,
  CreateReconciliationRequest,
  CreateReconciliationResponse,
  BatchReconciliationRequest,
  BatchReconciliationResponse,
  ReconciliationActionResponse,
} from '@/types/reconciliation';

// Re-export reconciliation types
export type {
  ReconciliationScanResponse,
  ReconciliationsResponse,
} from '@/types/reconciliation';

// ============================================================================
// JOBS API FUNCTIONS
// ============================================================================

/**
 * Create a new background job
 */
export async function createJob(data: JobCreateRequest): Promise<JobCreateResponse> {
  const res = await fetch(`${API_BASE}/api/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<JobCreateResponse>(res);
}

/**
 * Fetch job status by ID
 */
export async function fetchJob(jobId: string): Promise<Job> {
  const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
  return handleResponse<Job>(res);
}

// ============================================================================
// V2 IMPORTS API FUNCTIONS
// ============================================================================

/**
 * Upload PDF for V2 staged import (multipart upload)
 */
export async function uploadV2PdfImport(
  file: File,
  member: string = 'Self',
  autoCommit: boolean = true
): Promise<ImportPdfResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('member', member);
  formData.append('auto_commit', String(autoCommit));

  const res = await fetch(`${API_BASE}/api/imports/pdf`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<ImportPdfResponse>(res);
}

/**
 * List staged imports with pagination
 */
export async function fetchV2Imports(params?: {
  status?: string;
  page?: number;
  per_page?: number;
}): Promise<ImportListResponse> {
  const query = new URLSearchParams();
  if (params?.status) query.set('status', params.status);
  if (params?.page !== undefined) query.set('page', String(params.page));
  if (params?.per_page !== undefined) query.set('per_page', String(params.per_page));

  const res = await fetch(`${API_BASE}/api/imports?${query}`);
  return handleResponse<ImportListResponse>(res);
}

/**
 * Get import status by statement_id
 */
export async function fetchV2Import(statementId: string): Promise<ImportStatusResponse> {
  const res = await fetch(`${API_BASE}/api/imports/${statementId}`);
  return handleResponse<ImportStatusResponse>(res);
}

/**
 * Manually commit a staged import
 */
export async function commitV2Import(
  statementId: string,
  member: string = 'Self'
): Promise<CommitResponse> {
  const formData = new FormData();
  formData.append('member', member);

  const res = await fetch(`${API_BASE}/api/imports/${statementId}/commit`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<CommitResponse>(res);
}

/**
 * Discard a staged import
 */
export async function discardV2Import(statementId: string): Promise<DiscardResponse> {
  const res = await fetch(`${API_BASE}/api/imports/${statementId}/discard`, {
    method: 'POST',
  });
  return handleResponse<DiscardResponse>(res);
}

/**
 * Revalidate a statement (rebuild from quarantine corrections)
 */
export async function revalidateV2Import(
  statementId: string,
  member: string = 'Self'
): Promise<RevalidateResponse> {
  const formData = new FormData();
  formData.append('member', member);

  const res = await fetch(`${API_BASE}/api/imports/${statementId}/revalidate`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<RevalidateResponse>(res);
}

/**
 * Set opening/closing balances for a NEEDS_REVIEW import.
 * This updates balances and auto-revalidates (potentially auto-commits if valid).
 */
export async function setImportBalances(
  statementId: string,
  openingBalancePaise: number,
  closingBalancePaise: number,
  member: string = 'Self'
): Promise<RevalidateResponse> {
  const formData = new FormData();
  formData.append('opening_balance_paise', String(openingBalancePaise));
  formData.append('closing_balance_paise', String(closingBalancePaise));
  formData.append('member', member);

  const res = await fetch(`${API_BASE}/api/imports/${statementId}/set-balances`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<RevalidateResponse>(res);
}

/**
 * Re-extract statement using user-drawn bbox coordinates.
 * This endpoint runs bbox extraction and optionally saves the bbox as a template.
 */
export async function reextractWithBbox(
  statementId: string,
  bboxesNorm: Array<{ page_number: number; x0: number; y0: number; x1: number; y1: number }>,
  applyToAllPages: boolean = true,
  saveAsTemplate: boolean = true
): Promise<ImportPdfResponse> {
  const res = await fetch(`${API_BASE}/api/imports/${statementId}/reextract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      bboxes_norm: bboxesNorm,
      apply_to_all_pages: applyToAllPages,
      save_as_template: saveAsTemplate,
    }),
  });
  return handleResponse<ImportPdfResponse>(res);
}

// ============================================================================
// RECONCILIATION API FUNCTIONS
// ============================================================================

/**
 * Scan for potential reconciliation matches
 */
export async function scanReconciliations(): Promise<ReconciliationScanResponse> {
  const res = await fetch(`${API_BASE}/api/reconciliations/scan`);
  return handleResponse<ReconciliationScanResponse>(res);
}

/**
 * Fetch all reconciliations with pagination
 */
export async function fetchReconciliations(params?: {
  status?: string;
  page?: number;
  per_page?: number;
}): Promise<ReconciliationsResponse> {
  const query = new URLSearchParams();
  if (params?.status) query.set('status', params.status);
  if (params?.page !== undefined) query.set('page', String(params.page));
  if (params?.per_page !== undefined) query.set('per_page', String(params.per_page));

  const res = await fetch(`${API_BASE}/api/reconciliations?${query}`);
  return handleResponse<ReconciliationsResponse>(res);
}

/**
 * Fetch pending reconciliations
 */
export async function fetchPendingReconciliations(): Promise<PendingReconciliationsResponse> {
  const res = await fetch(`${API_BASE}/api/reconciliations/pending`);
  return handleResponse<PendingReconciliationsResponse>(res);
}

/**
 * Create a new reconciliation
 */
export async function createReconciliation(
  data: CreateReconciliationRequest
): Promise<CreateReconciliationResponse> {
  const res = await fetch(`${API_BASE}/api/reconciliations/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<CreateReconciliationResponse>(res);
}

/**
 * Confirm a reconciliation
 */
export async function confirmReconciliation(reconciliationId: number): Promise<ReconciliationActionResponse> {
  const res = await fetch(`${API_BASE}/api/reconciliations/${reconciliationId}/confirm`, {
    method: 'POST',
  });
  return handleResponse<ReconciliationActionResponse>(res);
}

/**
 * Reject a reconciliation
 */
export async function rejectReconciliation(reconciliationId: number): Promise<ReconciliationActionResponse> {
  const res = await fetch(`${API_BASE}/api/reconciliations/${reconciliationId}/reject`, {
    method: 'POST',
  });
  return handleResponse<ReconciliationActionResponse>(res);
}

/**
 * Batch insert reconciliations
 */
export async function batchInsertReconciliations(
  data: BatchReconciliationRequest
): Promise<BatchReconciliationResponse> {
  const res = await fetch(`${API_BASE}/api/reconciliations/batch-insert`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<BatchReconciliationResponse>(res);
}

