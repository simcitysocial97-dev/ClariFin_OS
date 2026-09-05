/**
 * Platform Capability Detail Page — M9-C57 Phase 9C
 *
 * Shows owner, runtime, API, frontend deps, tests, verification state,
 * evidence, recent failures, and dependency graph for one capability.
 * Data source: /platform/v1/capabilities/{id} + /graph.
 */

'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useCapabilityDetail, useCapabilityGraph } from '@/lib/hooks/use-platform-capabilities';
import { HealthBadge } from '@/components/platform/health-badge';
import {
  ArrowLeft,
  GitBranch,
  Package,
  TestTube,
  Shield,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function CapabilityDetailPage() {
  const params = useParams<{ capabilityId: string }>();
  const capabilityId = decodeURIComponent(String(params?.capabilityId ?? ''));

  const { data, isLoading } = useCapabilityDetail(capabilityId);
  const { data: graphData } = useCapabilityGraph(capabilityId);

  const cap = data?.data;

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-[var(--text-tertiary)] py-12">
        <RefreshCw className="h-4 w-4 animate-spin" />
        Loading capability…
      </div>
    );
  }

  if (!cap) {
    return (
      <div className="flex flex-col gap-4 max-w-2xl">
        <Link href="/platform/capabilities" className="text-xs text-[var(--text-tertiary)] underline flex items-center gap-1">
          <ArrowLeft className="h-3 w-3" /> Back to Capabilities
        </Link>
        <div className="py-12 text-center text-[var(--text-tertiary)]">
          Capability not found: <code className="font-mono text-sm">{capabilityId}</code>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 max-w-4xl">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link href="/platform/capabilities" className="text-xs text-[var(--text-tertiary)] underline self-center">
          ← Back
        </Link>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-[var(--text-primary)] font-mono">{cap.id}</h1>
            <HealthBadge status={cap.health} size="sm" />
          </div>
          <p className="text-sm text-[var(--text-tertiary)] mt-0.5">{cap.name}</p>
        </div>
        <span className={cn(
          'text-xs font-mono px-2 py-1 rounded-full shrink-0',
          cap.cost === 'P0' ? 'bg-emerald-500/20 text-emerald-400' :
          cap.cost === 'P1' ? 'bg-amber-500/20 text-amber-400' :
          'bg-blue-500/20 text-blue-400',
        )}>
          {cap.cost} · {cap.authorization}
        </span>
      </div>

      {/* Detail grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <DetailSection title="Identity" icon={<Package className="h-4 w-4 text-blue-400" />}>
          <DetailRow label="Stage" value={cap.stage} />
          <DetailRow label="Owner" value={cap.owner} />
          <DetailRow label="Command" value={cap.command} monospace />
        </DetailSection>

        <DetailSection title="Dependencies" icon={<GitBranch className="h-4 w-4 text-violet-400" />}>
          <MetaList label="Upstream (consumes)" items={cap.dependencies} empty="None" />
          {!!graphData && graphData.data.upstream.length > 0 && (
            <div className="mt-2">
              <span className="text-xs text-[var(--text-tertiary)]">Producers:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {graphData.data.upstream.map((id) => (
                  <span key={id} className="text-xs font-mono px-2 py-0.5 rounded bg-[var(--surface-raised)] text-[var(--text-secondary)]">
                    {id}
                  </span>
                ))}
              </div>
            </div>
          )}
          {!!graphData && graphData.data.downstream.length > 0 && (
            <div className="mt-2">
              <span className="text-xs text-[var(--text-tertiary)]">Consumers:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {graphData.data.downstream.map((id) => (
                  <span key={id} className="text-xs font-mono px-2 py-0.5 rounded bg-[var(--surface-raised)] text-[var(--text-secondary)]">
                    {id}
                  </span>
                ))}
              </div>
            </div>
          )}
        </DetailSection>

        <DetailSection title="Outputs & Triggers" icon={<Shield className="h-4 w-4 text-emerald-400" />}>
          <MetaList label="Produces" items={cap.produces} empty="—" />
          <MetaList label="Triggers" items={cap.triggers} empty="—" />
        </DetailSection>

        <DetailSection title="Verification State" icon={<TestTube className="h-4 w-4 text-amber-400" />}>
          <DetailRow label="Cache" value={cap.cache_status ?? '—'} />
          <DetailRow label="Evidence IDs" value={cap.evidence.length > 0 ? cap.evidence.slice(0, 3).join(', ') + (cap.evidence.length > 3 ? ` +${cap.evidence.length - 3}` : '') : '—'} monospace={false} />
          <DetailRow label="Recent failures" value={cap.failure_history.length > 0 ? `${cap.failure_history.length} recorded` : 'None'} />
        </DetailSection>
      </div>

      {/* Navigation links */}
      <div className="flex gap-2 flex-wrap mt-2">
        <Link
          href={`/platform/verification/run/${encodeURIComponent(cap.id)}`}
          className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] hover:border-[var(--border-default)] hover:bg-[var(--surface-raised)] transition-colors flex items-center gap-1"
        >
          <TestTube className="h-3 w-3" /> Run Verification
        </Link>
        <Link
          href={`/platform/errors`}
          className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] hover:border-[var(--border-default)] hover:bg-[var(--surface-raised)] transition-colors flex items-center gap-1"
        >
          View Errors
        </Link>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

function DetailSection({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] p-4 flex flex-col gap-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)]">
        {icon}
        {title}
      </div>
      <div className="flex flex-col gap-2">
        {children}
      </div>
    </div>
  );
}

function DetailRow({
  label,
  value,
  monospace = false,
}: {
  label: string;
  value: string | null | undefined;
  monospace?: boolean;
}) {
  return (
    <div className="flex items-start gap-3 text-sm">
      <span className="text-[var(--text-tertiary)] w-28 shrink-0">{label}:</span>
      <span className={cn(
        'text-[var(--text-primary)] break-all',
        monospace && 'font-mono text-xs',
      )}>
        {value ?? '—'}
      </span>
    </div>
  );
}

function MetaList({
  label,
  items,
  empty,
}: {
  label: string;
  items: string[];
  empty: string;
}) {
  if (items.length === 0) {
    return (
      <div className="text-sm text-[var(--text-tertiary)]">
        <span className="text-[var(--text-tertiary)]">{label}: </span>{empty}
      </div>
    );
  }
  return (
    <div>
      <div className="text-xs text-[var(--text-tertiary)] mb-1">{label} ({items.length})</div>
      <div className="flex flex-wrap gap-1">
        {items.map((item) => (
          <span key={item} className="text-xs font-mono px-2 py-0.5 rounded bg-[var(--surface-raised)] text-[var(--text-secondary)]">
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
