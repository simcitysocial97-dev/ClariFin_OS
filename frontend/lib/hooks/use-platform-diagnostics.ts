/**
 * Platform Diagnostics Hooks — M9-C63 Phase G
 *
 * Provides typed access to the diagnostic engine and failure signatures.
 * Data sources:
 * - POST /platform/v1/diagnose (deterministic diagnostic engine)
 * - POST /platform/v1/diagnose/register (signature registration)
 * - GET /platform/v1/health (for system-level diagnostics)
 * - GET /platform/v1/errors/* (for error-based diagnostics)
 * - GET /platform/v1/tasks (for task/obligation diagnostics)
 * - runtime/generated/diagnostic-signatures.json (local signature store)
 */

import { useMutation, useQuery } from '@tanstack/react-query';
import { apiFetchJson, apiFetch } from '@/lib/api/gateway';

// ---------------------------------------------------------------------------
// Types matching backend contracts (runtime/platform/api/contracts/diagnostics.py)
// ---------------------------------------------------------------------------

export interface DiagnosticRecommendationItem {
  action: string;
  target: string;
}

export interface DiagnosticResultData {
  symptom: string;
  error_code: string | null;
  capability_id: string | null;
  level: string; // L0-L5
  fact: string;
  evidence: string[];
  affected_capability: string | null;
  recommendation: DiagnosticRecommendationItem[];
  generated_at: string;
}

export interface DiagnosticResultEnvelope {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: DiagnosticResultData;
}

export interface DiagnosticSignatureData {
  id: string;
  error_code: string;
  description: string;
  affected_capability: string;
  severity: string;
  occurrences: number;
  first_seen: string;
  last_seen: string;
}

export interface DiagnosticSignatureEnvelope {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: DiagnosticSignatureData;
}

export interface DiagnosticRecommendationData {
  signature_id: string;
  severity: string;
  recommended_verification: string[];
}

export interface DiagnosticRecommendationEnvelope {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: DiagnosticRecommendationData;
}

// ---------------------------------------------------------------------------
// Local failure signatures (from diagnostic-signatures.json)
// ---------------------------------------------------------------------------

export interface LocalSignatureStore {
  signatures: DiagnosticSignatureData[];
  index: Record<string, string[]>;
}

// ---------------------------------------------------------------------------
// Diagnostic Categories (C63 §10)
// ---------------------------------------------------------------------------

export type DiagnosticCategory =
  | 'FAILED'
  | 'BLOCKED'
  | 'INTERRUPTED'
  | 'STALE'
  | 'DIVERGED';

export interface CategoryDiagnostic {
  category: DiagnosticCategory;
  items: DiagnosticItem[];
}

export interface DiagnosticItem {
  id: string;
  title: string;
  capability: string;
  source: string;
  evidence: string[];
  detail: string;
  provenance: {
    detector: string;
    timestamp: string;
    commit?: string;
    run_id?: string;
    status: string;
    decision: string;
    evidence_reference: string;
    diagnostic_reason: string;
  };
}

// ---------------------------------------------------------------------------
// Hook: Run deterministic diagnosis
// ---------------------------------------------------------------------------

export function useDiagnose() {
  return useMutation<DiagnosticResultEnvelope | null, Error, {
    symptom: string;
    error_code?: string;
    capability_id?: string;
  }>({
    mutationFn: async ({ symptom, error_code, capability_id }) => {
      const response = await apiFetch('/platform/v1/diagnose', {
        method: 'POST',
        body: JSON.stringify({ symptom, error_code, capability_id }),
      });
      if (!response.ok) {
        if (response.status === 404) return null;
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json() as Promise<DiagnosticResultEnvelope>;
    },
  });
}

// ---------------------------------------------------------------------------
// Hook: Register failure signature
// ---------------------------------------------------------------------------

export function useRegisterDiagnosticSignature() {
  return useMutation<DiagnosticRecommendationEnvelope, Error, {
    error_code: string;
    capability_id: string;
    description: string;
    severity?: string;
  }>({
    mutationFn: async ({ error_code, capability_id, description, severity = 'medium' }) => {
      const response = await apiFetch('/platform/v1/diagnose/register', {
        method: 'POST',
        body: JSON.stringify({ error_code, capability_id, description, severity }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json() as Promise<DiagnosticRecommendationEnvelope>;
    },
  });
}

// ---------------------------------------------------------------------------
// Hook: Load local failure signatures
// ---------------------------------------------------------------------------

export function useDiagnosticSignatures() {
  return useQuery<LocalSignatureStore, Error>({
    queryKey: ['platform', 'diagnostic-signatures'],
    queryFn: async () => {
      const response = await apiFetch('/platform/v1/diagnostics/signatures');
      if (!response.ok) {
        // Return empty store if file doesn't exist
        return { signatures: [], index: {} };
      }
      return response.json() as Promise<LocalSignatureStore>;
    },
    staleTime: 60_000,
  });
}

// ---------------------------------------------------------------------------
// Hook: Compute consolidated diagnostic categories
// ---------------------------------------------------------------------------

export function useConsolidatedDiagnostics() {
  const { data: healthData } = useQuery({
    queryKey: ['platform', 'health'],
    queryFn: () => apiFetchJson('/platform/v1/health') as Promise<{ data: any }>,
    staleTime: 60_000,
  });

  const { data: errorsData } = useQuery({
    queryKey: ['platform', 'errors', 'current'],
    queryFn: () => apiFetchJson('/platform/v1/errors/current') as Promise<{ data: { items: any[] } }>,
    staleTime: 60_000,
  });

  const { data: tasksData } = useQuery({
    queryKey: ['platform', 'tasks'],
    queryFn: () => apiFetchJson('/platform/v1/tasks') as Promise<{ data: { items: any[]; open_count: number } }>,
    staleTime: 60_000,
  });

  // Build consolidated diagnostic categories
  const categories = buildDiagnosticCategories(healthData, errorsData, tasksData);

  return {
    categories,
    isLoading: false,
    healthData,
    errorsData,
    tasksData,
  };
}

function buildDiagnosticCategories(
  healthData: any,
  errorsData: any,
  tasksData: any,
): CategoryDiagnostic[] {
  const items: DiagnosticItem[] = [];

  // FAILED: task → capability → source → test/evidence
  // From evidence integrity failures and open obligations
  if (errorsData?.data?.items) {
    for (const error of errorsData.data.items) {
      if (error.code === 'INTEGRITY_FAILED' || error.code === 'OBLIGATION_OPEN') {
        items.push({
          id: error.id,
          title: error.message,
          capability: error.affected_workflow ?? 'unknown',
          source: error.layer,
          evidence: [error.id],
          detail: `Code: ${error.code} · Occurrences: ${error.occurrences}`,
          provenance: {
            detector: error.layer === 'platform.evidence' ? 'EvidenceIntegrityReport' : 'ObligationSet',
            timestamp: error.first_seen,
            status: 'FAILED',
            decision: 'ACTIONABLE',
            evidence_reference: error.id,
            diagnostic_reason: 'Failed verification condition or open obligation disposition',
          },
        });
      }
    }
  }

  // BLOCKED: reason → timeout/dependency/environment/obligation → partial evidence
  // From tasks that are blocked (infrastructure, timeout, validation, authorization)
  if (tasksData?.data?.items) {
    for (const task of tasksData.data.items) {
      if (task.status === 'BLOCKED' || task.status === 'INFRASTRUCTURE_BLOCKED' ||
          task.status === 'TIMEOUT_BLOCKED' || task.status === 'VALIDATION_BLOCKED' ||
          task.status === 'AWAITING_AUTHORIZATION') {
        items.push({
          id: task.id,
          title: task.name,
          capability: task.capability_id,
          source: 'platform.tasks',
          evidence: task.evidence_ids ?? [],
          detail: `Status: ${task.status}`,
          provenance: {
            detector: 'ControlPlane',
            timestamp: task.created_at,
            run_id: task.id,
            status: 'BLOCKED',
            decision: 'ACTIONABLE',
            evidence_reference: task.evidence_ids?.join(', ') ?? 'none',
            diagnostic_reason: `Task blocked: ${task.status.replace(/_/g, ' ').toLowerCase()}`,
          },
        });
      }
    }
  }

  // INTERRUPTED: signal → run state → recovery status
  // From executions that were interrupted (SIGINT/SIGTERM)
  // This would come from history/runs with interrupted status
  // For now, we note this as a category that would be populated from history

  // STALE: artifact → identity mismatch/age/generator mismatch
  // From framework integrity artifact freshness findings
  if (healthData?.data?.domains) {
    const fiDomain = healthData.data.domains.find((d: any) => d.name === 'Framework Integrity');
    if (fiDomain && fiDomain.detail) {
      // Parse framework integrity detail for stale artifacts
      const staleMatch = fiDomain.detail.match(/stale|identity|generator/i);
      if (staleMatch) {
        items.push({
          id: 'stale-artifact',
          title: 'Stale or mismatched artifact detected',
          capability: 'framework',
          source: 'platform.framework',
          evidence: [],
          detail: fiDomain.detail,
          provenance: {
            detector: 'ArtifactFreshnessDetector',
            timestamp: fiDomain.last_check,
            status: 'STALE',
            decision: 'ACTIONABLE',
            evidence_reference: '/platform/v1/framework/integrity',
            diagnostic_reason: 'Artifact exceeds freshness threshold or has identity/generator mismatch',
          },
        });
      }
    }
  }

  // DIVERGED: authority/configuration/registry mismatch → specific detector
  // From framework integrity authority drift findings
  if (healthData?.data?.domains) {
    const fiDomain = healthData.data.domains.find((d: any) => d.name === 'Framework Integrity');
    if (fiDomain && fiDomain.detail) {
      const divergedMatch = fiDomain.detail.match(/drift|authority|config|bypass/i);
      if (divergedMatch) {
        items.push({
          id: 'diverged-authority',
          title: 'Authority or configuration drift detected',
          capability: 'framework',
          source: 'platform.framework',
          evidence: [],
          detail: fiDomain.detail,
          provenance: {
            detector: 'AuthorityDriftDetector',
            timestamp: fiDomain.last_check,
            status: 'DIVERGED',
            decision: 'ACTIONABLE',
            evidence_reference: '/platform/v1/framework/integrity',
            diagnostic_reason: 'Authority/configuration/registry mismatch detected by drift detectors',
          },
        });
      }
    }
  }

  // Group by category
  const categoryMap = new Map<DiagnosticCategory, DiagnosticItem[]>();
  for (const item of items) {
    const cat = item.provenance.status as DiagnosticCategory;
    if (!categoryMap.has(cat)) categoryMap.set(cat, []);
    categoryMap.get(cat)!.push(item);
  }

  const categoryOrder: DiagnosticCategory[] = ['FAILED', 'BLOCKED', 'INTERRUPTED', 'STALE', 'DIVERGED'];
  return categoryOrder
    .filter((cat) => categoryMap.has(cat) && categoryMap.get(cat)!.length > 0)
    .map((cat) => ({
      category: cat,
      items: categoryMap.get(cat)!,
    }));
}