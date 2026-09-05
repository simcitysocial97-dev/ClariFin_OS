/**
 * Platform Health Hook — M9-C57 Phase 5
 *
 * Fetches and caches the /platform/v1/health endpoint.
 * Uses the canonical API gateway for URL resolution and error handling.
 */

import { useQuery } from '@tanstack/react-query';
import { apiFetchJson } from '@/lib/api/gateway';

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
    retry: (failureCount, error) => {
      // Only retry transient errors (network, 5xx). Permanent 4xx errors are not retried.
      if (error instanceof Error && error.message.includes('4')) return false;
      return failureCount < 2;
    },
  });
}

/**
 * Derive a human-readable summary from the health snapshot.
 */
export function usePlatformHealthSummary() {
  const { data, isLoading } = usePlatformHealth();

  return {
    isLoading,
    platformStatus: data?.data?.platform ?? 'UNKNOWN',
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
