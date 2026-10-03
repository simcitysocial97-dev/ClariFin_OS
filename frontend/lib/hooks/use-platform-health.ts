/**
 * Platform Health Hook — M9-C57 Phase 5
 *
 * Fetches and caches the /platform/v1/health endpoint.
 * Uses the canonical API gateway for URL resolution and error handling.
 */

import { useQuery } from '@tanstack/react-query';
import { apiFetchJson, platformReadRetry } from '@/lib/api/gateway';

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

/**
 * The eight dimensions the console reports, in display order.
 *
 * M10-A3: these are the labels the dashboard renders as a status row. The
 * authoritative status for each one is a *top-level* field of the health
 * snapshot (`backend`, `frontend`, `database`, `architecture`, `verification`,
 * `evidence`, `ai`, `framework_integrity`) — NOT an entry in `data.domains`.
 * `data.domains` only carries the sub-authority breakdown (Verification,
 * EventStore, Framework Integrity), so looking the labels up there is what made
 * the operations dashboard print UNKNOWN for seven of eight dimensions while
 * the API was reporting HEALTHY/SAFE/CURRENT/VALID/READY.
 */
export const HEALTH_DIMENSIONS = [
  { label: 'Backend', field: 'backend' },
  { label: 'Frontend', field: 'frontend' },
  { label: 'Database', field: 'database' },
  { label: 'Architecture', field: 'architecture' },
  { label: 'Verification', field: 'verification' },
  { label: 'Evidence', field: 'evidence' },
  { label: 'AI Runtime', field: 'ai' },
  { label: 'Framework Integrity', field: 'framework_integrity' },
] as const satisfies ReadonlyArray<{ label: string; field: keyof PlatformHealthData }>;

export function usePlatformHealth() {
  return useQuery<PlatformHealthResponse, Error>({
    queryKey: ['platform', 'health'],
    queryFn: () => apiFetchJson('/platform/v1/health') as Promise<PlatformHealthResponse>,
    staleTime: STALE_TIME_MS,
    retry: platformReadRetry,
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
    // M10-A3: expose the raw snapshot slices so surfaces render what the API
    // actually reported instead of re-deriving (and losing) it.
    dimensions: HEALTH_DIMENSIONS.map(({ label, field }) => ({
      label,
      // Top-level field is authoritative. A `data.domains` entry with the same
      // name is only a fallback for the two dimensions that also appear in the
      // sub-authority breakdown.
      status: data?.data?.[field] ?? matchDomain(data, label) ?? 'UNKNOWN',
    })),
    domains: data?.data?.domains ?? [],
  };
}

/** Case-insensitive lookup of a sub-authority domain by display label. */
function matchDomain(
  data: PlatformHealthResponse | undefined,
  label: string,
): string | undefined {
  const domains = data?.data?.domains ?? [];
  const wanted = label.toLowerCase();
  return domains.find((d) => d.name.toLowerCase() === wanted)?.status;
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
