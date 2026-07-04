/**
 * React Hooks for Finance Data
 * Wraps the API client with useState/useEffect for data fetching
 */

import { useState, useEffect, useCallback } from 'react';
import {
  fetchOverview,
  fetchTransactions,
  fetchStatements,
  fetchCategories,
  fetchAnalytics,
  fetchBanks,
  fetchCategoryList,
  fetchMembers,
  uploadStatement,
  updateTransactionCategory,
  deleteStatement,
  exportCSV,
  fetchNetWorth,
  type Transaction,
  type OverviewData,
  type Statement,
  type CategorySummary,
  type Member,
  type UploadResult,
  type NetWorth,
} from '@/lib/api/client';
import type {
  CategoriesResponse,
  AnalyticsData,
  MonthlyBreakdown,
  UncategorizedPattern,
} from '@/types/api';

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
// useCategories
// ============================================================================

export function useCategories(params?: {
  exclude_transfers?: boolean;
  member?: string;
  drill_category?: string;
}): HookState<CategoriesResponse> {
  const [data, setData] = useState<CategoriesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchCategories(params);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [params?.exclude_transfers, params?.member, params?.drill_category]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// ============================================================================
// useAnalytics
// ============================================================================

export function useAnalytics(params?: {
  exclude_transfers?: boolean;
  member?: string;
}): HookState<AnalyticsData> {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAnalytics(params);
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
// useMembers
// ============================================================================

export function useMembers(): HookState<Member[]> {
  const [data, setData] = useState<Member[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchMembers();
      setData(result.members);
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
// useNetWorth
// ============================================================================

export function useNetWorth(): HookState<NetWorth> {
  const [data, setData] = useState<NetWorth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchNetWorth();
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
// useUpdateCategory
// ============================================================================

interface UpdateCategoryState {
  updating: boolean;
  error: Error | null;
  update: (id: number, category: string, subcategory?: string) => Promise<void>;
}

export function useUpdateCategory(): UpdateCategoryState {
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const update = useCallback(async (id: number, category: string, subcategory?: string) => {
    setUpdating(true);
    setError(null);
    try {
      await updateTransactionCategory(id, category, subcategory);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Update failed'));
      throw err;
    } finally {
      setUpdating(false);
    }
  }, []);

  return { updating, error, update };
}

// ============================================================================
// useDeleteStatement
// ============================================================================

interface DeleteStatementState {
  deleting: boolean;
  error: Error | null;
  deleteStatement: (id: number) => Promise<void>;
}

export function useDeleteStatement(): DeleteStatementState {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const deleteStmt = useCallback(async (id: number) => {
    setDeleting(true);
    setError(null);
    try {
      await deleteStatement(id);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Delete failed'));
      throw err;
    } finally {
      setDeleting(false);
    }
  }, []);

  return { deleting, error, deleteStatement: deleteStmt };
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
