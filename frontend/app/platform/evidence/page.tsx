/**
 * Platform Evidence Explorer — M9-C63 Phase H
 *
 * Surfaces canonical evidence from the Platform API.
 * Navigation: Verification → Execution → Evidence → Artifact → Source/capability/test
 *
 * Data sources:
 *   /platform/v1/evidence           → evidence list
 *   /platform/v1/evidence/{id}      → evidence detail
 *   /platform/v1/evidence/by-execution/{id} → evidence by execution
 *
 * No new evidence store — all from canonical authorities.
 */

'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetchJson } from '@/lib/api/gateway';
import {
  FileText,
  Clock,
  Activity,
  Filter,
  GitBranch,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface EvidenceItem {
  id: string;
  kind: string;
  capability_id: string;
  execution_id: string | null;
  collected_at: string;
  status: string;
  summary: string;
  payload?: Record<string, unknown>;
  references?: string[];
}

interface EvidenceListResponse {
  kind: string;
  data: { count: number; items: EvidenceItem[] };
}

interface EvidenceDetailResponse {
  kind: string;
  data: EvidenceItem & { payload: Record<string, unknown>; references: string[] };
}

const STATUS_COLORS: Record<string, string> = {
  CLOSED: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  OPEN: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  HEALTHY: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  UNHEALTHY: 'text-red-400 bg-red-500/10 border-red-500/30',
  UNKNOWN: 'text-gray-400 bg-gray-500/10 border-gray-500/30',
};

const KIND_LABELS: Record<string, string> = {
  verification: 'Verification',
  'VerificationCompleted': 'Completed',
  'VerificationFailed': 'Failed',
  'VerificationBlocked': 'Blocked',
};

export default function EvidenceExplorerPage() {
  const { data: listData, isLoading: listLoading } = useQuery<EvidenceListResponse, Error>({
    queryKey: ['platform', 'evidence'],
    queryFn: () => apiFetchJson('/platform/v1/evidence') as Promise<EvidenceListResponse>,
    staleTime: 60_000,
  });

  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: detailData, isLoading: detailLoading } = useQuery<EvidenceDetailResponse | null, Error>({
    queryKey: ['platform', 'evidence', selectedId],
    queryFn: async () => {
      if (!selectedId) return null;
      return apiFetchJson(`/platform/v1/evidence/${selectedId}`) as Promise<EvidenceDetailResponse>;
    },
    enabled: !!selectedId,
    staleTime: 60_000,
  });

  const items = listData?.data?.items ?? [];
  const filtered = filterStatus === 'all'
    ? items
    : items.filter((item) => item.status === filterStatus);

  return (
    <div className="flex flex-col gap-4 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
            <FileText className="h-5 w-5 text-violet-400" />
            Evidence Explorer
          </h1>
          <p className="text-xs text-[var(--text-tertiary)] mt-0.5">
            {items.length} evidence items · sourced from C50 obligations · no second store
          </p>
        </div>
        <div className="text-xs font-mono text-[var(--text-tertiary)]">
          UI → Platform API → ControlPlane → evidence
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 items-center">
        <Filter className="h-4 w-4 text-[var(--text-tertiary)]" />
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="text-sm rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] text-[var(--text-primary)] px-3 py-1.5 focus:outline-none"
        >
          <option value="all">All Status</option>
          <option value="CLOSED">CLOSED</option>
          <option value="OPEN">OPEN</option>
          <option value="HEALTHY">HEALTHY</option>
          <option value="UNHEALTHY">UNHEALTHY</option>
        </select>
        <span className="text-xs text-[var(--text-tertiary)] font-mono ml-2">
          {filtered.length} of {items.length}
        </span>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Evidence List */}
        <div className="flex flex-col gap-2">
          {listLoading ? (
            <div className="text-sm text-[var(--text-tertiary)] py-8">Loading evidence…</div>
          ) : filtered.length === 0 ? (
            <div className="text-sm text-[var(--text-tertiary)] py-8 text-center">
              No evidence items found
            </div>
          ) : (
            filtered.map((item) => (
              <button
                key={item.id}
                onClick={() => setSelectedId(item.id)}
                className={cn(
                  'text-left rounded-lg border p-3 transition-colors hover:bg-[var(--surface-raised)]',
                  selectedId === item.id
                    ? 'border-violet-500/50 bg-violet-500/5'
                    : 'border-[var(--border-subtle)]'
                )}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-mono text-[var(--text-primary)] truncate">
                    {item.id}
                  </span>
                  <span className={cn(
                    'text-xs font-mono px-2 py-0.5 rounded border',
                    STATUS_COLORS[item.status] ?? STATUS_COLORS.UNKNOWN
                  )}>
                    {item.status}
                  </span>
                </div>
                <div className="text-xs text-[var(--text-tertiary)] truncate">
                  {item.summary}
                </div>
                <div className="flex items-center gap-3 mt-1 text-xs text-[var(--text-tertiary)] font-mono">
                  <span>cap: {item.capability_id}</span>
                  {item.execution_id && (
                    <span>exec: {item.execution_id.slice(0, 24)}…</span>
                  )}
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {item.collected_at.slice(0, 19).replace('T', ' ')}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>

        {/* Evidence Detail */}
        <div className="flex flex-col gap-3">
          {!selectedId ? (
            <div className="flex flex-col items-center justify-center py-16 text-[var(--text-tertiary)]">
              <FileText className="h-12 w-12 opacity-30 mb-3" />
              <span className="text-sm">Select an evidence item to inspect</span>
              <span className="text-xs mt-1">Click any item from the list</span>
            </div>
          ) : detailLoading ? (
            <div className="text-sm text-[var(--text-tertiary)] py-8">Loading detail…</div>
          ) : detailData ? (
            <EvidenceDetailPanel detail={detailData.data} />
          ) : null}
        </div>
      </div>

      {/* Provenance Note */}
      <div className="border-t border-[var(--border-subtle)] pt-3 text-xs text-[var(--text-tertiary)]">
        All evidence originates from the canonical ControlPlane obligation set.
        No evidence is presented as current truth unless its status indicates current/active.
        Historical evidence items are distinguished by their collected_at timestamp.
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

function EvidenceDetailPanel({ detail }: { detail: EvidenceItem & { payload: Record<string, unknown>; references: string[] } }) {
  return (
    <div className="flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="text-base font-semibold text-[var(--text-primary)]">
            {detail.summary}
          </div>
          <div className="text-xs font-mono text-[var(--text-tertiary)] mt-1">
            {detail.id}
          </div>
        </div>
        <span className={cn(
          'text-xs font-mono px-3 py-1 rounded-full border shrink-0',
          STATUS_COLORS[detail.status] ?? STATUS_COLORS.UNKNOWN
        )}>
          {detail.status}
        </span>
      </div>

      {/* Metadata Grid */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <MetaField label="ID" value={detail.id} />
        <MetaField label="Kind" value={KIND_LABELS[detail.kind] ?? detail.kind} />
        <MetaField label="Capability" value={detail.capability_id} />
        <MetaField label="Execution" value={detail.execution_id ?? 'N/A'} />
        <MetaField label="Status" value={detail.status} />
        <MetaField
          label="Collected"
          value={detail.collected_at.slice(0, 19).replace('T', ' ')}
        />
      </div>

      {/* References */}
      {detail.references.length > 0 && (
        <div className="border border-[var(--border-subtle)] rounded-lg p-3">
          <div className="text-xs font-semibold text-[var(--text-secondary)] mb-2 flex items-center gap-1">
            <GitBranch className="h-3 w-3" /> References
          </div>
          <div className="flex flex-wrap gap-1">
            {detail.references.map((ref, i) => (
              <span key={i} className="text-xs font-mono px-2 py-0.5 bg-[var(--surface-base)] rounded border border-[var(--border-subtle)]">
                {ref}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Payload */}
      {detail.payload && Object.keys(detail.payload).length > 0 && (
        <div className="border border-[var(--border-subtle)] rounded-lg p-3">
          <div className="text-xs font-semibold text-[var(--text-secondary)] mb-2">Payload</div>
          <pre className="text-xs font-mono text-[var(--text-tertiary)] bg-[var(--surface-raised)] p-2 rounded overflow-auto">
            {JSON.stringify(detail.payload, null, 2)}
          </pre>
        </div>
      )}

      {/* Authoritative Evidence Note */}
      <div className="text-xs text-[var(--text-tertiary)] border-t border-[var(--border-subtle)] pt-2">
        <Activity className="h-3 w-3 inline mr-1" />
        Authoritative evidence from ControlPlane obligation set
      </div>
    </div>
  );
}

function MetaField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-[var(--text-tertiary)] text-xs">{label}</span>
      <div className="text-sm font-mono text-[var(--text-secondary)] truncate" title={value}>
        {value}
      </div>
    </div>
  );
}
