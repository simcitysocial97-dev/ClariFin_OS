/**
 * Platform Architecture Hook — M9-C57 Phase 9B
 *
 * Fetches architecture authorities, boundaries, duplicates, bypasses,
 * deprecations, and unmapped findings from /platform/v1/architecture/*.
 */

import { useQuery } from '@tanstack/react-query';
import { apiFetchJson } from '@/lib/api/gateway';

export interface AuthoritySummary {
  name: string;
  owner: string;
  status: string;
  last_check: string;
  issues: number;
}

export interface AuthoritiesResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: { count: number; items: AuthoritySummary[] };
}

export interface AuthorityDetailData {
  name: string;
  owner: string;
  status: string;
  last_check: string;
  description: string;
  recent_evidence: string[];
  issues: number;
}

export interface AuthorityDetailResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: AuthorityDetailData;
}

export interface ArchitectureIssue {
  id: string;
  severity: string;
  title: string;
  location: string;
  evidence: string[];
  first_seen?: string | null;
}

export interface FindingsResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: { count: number; items: ArchitectureIssue[] };
}

const STALE_TIME_MS = 60_000;

export function useArchitectureAuthorities() {
  return useQuery<AuthoritiesResponse, Error>({
    queryKey: ['platform', 'architecture', 'authorities'],
    queryFn: () =>
      apiFetchJson('/platform/v1/architecture/authorities') as Promise<AuthoritiesResponse>,
    staleTime: STALE_TIME_MS,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes('4')) return false;
      return failureCount < 2;
    },
  });
}

export function useAuthorityDetail(name: string | undefined) {
  return useQuery<AuthorityDetailResponse, Error>({
    queryKey: ['platform', 'architecture', 'authority', name],
    queryFn: () =>
      apiFetchJson(
        `/platform/v1/architecture/authority/${encodeURIComponent(name!)}`,
      ) as Promise<AuthorityDetailResponse>,
    enabled: !!name,
    staleTime: STALE_TIME_MS,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes('4')) return false;
      return failureCount < 2;
    },
  });
}

export function useArchitectureFindings(kind: string) {
  return useQuery<FindingsResponse, Error>({
    queryKey: ['platform', 'architecture', kind],
    queryFn: () =>
      apiFetchJson(`/platform/v1/architecture/${kind}`) as Promise<FindingsResponse>,
    staleTime: STALE_TIME_MS,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes('4')) return false;
      return failureCount < 2;
    },
  });
}

export function useArchitectureBoundaries() {
  return useArchitectureFindings('boundaries');
}

export function useArchitectureDuplicates() {
  return useArchitectureFindings('duplicates');
}

export function useArchitectureBypasses() {
  return useArchitectureFindings('bypasses');
}

export function useArchitectureDeprecations() {
  return useArchitectureFindings('deprecations');
}

export function useArchitectureUnmapped() {
  return useArchitectureFindings('unmapped');
}
