/**
 * V2 API Types - Jobs and Imports
 *
 * Types for the V2 staging-based import pipeline (B1–B5).
 * These types correspond to the endpoints documented in V2_API_CONTRACT_FACTS.md
 */

// ============================================================================
// JOBS TYPES
// ============================================================================

export type JobStatus = 'PENDING' | 'CLAIMED' | 'COMPLETED' | 'FAILED';

export interface Job {
  id: string;
  job_type: string;
  status: JobStatus;
  payload: Record<string, unknown>;
  total_items: number;
  processed_items: number;
  progress_pct: number;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  error?: string;
  worker_id?: string;
}

export interface JobCreateRequest {
  job_type: string;
  payload?: Record<string, unknown>;
  total_items: number;
}

export interface JobCreateResponse {
  job_id: string;
}

// ============================================================================
// IMPORTS TYPES
// ============================================================================

export type ImportStatus = 'STAGED' | 'NEEDS_REVIEW' | 'COMMITTED' | 'FAILED';

export interface ImportValidation {
  valid: boolean;
  reason?: string;
  opening_balance_paise?: number;
  closing_balance_paise?: number;
}

export interface ImportCommittedInfo {
  inserted: number;
  skipped: number;
}

export interface ImportItem {
  id: string;
  status: ImportStatus;
  source_filename: string;
  bank: string;
  delta_paise: number | null;
  opening_balance_paise: number | null;
  closing_balance_paise: number | null;
  transaction_count: number;
  created_at: string;
  committed_at: string | null;
  error: string | null;
  template_id: string | null;
}

export interface ImportPdfResponse {
  success: boolean;
  statement_id: string;
  status: ImportStatus;
  delta_paise: number;
  transaction_count: number;
  bank: string;
  filename: string;
  extractor: 'legacy' | 'docling' | 'bbox';
  validation: ImportValidation;
  committed?: ImportCommittedInfo;
  error?: string;
  // Additional fields from backend
  fingerprint: string;
  template_applied: boolean;
  suggested_bbox_norm: number[] | null;
  preview_rows?: Array<{
    date: string;
    description: string;
    debit_paise: number | null;
    credit_paise: number | null;
    balance_paise: number | null;
  }>;
}

export interface ImportListResponse {
  items: ImportItem[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
}

export interface ImportStatusResponse {
  id: string;
  status: ImportStatus;
  source_filename: string;
  bank: string;
  delta_paise: number | null;
  opening_balance_paise: number | null;
  closing_balance_paise: number | null;
  transaction_count: number;
  created_at: string;
  committed_at: string | null;
  error: string | null;
}

export interface CommitResponse {
  success: boolean;
  inserted: number;
  skipped: number;
  error: string | null;
}

export interface DiscardResponse {
  success: boolean;
}

export interface RevalidateResponse {
  success: boolean;
  delta_paise: number;
  valid: boolean;
  committed: boolean;
  inserted: number;
  skipped: number;
  error: string | null;
}

