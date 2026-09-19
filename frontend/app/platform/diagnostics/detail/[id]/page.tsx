/**
 * Diagnostic Detail Page — M9-C63 Phase G
 *
 * Shows detailed failure signature and evidence chain for a single
 * diagnostic finding. Routes:
 *   /platform/diagnostics/detail/:id
 *
 * Data sources:
 * - GET /platform/v1/diagnose (deterministic engine)
 * - GET /platform/v1/errors/* (error details)
 * - GET /platform/v1/tasks/:id (task/obligation details)
 * - GET /platform/v1/history/runs/:id (execution history)
 * - runtime/generated/diagnostic-signatures.json (signatures)
 */

'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Bug,
  FileText,
  Activity,
  ShieldCheck,
  Clock,
  AlertTriangle,
  ExternalLink,
  Search,
} from 'lucide-react';

interface DiagnosticDetail {
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
  signature?: {
    id: string;
    error_code: string;
    description: string;
    affected_capability: string;
    severity: string;
    occurrences: number;
    first_seen: string;
    last_seen: string;
    linked_execution?: string;
    linked_evidence?: string;
    linked_change?: string;
    recommended_verification: string[];
  };
}

export default function DiagnosticDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [detail, setDetail] = useState<DiagnosticDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDiagnosticDetail(id)
      .then((data) => {
        if (data) {
          setDetail(data);
        } else {
          setError('Diagnostic finding not found');
        }
      })
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex flex-col gap-4 max-w-4xl">
        <div className="text-sm text-[var(--text-tertiary)] py-8 flex items-center gap-2">
          <Activity className="h-4 w-4 animate-spin" />
          Loading diagnostic detail…
        </div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="flex flex-col gap-4 max-w-4xl">
        <div className="text-sm text-red-400 py-8">{error ?? 'Not found'}</div>
        <Link href="/platform/diagnostics" className="text-xs text-violet-400 hover:underline">
          ← Back to Diagnostics
        </Link>
      </div>
    );
  }

  const sevColor =
    detail.provenance.status === 'FAILED' ? 'text-red-400 bg-red-500/10 border-red-500/30' :
    detail.provenance.status === 'BLOCKED' ? 'text-amber-400 bg-amber-500/10 border-amber-500/30' :
    detail.provenance.status === 'INTERRUPTED' ? 'text-gray-400 bg-gray-500/10 border-gray-500/30' :
    detail.provenance.status === 'STALE' ? 'text-orange-400 bg-orange-500/10 border-orange-500/30' :
    detail.provenance.status === 'DIVERGED' ? 'text-purple-400 bg-purple-500/10 border-purple-500/30' :
    'text-gray-400 bg-gray-500/10 border-gray-500/30';

  return (
    <div className="flex flex-col gap-4 max-w-4xl">
      {/* Back link */}
      <Link href="/platform/diagnostics" className="text-xs text-[var(--text-tertiary)] underline hover:text-[var(--text-secondary)] w-fit">
        ← Diagnostics
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
            <Bug className="h-5 w-5 text-red-400" />
            Diagnostic Detail
          </h1>
          <div className="text-xs font-mono text-[var(--text-tertiary)] mt-1">{detail.id}</div>
        </div>
        <span className={`text-xs font-bold font-mono px-3 py-1 rounded-full border ${sevColor}`}>
          {detail.provenance.status}
        </span>
      </div>

      {/* Title & Detail */}
      <div className="border border-[var(--border-subtle)] rounded-lg p-4">
        <div className="text-base font-semibold text-[var(--text-primary)]">{detail.title}</div>
        <div className="text-sm text-[var(--text-secondary)] mt-1 font-mono">{detail.detail}</div>
      </div>

      {/* Metadata grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <MetaTile label="Capability" value={detail.capability} icon={<FileText className="h-3 w-3" />} />
        <MetaTile label="Source" value={detail.source} icon={<Activity className="h-3 w-3" />} />
        <MetaTile label="Decision" value={detail.provenance.decision} icon={<ShieldCheck className="h-3 w-3" />} />
        <MetaTile label="Detector" value={detail.provenance.detector} icon={<Search className="h-3 w-3" />} />
        <MetaTile label="Timestamp" value={detail.provenance.timestamp} icon={<Clock className="h-3 w-3" />} />
        <MetaTile label="Diagnostic Reason" value={detail.provenance.diagnostic_reason} icon={<Bug className="h-3 w-3" />} />
      </div>

      {/* Evidence Chain */}
      <div className="border border-[var(--border-subtle)] rounded-lg p-4">
        <div className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2 mb-3">
          <Activity className="h-4 w-4 text-violet-400" />
          Evidence Chain
        </div>
        {detail.evidence.length > 0 ? (
          <div className="flex flex-col gap-2">
            {detail.evidence.map((e, i) => (
              <div key={i} className="flex items-center gap-2 text-xs font-mono">
                <span className="text-[var(--text-tertiary)]">{i + 1}.</span>
                <span className="text-[var(--text-secondary)] px-2 py-1 bg-[var(--surface-base)] rounded border border-[var(--border-subtle)]">{e}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-xs text-[var(--text-tertiary)] italic">No evidence available</div>
        )}
      </div>

      {/* Signature (if available) */}
      {detail.signature && (
        <div className="border border-[var(--border-subtle)] rounded-lg p-4">
          <div className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2 mb-3">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            Failure Signature
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="flex flex-col gap-1">
              <span className="text-[var(--text-tertiary)]">Signature ID</span>
              <span className="font-mono text-[var(--text-secondary)]">{detail.signature.id}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[var(--text-tertiary)]">Error Code</span>
              <span className="font-mono text-[var(--text-secondary)]">{detail.signature.error_code}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[var(--text-tertiary)]">Severity</span>
              <span className="font-mono text-[var(--text-secondary)]">{detail.signature.severity}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[var(--text-tertiary)]">Occurrences</span>
              <span className="font-mono text-[var(--text-secondary)]">{detail.signature.occurrences}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[var(--text-tertiary)]">First Seen</span>
              <span className="font-mono text-[var(--text-secondary)]">{detail.signature.first_seen}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[var(--text-tertiary)]">Last Seen</span>
              <span className="font-mono text-[var(--text-secondary)]">{detail.signature.last_seen}</span>
            </div>
            {detail.signature.linked_execution && (
              <div className="flex flex-col gap-1">
                <span className="text-[var(--text-tertiary)]">Linked Execution</span>
                <span className="font-mono text-[var(--text-secondary)]">{detail.signature.linked_execution}</span>
              </div>
            )}
            {detail.signature.linked_evidence && (
              <div className="flex flex-col gap-1">
                <span className="text-[var(--text-tertiary)]">Linked Evidence</span>
                <span className="font-mono text-[var(--text-secondary)]">{detail.signature.linked_evidence}</span>
              </div>
            )}
            {detail.signature.linked_change && (
              <div className="flex flex-col gap-1">
                <span className="text-[var(--text-tertiary)]">Linked Change</span>
                <span className="font-mono text-[var(--text-secondary)]">{detail.signature.linked_change}</span>
              </div>
            )}
            <div className="col-span-2 flex flex-col gap-1">
              <span className="text-[var(--text-tertiary)]">Description</span>
              <span className="text-[var(--text-secondary)]">{detail.signature.description}</span>
            </div>
            {detail.signature.recommended_verification.length > 0 && (
              <div className="col-span-2 flex flex-col gap-1">
                <span className="text-[var(--text-tertiary)]">Recommended Verification</span>
                <div className="flex flex-wrap gap-1">
                  {detail.signature.recommended_verification.map((v, i) => (
                    <Link
                      key={i}
                      href={`/platform/verification/run/${encodeURIComponent(v)}`}
                      className="text-xs font-mono px-2 py-0.5 bg-violet-500/10 text-violet-300 border border-violet-500/30 rounded hover:bg-violet-500/20 transition-colors"
                    >
                      {v}
                      <ExternalLink className="inline h-2.5 w-2.5 ml-1" />
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Provenance summary */}
      <div className="border border-[var(--border-subtle)] rounded-lg p-4">
        <div className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2 mb-3">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          Provenance Summary
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <ProvenanceField label="Detector" value={detail.provenance.detector} />
          <ProvenanceField label="Decision" value={detail.provenance.decision} />
          <ProvenanceField label="Status" value={detail.provenance.status} />
          <ProvenanceField label="Evidence Reference" value={detail.provenance.evidence_reference} />
          {detail.provenance.commit && (
            <ProvenanceField label="Commit" value={detail.provenance.commit} />
          )}
          {detail.provenance.run_id && (
            <ProvenanceField label="Run ID" value={detail.provenance.run_id} />
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helper components
// ---------------------------------------------------------------------------

function MetaTile({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="border border-[var(--border-subtle)] rounded-lg p-3 flex flex-col gap-1">
      <div className="flex items-center gap-1 text-[var(--text-tertiary)] text-xs">
        {icon}
        <span>{label}</span>
      </div>
      <div className="text-sm font-mono text-[var(--text-secondary)] truncate" title={value}>
        {value}
      </div>
    </div>
  );
}

function ProvenanceField({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[var(--text-tertiary)] text-xs">{label}</span>
      <span className="font-mono text-[var(--text-secondary)] break-all">{value}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Mock detail fetcher (uses local data + API lookups)
// ---------------------------------------------------------------------------

async function fetchDiagnosticDetail(id: string): Promise<DiagnosticDetail | null> {
  // Try to load from local diagnostic signatures store
  try {
    const response = await fetch('/api/diagnostic-signatures');
    if (response.ok) {
      const store = await response.json();
      const sig = store.signatures?.find((s: any) => s.id === id);
      if (sig) {
        return {
          id: sig.id,
          title: sig.description,
          capability: sig.affected_capability,
          source: 'diagnostic-signatures',
          evidence: [sig.id],
          detail: `Error Code: ${sig.error_code} · Severity: ${sig.severity} · Occurrences: ${sig.occurrences}`,
          provenance: {
            detector: 'DiagnosticEngine',
            timestamp: sig.first_seen,
            status: 'FAILED',
            decision: 'ACTIONABLE',
            evidence_reference: sig.id,
            diagnostic_reason: `Failure signature ${sig.id} matched — ${sig.error_code} on ${sig.affected_capability}`,
          },
          signature: {
            ...sig,
            recommended_verification: ['execute.contract.api'],
          },
        };
      }
    }
  } catch {
    // Fall through to API lookups
  }

  // Try errors API
  try {
    const response = await fetch('/platform/v1/errors/current');
    if (response.ok) {
      const data = await response.json();
      const error = data.data?.items?.find((e: any) => e.id === id);
      if (error) {
        return {
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
        };
      }
    }
  } catch {
    // Fall through
  }

  // Try tasks API
  try {
    const response = await fetch('/platform/v1/tasks');
    if (response.ok) {
      const data = await response.json();
      const task = data.data?.items?.find((t: any) => t.id === id);
      if (task) {
        return {
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
            status: (task.status as string).toUpperCase().includes('BLOCK') ? 'BLOCKED' : 'FAILED',
            decision: 'ACTIONABLE',
            evidence_reference: task.evidence_ids?.join(', ') ?? 'none',
            diagnostic_reason: `Task status: ${task.status}`,
          },
        };
      }
    }
  } catch {
    // Not found
  }

  return null;
}