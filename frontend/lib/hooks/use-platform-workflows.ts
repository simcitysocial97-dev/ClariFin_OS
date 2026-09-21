/**
 * Platform Workflows Hook — M9-C67.2
 *
 * Fetches the canonical workflow inventory from /platform/v1/workflows.
 * Same source as `verify inspect workflows`.
 */

import { useQuery } from '@tanstack/react-query';
import { apiFetchJson } from '@/lib/api/gateway';

export interface WorkflowItem {
  workflow_id: string;
  name: string;
  path: string;
  triggers: string[];
  jobs: string[];
  commands: string[];
  canonical_command: string;
  local_executable: boolean;
  boundary_classification: string;
  environment_requirements: string[];
  parity_status: string;
}

export interface WorkflowsData {
  count: number;
  items: WorkflowItem[];
  source: string;
  last_updated: string;
}

export interface WorkflowsResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: WorkflowsData;
}

export type BoundaryClassification =
  | 'LOCAL'
  | 'GITHUB_ONLY'
  | 'ENVIRONMENT_BOUNDARY'
  | 'EXTERNAL_TOOLING'
  | 'EXTERNAL_SERVICE'
  | 'BROWSER';

const BOUNDARY_COLORS: Record<string, string> = {
  LOCAL: 'text-emerald-400',
  GITHUB_ONLY: 'text-blue-400',
  ENVIRONMENT_BOUNDARY: 'text-amber-400',
  EXTERNAL_TOOLING: 'text-orange-400',
  EXTERNAL_SERVICE: 'text-red-400',
  BROWSER: 'text-purple-400',
};

export const BOUNDARY_DESCRIPTIONS: Record<string, string> = {
  LOCAL: 'Runs locally without external dependencies',
  GITHUB_ONLY: 'Requires GitHub Actions infrastructure',
  ENVIRONMENT_BOUNDARY: 'Needs specific environment setup',
  EXTERNAL_TOOLING: 'Depends on external tooling (Docker, mutmut, etc.)',
  EXTERNAL_SERVICE: 'Calls external services',
  BROWSER: 'Requires browser automation',
};

export function usePlatformWorkflows() {
  return useQuery<WorkflowsResponse, Error>({
    queryKey: ['platform', 'workflows'],
    queryFn: () => apiFetchJson('/platform/v1/workflows') as Promise<WorkflowsResponse>,
    staleTime: 120_000,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes('4')) return false;
      return failureCount < 2;
    },
  });
}

export function useWorkflowByBoundary() {
  const { data } = usePlatformWorkflows();
  const items = data?.data?.items ?? [];

  const byBoundary: Record<string, WorkflowItem[]> = {};
  for (const w of items) {
    const key = w.boundary_classification;
    if (!byBoundary[key]) byBoundary[key] = [];
    byBoundary[key].push(w);
  }

  return { byBoundary, totalCount: items.length };
}

export function getBoundaryColor(classification: string): string {
  return BOUNDARY_COLORS[classification] ?? 'text-slate-400';
}

export function getBoundaryDescription(classification: string): string {
  return BOUNDARY_DESCRIPTIONS[classification] ?? 'Unknown classification';
}
