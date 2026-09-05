/**
 * Platform Errors Hook — M9-C57 Phase 5
 *
 * Fetches current and recent errors from /platform/v1/errors/*.
 */

import { useQuery } from '@tanstack/react-query';
import { apiFetchJson } from '@/lib/api/gateway';

export interface PlatformErrorItem {
  id: string;
  code: string;
  layer: string;
  message: string;
  first_seen: string;
  last_seen: string;
  occurrences: number;
  affected_workflow?: string;
}

export interface ErrorsListData {
  window: string;
  count: number;
  items: PlatformErrorItem[];
}

export interface ErrorsListResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: ErrorsListData;
}

export function usePlatformErrors(window = 'current') {
  const url = `/platform/v1/errors/${window}`;
  return useQuery<ErrorsListResponse, Error>({
    queryKey: ['platform', 'errors', window],
    queryFn: () => apiFetchJson(url) as Promise<ErrorsListResponse>,
    staleTime: 60_000,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes('4')) return false;
      return failureCount < 2;
    },
  });
}

export function useCurrentErrorCount() {
  const { data } = usePlatformErrors('current');
  return data?.data?.count ?? 0;
}

export function useRecentErrorCount() {
  const { data } = usePlatformErrors('recent');
  return data?.data?.count ?? 0;
}
