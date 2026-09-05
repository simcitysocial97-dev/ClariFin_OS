/**
 * Verification Center hooks — M9-C57 Phase 6
 *
 * Thin React Query layer over the canonical Platform API gateway.
 * All write endpoints (run, cancel) still enter the C50 task/execution
 * path — the hook never invents a second executor.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetchJson, apiFetch } from '@/lib/api/gateway';

// ---------------------------------------------------------------------------
// Types (mirror Phase 1 contracts; kept minimal here to stay honest)
// ---------------------------------------------------------------------------


type ContractEnvelope<TData = unknown> = {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: TData;
};

export type CapabilityItem = {
  id: string;
  name: string;
  stage: string;
  cost: string;
  authorization: string;
  produces: string[];
  triggers: string[];
};

export type CapabilityDetail = CapabilityItem & {
  owner: string;
  command: string | null;
  dependencies: string[];
  recent_executions: string[];
  evidence: string[];
  cache_status: string | null;
  failure_history: string[];
  health: string;
};

export type VerificationRunResultData = {
  capability_id: string;
  status: string;
  task_id: string | null;
  execution_id: string | null;
  started_at: string;
  finished_at: string | null;
  duration_ms: number | null;
  message: string;
};

// ---------------------------------------------------------------------------
// Read hooks
// ---------------------------------------------------------------------------


export function useCapabilities() {
  return useQuery<ContractEnvelope<{ count: number; categories: string[]; items: CapabilityItem[] }>, Error>({
    queryKey: ['platform', 'capabilities:list'],
    queryFn: () => apiFetchJson('/platform/v1/capabilities') as Promise<ContractEnvelope<{ count: number; categories: string[]; items: CapabilityItem[] }>>,
    staleTime: 60_000,
  });
}

export function useCapabilityDetail(capabilityId: string) {
  return useQuery<ContractEnvelope<CapabilityDetail>, Error>({
    queryKey: ['platform', 'capabilities:detail', capabilityId],
    queryFn: () => apiFetchJson(`/platform/v1/capabilities/${capabilityId}`) as Promise<ContractEnvelope<CapabilityDetail>>,
    enabled: !!capabilityId,
    staleTime: 60_000,
  });
}

export function useRecentVerificationRuns(limit = 20) {
  return useQuery<ContractEnvelope<{ count: number; items: Array<{ id: string; started_at: string; finished_at: string | null; duration_ms: number | null; status: string; capabilities_run: number; capabilities_passed: number; capabilities_failed: number }> }>, Error>({
    queryKey: ['platform', 'verification:runs:recent', limit],
    queryFn: () => apiFetchJson('/platform/v1/verification/runs/recent') as Promise<ContractEnvelope<{ count: number; items: Array<{ id: string; started_at: string; finished_at: string | null; duration_ms: number | null; status: string; capabilities_run: number; capabilities_passed: number; capabilities_failed: number }> }>>,
    staleTime: 30_000,
  });
}

// ---------------------------------------------------------------------------
// Write hooks — every run enters the C50 path; no second executor
// ---------------------------------------------------------------------------


export function useVerificationRun() {
  const qc = useQueryClient();
  return useMutation<ContractEnvelope<VerificationRunResultData>, Error, { capability_id?: string | null }>({
    mutationFn: async (body) => {
      const res = await apiFetch('/platform/v1/verification/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body?.capability_id ? JSON.stringify({ capability_id: body.capability_id }) : '{}',
      });
      const data = await res.json();
      return data as ContractEnvelope<VerificationRunResultData>;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['platform', 'verification:runs:recent'] });
      void qc.invalidateQueries({ queryKey: ['platform', 'health'] });
    },
  });
}

export function useVerificationRunGroup() {
  const qc = useQueryClient();
  return useMutation<ContractEnvelope<VerificationRunResultData>, Error, { group?: string | null }>({
    mutationFn: async (body) => {
      const res = await apiFetch('/platform/v1/verification/run/group', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body?.group ? JSON.stringify({ group: body.group }) : '{}',
      });
      return (await res.json()) as ContractEnvelope<VerificationRunResultData>;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['platform', 'verification:runs:recent'] });
    },
  });
}

export function useVerificationRunAffected() {
  const qc = useQueryClient();
  return useMutation<ContractEnvelope<VerificationRunResultData>, Error, void>({
    mutationFn: async () => {
      const res = await apiFetch('/platform/v1/verification/run/affected', { method: 'POST' });
      return (await res.json()) as ContractEnvelope<VerificationRunResultData>;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['platform', 'verification:runs:recent'] });
    },
  });
}

export function useVerificationRunFull() {
  const qc = useQueryClient();
  return useMutation<ContractEnvelope<VerificationRunResultData>, Error, void>({
    mutationFn: async () => {
      const res = await apiFetch('/platform/v1/verification/run/full', { method: 'POST' });
      return (await res.json()) as ContractEnvelope<VerificationRunResultData>;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['platform', 'verification:runs:recent'] });
    },
  });
}

export function useCancelTask() {
  const qc = useQueryClient();
  return useMutation<ContractEnvelope<{ id: string; cancelled: boolean; reason: string }>, Error, string>({
    mutationFn: async (taskId) => {
      const res = await apiFetch(`/platform/v1/tasks/${taskId}/cancel`, { method: 'POST' });
      return (await res.json()) as ContractEnvelope<{ id: string; cancelled: boolean; reason: string }>;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['platform', 'tasks'] });
    },
  });
}
