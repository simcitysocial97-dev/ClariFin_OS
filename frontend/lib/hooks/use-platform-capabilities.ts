/**
 * Platform Capabilities Hook — M9-C57 Phase 9C
 *
 * Fetches capability list, detail, and graph from /platform/v1/capabilities/*.
 */

import { useQuery } from '@tanstack/react-query';
import { apiFetchJson, platformReadRetry } from '@/lib/api/gateway';

export interface CapabilityListItem {
  id: string;
  name: string;
  stage: string;
  cost: string;
  authorization: string;
  produces: string[];
  triggers: string[];
}

export interface CapabilityListData {
  count: number;
  categories: string[];
  items: CapabilityListItem[];
}

export interface CapabilityListResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: CapabilityListData;
}

export interface CapabilityDetailData {
  id: string;
  name: string;
  stage: string;
  cost: string;
  authorization: string;
  owner: string;
  command?: string | null;
  dependencies: string[];
  produces: string[];
  triggers: string[];
  recent_executions: string[];
  evidence: string[];
  cache_status?: string | null;
  failure_history: string[];
  health: string;
}

export interface CapabilityDetailResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: CapabilityDetailData;
}

export interface CapabilityGraphData {
  capability_id: string;
  upstream: string[];
  downstream: string[];
}

export interface CapabilityGraphResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: CapabilityGraphData;
}

const STALE_TIME_MS = 60_000;

export function useCapabilityList() {
  return useQuery<CapabilityListResponse, Error>({
    queryKey: ['platform', 'capabilities'],
    queryFn: () =>
      apiFetchJson('/platform/v1/capabilities') as Promise<CapabilityListResponse>,
    staleTime: STALE_TIME_MS,
    retry: platformReadRetry,
  });
}

export function useCapabilityDetail(capabilityId: string | undefined) {
  return useQuery<CapabilityDetailResponse, Error>({
    queryKey: ['platform', 'capabilities', capabilityId],
    queryFn: () =>
      apiFetchJson(
        `/platform/v1/capabilities/${encodeURIComponent(capabilityId!)}`,
      ) as Promise<CapabilityDetailResponse>,
    enabled: !!capabilityId,
    staleTime: STALE_TIME_MS,
    retry: platformReadRetry,
  });
}

export function useCapabilityGraph(capabilityId: string | undefined) {
  return useQuery<CapabilityGraphResponse, Error>({
    queryKey: ['platform', 'capabilities', capabilityId, 'graph'],
    queryFn: () =>
      apiFetchJson(
        `/platform/v1/capabilities/${encodeURIComponent(capabilityId!)}/graph`,
      ) as Promise<CapabilityGraphResponse>,
    enabled: !!capabilityId,
    staleTime: STALE_TIME_MS,
    retry: platformReadRetry,
  });
}
