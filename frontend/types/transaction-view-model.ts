/**
 * TransactionViewModel - Stage 3 Transaction Intelligence Workspace
 *
 * This is the canonical ViewModel for the Transaction Intelligence Workspace.
 * It follows the architecture flow: Backend → API → DTO → Mapper → ViewModel
 *
 * All amounts are in paise (₹1.00 = 100 paise) for financial determinism.
 * This ViewModel is presentation-only and must be mapped from backend DTOs.
 */

// ===== Money Type (matches backend MoneyDTO) =====
export interface MoneyViewModel {
  paise: number;  // Total paise (e.g., 123456 = ₹1,234.56)
  rupees: number;  // Derived rupees value for display
}

// ===== Evidence Types =====
export interface EvidenceItem {
  /** Type of evidence (categorization, import, adjustment, balance, reconciliation) */
  type: 'categorization' | 'import' | 'adjustment' | 'balance' | 'reconciliation';
  /** Human-readable summary of the evidence */
  summary: string;
  /** Source reference for the evidence */
  source: EvidenceSource;
  /** Confidence score (0-100) if applicable */
  confidence?: number;
}

export interface EvidenceSource {
  /** File ID for import evidence */
  file_id?: string;
  /** Row number in source file */
  row_number?: number;
  /** Extraction ID for PDF parsing */
  extraction_id?: string;
  /** API endpoint that provided this evidence */
  api_endpoint?: string;
}

// ===== Calculation Chain =====
export interface CalculationStep {
  /** Name of the calculation step */
  name: string;
  /** Description of what this step does */
  description: string;
  /** Input values for the step */
  inputs: Record<string, unknown>;
  /** Output values from the step */
  outputs: Record<string, unknown>;
}

// ===== Import Lineage =====
export interface ImportLineage {
  /** Unique import file identifier */
  file_id: string;
  /** Original filename */
  filename: string;
  /** Import date (ISO format) */
  import_date: string;
  /** Source type (pdf, csv, excel) */
  source_type: 'pdf' | 'csv' | 'excel';
  /** Bank name from the import */
  bank: string;
  /** Statement period from date */
  period_from?: string;
  /** Statement period to date */
  period_to?: string;
}

// ===== TransactionViewModel - Core Type =====
export interface TransactionViewModel {
  // ===== Core Fields (always present) =====
  /** Unique transaction identifier */
  id: string;
  /** Transaction date (ISO format YYYY-MM-DD) */
  date: string;
  /** Transaction description */
  description: string;
  /** Transaction amount as Money object (paise is canonical) */
  amount: MoneyViewModel;

  // ===== Extended Fields (populated by mapper) =====
  
  // --- Balance Reference ---
  /** Running balance after transaction (optional) */
  balance?: MoneyViewModel;
  
  // --- Category Navigation ---
  /** Category ID for navigation */
  category_id?: string;
  /** Category name for display */
  category_name?: string;
  /** Full category path (e.g., "Shopping > E-commerce") */
  category_path?: string;
  /** Subcategory name */
  subcategory?: string;
  
  // --- Merchant Navigation ---
  /** Merchant ID for navigation */
  merchant_id?: string;
  /** Merchant name for display */
  merchant_name?: string;
  /** Merchant category for grouping */
  merchant_category?: string;
  
  // --- Date Navigation ---
  /** Year for grouping (e.g., 2026) */
  year?: number;
  /** Month for grouping (1-12) */
  month?: number;
  /** Day for grouping (1-31) */
  day?: number;
  /** Formatted date string for display (e.g., "Jul 5, 2026") */
  date_formatted?: string;
  /** Month key for grouping (e.g., "2026-07") */
  month_key?: string;
  
  // --- Account Reference ---
  /** Account ID this transaction belongs to */
  account_id?: string;
  /** Account name for display */
  account_name?: string;
  /** Bank name */
  bank?: string;
  
  // --- Transaction Type ---
  /** Transaction type (debit/credit) */
  transaction_type?: 'debit' | 'credit';
  /** Bank reference number */
  reference_number?: string;
  
  // --- Selection State ---
  /** Whether this transaction is selected */
  selected?: boolean;
  /** Whether this transaction can be selected */
  selectable?: boolean;
  /** Reason why transaction is not selectable (if applicable) */
  selection_reason?: string;
  
  // --- Adjustment Visibility ---
  /** Whether this transaction has been adjusted */
  is_adjusted?: boolean;
  /** Adjustment ID if adjusted */
  adjustment_id?: string;
  /** Reason for adjustment */
  adjustment_reason?: string;
  
  // --- Import Lineage ---
  /** Import source information */
  import_lineage?: ImportLineage;
  
  // --- Evidence System ---
  /** Evidence items supporting this transaction */
  evidence?: EvidenceItem[];
  
  // --- Calculation Chain ---
  /** Steps in the calculation chain */
  calculation_chain?: CalculationStep[];
  
  // --- Source Reference ---
  /** Source reference for traceability */
  source_reference?: EvidenceSource;
  
  // --- Confidence Score ---
  /** Categorization confidence (0-100) */
  confidence?: number;
  
  // --- Reconciliation Reference ---
  /** Reconciliation ID if linked */
  reconciliation_id?: string;
  /** Reconciliation status */
  reconciliation_status?: 'pending' | 'confirmed' | 'rejected';
}

// ===== Type Exports =====
export type TransactionViewModelId = string;

// ===== Summary Type =====
export interface TransactionSummary {
  /** Transaction ID */
  id: string;
  /** Date for display */
  date: string;
  /** Description for display */
  description: string;
  /** Amount for display */
  amount: string;
  /** Category for display */
  category: string;
}