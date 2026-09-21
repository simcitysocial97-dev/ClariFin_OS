/**
 * Platform Runs Hooks — M9-C67.2
 *
 * Fetches run lists and individual run details from /platform/v1/runs.
 * Alias endpoints for /platform/v1/history/runs.
 */

import { useQuery } from '@tanstack/react-query';
import { apiFetchJson } from '@/lib/api/gateway';

export interface HistoryRunSummary {
  id: string;
  started_at: string;
  finished_at: string | null;
  duration_ms: number | null;
  status: string;
  capabilities_run: number;
  capabilities_passed: number;
  capabilities_failed: number;
  environment: string;
  intent: string;
  commit?: string;
  command?: string;
  profile?: string;
}

export interface RunsListData {
  page: number;
  page_size: number;
  total: number;
  items: HistoryRunSummary[];
}

export interface RunsListResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: RunsListData;
}

export interface RunDetailCapabilityResult {
  capability_id: string;
  status: string;
  duration_ms: number | null;
  evidence_ids: string[];
  error?: string;
}

export interface RunDetailData {
  id: string;
  started_at: string;
  finished_at: string | null;
  duration_ms: number | null;
  status: string;
  capabilities_run: number;
  capabilities_passed: number;
  capabilities_failed: number;
  capability_results: RunDetailCapabilityResult[];
  evidence_ids: string[];
  command?: string;
  profile?: string;
  commit?: string;
}

export interface RunDetailResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: RunDetailData;
}

const LIST_STALE_TIME_MS = 60_000;
const DETAIL_STALE_TIME_MS = 30_000;

export function usePlatformRuns(page = 1, page_size = 20) {
  return useQuery<RunsListResponse, Error>({
    queryKey: ['platform', 'runs', page, page_size],
    queryFn: () =>
      apiFetchJson(
        `/platform/v1/runs?page=${page}&page_size=${page_size}`
      ) as Promise<RunsListResponse>,
    staleTime: LIST_STALE_TIME_MS,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes('4')) return false;
      return failureCount < 2;
    },
  });
}

export function usePlatformRun(runId: string | undefined) {
  return useQuery<RunDetailResponse, Error>({
    queryKey: ['platform', 'runs', runId],
    queryFn: () =>
      apiFetchJson(
        `/platform/v1/runs/${encodeURIComponent(runId!)}`
      ) as Promise<RunDetailResponse>,
    enabled: !!runId,
    staleTime: DETAIL_STALE_TIME_MS,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes('4')) return false;
      return failureCount < 2;
    },
  });
}

export function isRunSuccess(status: string): boolean {
  return status === 'HEALTHY' || status === 'CLOSED' || status === 'PASSED';
}

export function isRunFailed(status: string): boolean {
  return status === 'UNHEALTHY' || status === 'FAILED' || status === 'BLOCKED';
}
