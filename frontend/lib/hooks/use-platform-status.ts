/**
 * Platform Status Hook — M9-C67.2
 *
 * Fetches the canonical operator-oriented snapshot from /platform/v1/status.
 * Returns repository identity, commit, certification state, capability/workflow counts.
 */

import { useQuery } from '@tanstack/react-query';
import { apiFetchJson } from '@/lib/api/gateway';

export interface PlatformStatusData {
  repository: string;
  commit_sha: string;
  tree_sha: string;
  branch: string;
  runtime_version: string;
  fingerprint: string;
  framework_health: string;
  certification_state: string;
  capability_count: number;
  profile_count: number;
  workflow_count: number;
  recent_run_status: string | null;
  recent_run_id: string | null;
}

export interface PlatformStatusResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: PlatformStatusData;
}

const STALE_TIME_MS = 30_000;

export function usePlatformStatus() {
  return useQuery<PlatformStatusResponse, Error>({
    queryKey: ['platform', 'status'],
    queryFn: () => apiFetchJson('/platform/v1/status') as Promise<PlatformStatusResponse>,
    staleTime: STALE_TIME_MS,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes('4')) return false;
      return failureCount < 2;
    },
  });
}

export function usePlatformCertificationState() {
  const { data } = usePlatformStatus();
  return data?.data?.certification_state ?? 'UNKNOWN';
}

export function usePlatformCommit() {
  const { data } = usePlatformStatus();
  return data?.data?.commit_sha ?? '';
}

export function usePlatformCapabilityCount() {
  const { data } = usePlatformStatus();
  return data?.data?.capability_count ?? 0;
}

export function usePlatformWorkflowCount() {
  const { data } = usePlatformStatus();
  return data?.data?.workflow_count ?? 0;
}
