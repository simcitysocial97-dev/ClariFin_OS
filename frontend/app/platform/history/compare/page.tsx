/**
 * Platform History Comparison Page — M9-C57
 *
 * Shows delta between two runs: repository changes, test results,
 * duration, evidence invalidation, obligation changes, capability state.
 * Data source: POST /platform/v1/history/compare.
 */

'use client';

import { Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, GitCompareArrows, GitCommit, Calendar } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DeltaResponse {
  kind: string;
  data: {
    current_run: {
      id: string;
      started_at: string;
      finished_at: string | null;
      duration_ms: number | null;
      status: string;
      capabilities_run: number;
      capabilities_passed: number;
      capabilities_failed: number;
    };
    baseline_run: {
      id: string;
      started_at: string;
      finished_at: string | null;
      duration_ms: number | null;
      status: string;
      capabilities_run: number;
      capabilities_passed: number;
      capabilities_failed: number;
    };
    delta: {
      repository_changes: {
        changed: string[];
        removed: string[];
        common: string[];
      };
      test_changes: {
        passed_added: number;
        passed_removed: number;
        failed_added: number;
        failed_removed: number;
      };
      failures: number;
      recovered_failures: number;
      duration: {
        current_ms: number;
        baseline_ms: number;
        delta_ms: number;
      };
      evidence_invalidated: string[];
      new_obligations: string[];
      closed_obligations: string[];
      capability_state_changes: Array<{
        capability: string;
        from: string;
        to: string;
        evidence: string;
      }>;
    };
  };
}

// Client-side wrapper that uses search params — requires Suspense
function CompareContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const currentId = searchParams.get('current') ?? '';
  const baseline = searchParams.get('baseline') ?? 'LAST_PASS';

  const { data, isLoading, error } = useQuery<DeltaResponse, Error>({
    queryKey: ['platform', 'history', 'compare', currentId, baseline],
    queryFn: async () => {
      const resp = await fetch('/platform/v1/history/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_run_id: currentId, baseline }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return resp.json() as Promise<DeltaResponse>;
    },
    enabled: !!currentId,
    staleTime: 60_000,
  });

  const d = data?.data;

  return (
    <div className="flex flex-col gap-4 max-w-5xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.push('/platform/history')}
          className="text-xs text-[var(--text-tertiary)] underline hover:text-[var(--text-secondary)]"
        >
          ← History
        </button>
        <h1 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
          <GitCompareArrows className="h-5 w-5 text-violet-400" />
          Run Comparison
        </h1>
      </div>

      {isLoading && (
        <div className="text-sm text-[var(--text-tertiary)] py-8 flex items-center gap-2">
          Computing delta…
        </div>
      )}

      {error && (
        <div className="text-sm text-red-400 py-8">
          Compare error: {error.message}
        </div>
      )}

      {d && (
        <>
          {/* Two-run header */}
          <RunComparisonHeader current={d.current_run} baseline={d.baseline_run} />

          {/* Delta dimensions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TestChangesPanel delta={d.delta} />
            <DurationPanel delta={d.delta} />
            <RepoChangesPanel delta={d.delta} />
            <ObligationsPanel delta={d.delta} />
            <EvidencePanel delta={d.delta} />
            <CapabilityChangesPanel delta={d.delta} />
          </div>
        </>
      )}
    </div>
  );
}

export default function HistoryComparePage() {
  return (
    <Suspense fallback={
      <div className="flex items-center gap-2 text-sm text-[var(--text-tertiary)] py-12">
        Loading comparison…
      </div>
    }>
      <CompareContent />
    </Suspense>
  );
}

// ---------------------------------------------------------------------------

function RunComparisonHeader({
  current,
  baseline,
}: {
  current: DeltaResponse['data']['current_run'];
  baseline: DeltaResponse['data']['baseline_run'];
}) {
  const curOk = current.status === 'HEALTHY' || current.status === 'CLOSED';
  const baseOk = baseline.status === 'HEALTHY' || baseline.status === 'CLOSED';

  return (
    <div className="flex items-center gap-4 p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)]">
      <RunMiniRun label="CURRENT" run={current} ok={curOk} />
      <ArrowRight className="h-5 w-5 text-[var(--text-tertiary)] shrink-0" />
      <RunMiniRun label={baseline.id === current.id ? 'SAME (LAST)' : 'BASELINE'} run={baseline} ok={baseOk} />
    </div>
  );
}

function RunMiniRun({
  label,
  run,
  ok,
}: {
  label: string;
  run: { id: string; started_at: string; duration_ms: number | null; status: string; capabilities_passed: number; capabilities_failed: number; capabilities_run: number };
  ok: boolean;
}) {
  return (
    <div className="flex-1">
      <div className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider mb-1">{label}</div>
      <div className="flex items-center gap-2">
        <span className={cn(
          'text-xs font-mono px-2 py-0.5 rounded',
          ok ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400',
        )}>
          {run.status}
        </span>
        <span className="text-xs font-mono text-[var(--text-tertiary)] truncate" title={run.id}>{run.id.slice(0, 16)}…</span>
      </div>
      <div className="text-xs text-[var(--text-tertiary)] mt-1 font-mono">
        {run.capabilities_passed}/{run.capabilities_run} passed
        {run.capabilities_failed > 0 && <span className="text-red-400"> · {run.capabilities_failed} failed</span>}
      </div>
      {run.duration_ms && (
        <div className="text-xs text-[var(--text-tertiary)] font-mono">
          <Calendar className="h-3 w-3 inline mr-1" />
          {(run.duration_ms / 1000).toFixed(1)}s
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

function TestChangesPanel({ delta }: { delta: DeltaResponse['data']['delta'] }) {
  const tc = delta.test_changes;
  const netChange = (tc.passed_added - tc.passed_removed) + (tc.failed_removed - tc.failed_added);

  return (
    <DeltaCard title="Test Changes" icon={<GitCommit className="h-4 w-4 text-blue-400" />}>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <MetricTile label="Passed added" value={tc.passed_added} accent="positive" />
        <MetricTile label="Passed removed" value={tc.passed_removed} accent="negative" />
        <MetricTile label="Failed added" value={tc.failed_added} accent="negative" />
        <MetricTile label="Failed removed" value={tc.failed_removed} accent="positive" />
      </div>
      <div className={cn(
        'mt-2 text-xs font-mono',
        netChange > 0 ? 'text-emerald-400' : netChange < 0 ? 'text-red-400' : 'text-[var(--text-tertiary)]',
      )}>
        Net: {netChange > 0 ? '+' : ''}{netChange}
      </div>
    </DeltaCard>
  );
}

function DurationPanel({ delta }: { delta: DeltaResponse['data']['delta'] }) {
  const dur = delta.duration;
  return (
    <DeltaCard title="Duration" icon={<Calendar className="h-4 w-4 text-amber-400" />}>
      <div className="grid grid-cols-3 gap-3 text-sm">
        <div>
          <div className="text-[var(--text-tertiary)] text-xs">Current</div>
          <div className="font-mono text-[var(--text-primary)]">{dur.current_ms ? `${(dur.current_ms / 1000).toFixed(1)}s` : '—'}</div>
        </div>
        <div>
          <div className="text-[var(--text-tertiary)] text-xs">Baseline</div>
          <div className="font-mono text-[var(--text-primary)]">{dur.baseline_ms ? `${(dur.baseline_ms / 1000).toFixed(1)}s` : '—'}</div>
        </div>
        <div>
          <div className="text-[var(--text-tertiary)] text-xs">Delta</div>
          <div className={cn('font-mono', dur.delta_ms > 0 ? 'text-red-400' : dur.delta_ms < 0 ? 'text-emerald-400' : 'text-[var(--text-tertiary)]')}>
            {dur.delta_ms > 0 ? '+' : ''}{dur.delta_ms ? `${(dur.delta_ms / 1000).toFixed(1)}s` : '—'}
          </div>
        </div>
      </div>
    </DeltaCard>
  );
}

function RepoChangesPanel({ delta }: { delta: DeltaResponse['data']['delta'] }) {
  const rc = delta.repository_changes;
  return (
    <DeltaCard title="Repository Changes" icon={<GitCommit className="h-4 w-4 text-violet-400" />}>
      <div className="flex flex-col gap-2 text-sm">
        {rc.changed.length > 0 && (
          <div>
            <span className="text-[var(--text-tertiary)] text-xs">Changed since baseline: {rc.changed.length}</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {rc.changed.slice(0, 5).map((f) => (
                <span key={f} className="text-xs font-mono px-2 py-0.5 rounded bg-violet-500/20 text-violet-300">{f}</span>
              ))}
              {rc.changed.length > 5 && (
                <span className="text-xs text-[var(--text-tertiary)]">+{rc.changed.length - 5} more</span>
              )}
            </div>
          </div>
        )}
        {rc.removed.length > 0 && (
          <div>
            <span className="text-[var(--text-tertiary)] text-xs">Removed: {rc.removed.length}</span>
          </div>
        )}
        {rc.changed.length === 0 && rc.removed.length === 0 && (
          <span className="text-xs text-[var(--text-tertiary)] italic">No repository changes detected</span>
        )}
      </div>
    </DeltaCard>
  );
}

function ObligationsPanel({ delta }: { delta: DeltaResponse['data']['delta'] }) {
  return (
    <DeltaCard title="Obligations" icon={<GitCompareArrows className="h-4 w-4 text-emerald-400" />}>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <MetricTile label="New obligations" value={delta.new_obligations.length} accent={delta.new_obligations.length > 0 ? 'warning' : 'positive'} />
        <MetricTile label="Closed obligations" value={delta.closed_obligations.length} accent="positive" />
      </div>
      {delta.new_obligations.length > 0 && (
        <div className="mt-2">
          <span className="text-xs text-[var(--text-tertiary)]">New:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {delta.new_obligations.slice(0, 3).map((id) => (
              <span key={id} className="text-xs font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300">{id}</span>
            ))}
          </div>
        </div>
      )}
    </DeltaCard>
  );
}

function EvidencePanel({ delta }: { delta: DeltaResponse['data']['delta'] }) {
  return (
    <DeltaCard title="Evidence Invalidation" icon={<GitCompareArrows className="h-4 w-4 text-red-400" />}>
      {delta.evidence_invalidated.length > 0 ? (
        <div>
          <span className="text-sm text-red-400 font-mono">{delta.evidence_invalidated.length} evidence item(s) invalidated</span>
          <div className="flex flex-wrap gap-1 mt-2">
            {delta.evidence_invalidated.slice(0, 5).map((id) => (
              <span key={id} className="text-xs font-mono px-2 py-0.5 rounded bg-red-500/20 text-red-300">{id}</span>
            ))}
          </div>
        </div>
      ) : (
        <span className="text-sm text-emerald-400">All evidence preserved across runs</span>
      )}
    </DeltaCard>
  );
}

function CapabilityChangesPanel({ delta }: { delta: DeltaResponse['data']['delta'] }) {
  const changes = delta.capability_state_changes;
  return (
    <DeltaCard title="Capability State Changes" icon={<GitCompareArrows className="h-4 w-4 text-blue-400" />}>
      {changes.length > 0 ? (
        <div className="flex flex-col gap-2">
          {changes.map((c, idx) => (
            <div key={idx} className="flex items-center gap-3 text-sm">
              <span className="font-mono text-xs text-[var(--text-secondary)] w-40 truncate">{c.capability}</span>
              <span className="text-[var(--text-tertiary)] text-xs">{c.from}</span>
              <ArrowRight className="h-3 w-3 text-[var(--text-tertiary)]" />
              <span className={cn(
                'text-xs px-2 py-0.5 rounded font-mono',
                c.to === 'HEALTHY' || c.to === 'CLOSED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400',
              )}>{c.to}</span>
            </div>
          ))}
        </div>
      ) : (
        <span className="text-sm text-[var(--text-tertiary)]">No capability state changes detected</span>
      )}
    </DeltaCard>
  );
}

// ---------------------------------------------------------------------------

function DeltaCard({
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
      {children}
    </div>
  );
}

function MetricTile({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: 'positive' | 'warning' | 'negative';
}) {
  const color =
    accent === 'positive' ? 'text-emerald-400' :
    accent === 'warning' ? 'text-amber-400' : 'text-red-400';
  return (
    <div>
      <div className="text-[var(--text-tertiary)] text-xs">{label}</div>
      <div className={cn('font-mono text-xl font-bold', color)}>{value}</div>
    </div>
  );
}
