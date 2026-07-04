/**
 * React Query Hooks
 * =================
 * 
 * High-performance data fetching using TanStack Query (React Query).
 * These hooks replace the manual useState/useEffect pattern for high-traffic queries.
 * 
 * Migrated hooks:
 * - useOverviewQuery (replaces useOverview)
 * - useImportsQuery (replaces useV2Imports)
 */

import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchOverview,
  fetchV2Imports,
} from "@/lib/api/client";
import type { ImportListResponse } from "@/types/v2";
import type { OverviewData } from "@/lib/api/client";

// ============================================================================
// Query Keys
// ============================================================================

export const queryKeys = {
  overview: ["overview"] as const,
  imports: (params?: { status?: string; page?: number; per_page?: number }) =>
    ["imports", params] as const,
};

// ============================================================================
// useOverviewQuery
// ============================================================================

interface UseOverviewQueryResult {
  data: OverviewData | undefined;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * React Query hook for dashboard overview data.
 * Replaces: useOverview from use-finance-data.ts
 */
export function useOverviewQuery(): UseOverviewQueryResult {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery<OverviewData, Error>({
    queryKey: queryKeys.overview,
    queryFn: fetchOverview,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const refetch = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.overview });
  };

  return {
    data,
    isLoading,
    error: error || null,
    refetch,
  };
}

// ============================================================================
// useImportsQuery
// ============================================================================

interface UseImportsQueryParams {
  status?: string;
  page?: number;
  per_page?: number;
}

interface UseImportsQueryResult {
  data: ImportListResponse | undefined;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * React Query hook for V2 imports list.
 * Replaces: useV2Imports from use-finance-data.ts
 */
export function useImportsQuery(params?: UseImportsQueryParams): UseImportsQueryResult {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery<ImportListResponse, Error>({
    queryKey: queryKeys.imports(params),
    queryFn: () => fetchV2Imports(params),
    staleTime: 30 * 1000, // 30 seconds - imports change frequently
  });

  const refetch = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.imports(params) });
  };

  return {
    data,
    isLoading,
    error: error || null,
    refetch,
  };
}

