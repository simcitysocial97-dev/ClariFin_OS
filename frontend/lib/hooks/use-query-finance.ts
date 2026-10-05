import { useState, useCallback } from 'react';
import { apiFetch } from '@/lib/api/gateway';
import {
  fetchTransactions,
  fetchStatements,
  fetchBanks,
  fetchCategoryList,
  uploadStatement,
  exportCSV,
  type Transaction,
  type Statement,
} from '@/lib/api/client';
import type { OverviewData } from '@/lib/api/client';
import type { HookState } from './use-async-query';
import { useAsyncQuery } from './use-async-query';

// ============================================================================
// Query Keys
// ============================================================================

export const queryKeys = {
  transactions: (params?: any) => ['transactions', params] as const,
  statements: ['statements'] as const,
  banks: ['banks'] as const,
  categories: ['categories'] as const,
  upload: ['upload'] as const,
  export: (params?: any) => ['export', params] as const,
  overview: ['overview'] as const,
};

// ============================================================================
// useOverview
// ============================================================================

/**
 * Overview totals, for cache invalidation after a statement upload.
 *
 * M10-A3: this requested `/api/overview`. The backend exposes overview only at
 * `/api/v1/overview` (`backend/src/routers/transactions.py`), so every call
 * returned HTTP 404 — verified against the running API. Its only consumer is
 * `components/upload/upload-modal.tsx`, which calls it purely to invalidate
 * cached totals after an upload, so the failure was silent: the upload
 * reported success while the overview cache was never refreshed and the
 * dashboard kept showing pre-upload totals.
 *
 * The sibling `useOverview` in `lib/hooks/use-overview.ts` already targets the
 * correct path and validates the response against `OverviewSchema`; the path
 * here is corrected to match, and a failure is surfaced rather than swallowed.
 * `exclude_transfers` / `member` are dropped: the registered backend route
 * takes no such parameters, so sending them would imply filtering that is not
 * applied.
 */
export async function fetchOverview(): Promise<OverviewData> {
  const res = await apiFetch(`/api/v1/overview`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export function useOverviewQuery(): HookState<OverviewData> {
  return useAsyncQuery(queryKeys.overview, () => fetchOverview());
}

// ============================================================================
// useTransactions
// ============================================================================

export function useTransactionsQuery(params?: {
  search?: string;
  bank?: string;
  category?: string;
  type?: string;
  member?: string;
  limit?: number;
  offset?: number;
}): HookState<{ transactions: Transaction[]; total: number }> {
  return useAsyncQuery(
    queryKeys.transactions(params),
    () => fetchTransactions(params)
  );
}

// ============================================================================
// useStatements
// ============================================================================

export function useStatementsQuery(): HookState<Statement[]> {
  return useAsyncQuery(
    queryKeys.statements,
    fetchStatements
  );
}

// ============================================================================
// useBanks
// ============================================================================

export function useBanksQuery(): HookState<string[]> {
  const result = useAsyncQuery(
    queryKeys.banks,
    async () => {
      const res = await fetchBanks();
      return res.banks;
    }
  );
  return result;
}

// ============================================================================
// useCategoryList
// ============================================================================

export function useCategoryListQuery(): HookState<string[]> {
  const result = useAsyncQuery(
    queryKeys.categories,
    async () => {
      const res = await fetchCategoryList();
      return res.categories;
    }
  );
  return result;
}

// ============================================================================
// useUpload
// ============================================================================

interface UploadState {
  uploading: boolean;
  error: Error | null;
  result: any | null;
  upload: (file: File, member?: string) => Promise<void>;
}

export function useUploadQuery(): UploadState {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<any | null>(null);

  const upload = useCallback(async (file: File, member: string = 'Self') => {
    setUploading(true);
    setError(null);
    setResult(null);
    try {
      const uploadResult = await uploadStatement(file, member);
      setResult(uploadResult);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Upload failed'));
      throw err;
    } finally {
      setUploading(false);
    }
  }, []);

  return { uploading, error, result, upload };
}

// ============================================================================
// useExportCSV
// ============================================================================

interface ExportCSVState {
  exporting: boolean;
  error: Error | null;
  exportCSV: (params?: Parameters<typeof exportCSV>[0]) => Promise<Blob | null>;
}

export function useExportCSVQuery(): ExportCSVState {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const exportData = useCallback(async (params?: Parameters<typeof exportCSV>[0]) => {
    setExporting(true);
    setError(null);
    try {
      const blob = await exportCSV(params);
      return blob;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Export failed'));
      return null;
    } finally {
      setExporting(false);
    }
  }, []);

  return { exporting, error, exportCSV: exportData };
}