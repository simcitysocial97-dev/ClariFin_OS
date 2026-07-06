/**
 * React Hooks for Finance Data
 * Wraps the API client with useState/useEffect for data fetching
 */

import { useState, useEffect, useCallback } from 'react';
import {
  fetchOverview,
  fetchTransactions,
  fetchStatements,
  fetchBanks,
  fetchCategoryList,
  uploadStatement,
  exportCSV,
  type Transaction,
  type OverviewData,
  type Statement,
  type CategorySummary,
  type UploadResult,
} from '@/lib/api/client';

// ============================================================================
// HOOK RETURN TYPES
// ============================================================================

interface HookState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

// ============================================================================
// useOverview
// ============================================================================

export function useOverview(params?: {
  exclude_transfers?: boolean;
  member?: string;
}): HookState<OverviewData> {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchOverview(params);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [params?.exclude_transfers, params?.member]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// ============================================================================
// useTransactions
// ============================================================================

export function useTransactions(params?: {
  search?: string;
  bank?: string;
  category?: string;
  type?: string;
  member?: string;
  limit?: number;
  offset?: number;
}): HookState<{ transactions: Transaction[]; total: number }> {
  const [data, setData] = useState<{ transactions: Transaction[]; total: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchTransactions(params);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [
    params?.search,
    params?.bank,
    params?.category,
    params?.type,
    params?.member,
    params?.limit,
    params?.offset,
  ]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// ============================================================================
// useStatements
// ============================================================================

export function useStatements(): HookState<Statement[]> {
  const [data, setData] = useState<Statement[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchStatements();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// ============================================================================
// useBanks
// ============================================================================

export function useBanks(): HookState<string[]> {
  const [data, setData] = useState<string[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchBanks();
      setData(result.banks);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// ============================================================================
// useCategoryList
// ============================================================================

export function useCategoryList(): HookState<string[]> {
  const [data, setData] = useState<string[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchCategoryList();
      setData(result.categories);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// ============================================================================
// useUpload
// ============================================================================

interface UploadState {
  uploading: boolean;
  error: Error | null;
  result: UploadResult | null;
  upload: (file: File, member?: string) => Promise<void>;
}

export function useUpload(): UploadState {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<UploadResult | null>(null);

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

export function useExportCSV(): ExportCSVState {
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