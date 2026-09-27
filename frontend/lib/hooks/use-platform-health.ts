/**
 * Platform Health Hook — M9-C57 Phase 5
 *
 * Fetches and caches the /platform/v1/health endpoint.
 * Uses the canonical API gateway for URL resolution and error handling.
 */

import { useQuery } from '@tanstack/react-query';
import { apiFetchJson, transientRetryPolicy } from '@/lib/api/gateway';

export interface DomainHealth {
  name: string;
  status: string;
  last_check: string;
  source: string;
  detail?: string;
}

export interface PlatformHealthData {
  platform: string;
  backend: string;
  frontend: string;
  database: string;
  architecture: string;
  verification: string;
  evidence: string;
  ai: string;
  framework_integrity: string;
  domains: DomainHealth[];
}

export interface PlatformHealthResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: PlatformHealthData;
}

const STALE_TIME_MS = 60_000; // 1 minute, matches cache TTL

export function usePlatformHealth() {
  return useQuery<PlatformHealthResponse, Error>({
    queryKey: ['platform', 'health'],
    queryFn: () => apiFetchJson('/platform/v1/health') as Promise<PlatformHealthResponse>,
    staleTime: STALE_TIME_MS,
    retry: transientRetryPolicy,
  });
}

/**
 * Derive a human-readable summary from the health snapshot.
 */
export function usePlatformHealthSummary() {
  const { data, isLoading, error, isError, refetch } = usePlatformHealth();

  return {
    isLoading,
    // M9-C71: consumers must be able to tell "still working" from "cannot
    // work". The operations dashboard previously had no way to distinguish the
    // two and rendered an indefinite "Loading platform state…".
    error,
    isError,
    refetch,
    platformStatus: data?.data?.platform ?? 'UNKNOWN',
    frameworkIntegrityStatus: data?.data?.framework_integrity ?? 'UNKNOWN',
    isHealthy: data?.data?.platform === 'HEALTHY',
    isUnhealthy: data?.data?.platform === 'UNHEALTHY',
    verificationStatus: data?.data?.verification ?? 'UNKNOWN',
    architectureStatus: data?.data?.architecture ?? 'UNKNOWN',
    domainCount: data?.data?.domains?.length ?? 0,
    unhealthyDomains:
      data?.data?.domains?.filter((d) => d.status === 'UNHEALTHY' || d.status === 'DEGRAD') ??
      [],
    verificationSuccessRate: computeSuccessRate(data),
  };
}

function computeSuccessRate(data: PlatformHealthResponse | undefined): number | null {
  if (!data) return null;
  const verif = data.data;
  // We don't have raw counts here — fall back to status-based heuristic.
  if (verif.verification === 'HEALTHY') return 1.0;
  if (verif.verification === 'DEGRAD') return 0.8;
  if (verif.verification === 'UNHEALTHY') return 0.33;
  return null;
}
