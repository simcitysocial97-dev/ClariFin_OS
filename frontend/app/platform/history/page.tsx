/**
 * Platform History Page — M9-C57
 *
 * Historical verification runs from /platform/v1/history/runs and baselines.
 * Supports compare actions: vs Last Run, Last Pass, Known Good, Baseline.
 * Data source: /platform/v1/history/*.
 */

'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { apiFetchJson } from '@/lib/api/gateway';
import { HealthBadge } from '@/components/platform/health-badge';
import {
  Clock,
  History,
  GitCompareArrows,
  CheckCircle2,
  XCircle,
  Loader2,
  CalendarDays,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface RunItem {
  id: string;
  started_at: string;
  finished_at: string | null;
  duration_ms: number | null;
  status: string;
  capabilities_run: number;
  capabilities_passed: number;
  capabilities_failed: number;
  environment: string;
  intent: string;
}

interface HistoryResponse {
  kind: string;
  data: { items: RunItem[] };
}

interface BaselineResponse {
  kind: string;
  data: { items: { id: string; label: string; run_id: string }[] };
}

export default function HistoryPage() {
  const router = useRouter();

  const { data: historyData, isLoading: historyLoading } = useQuery<HistoryResponse, Error>({
    queryKey: ['platform', 'history', 'runs'],
    queryFn: () => apiFetchJson('/platform/v1/history/runs') as Promise<HistoryResponse>,
    staleTime: 60_000,
  });

  const { data: baselineData } = useQuery<BaselineResponse, Error>({
    queryKey: ['platform', 'history', 'baselines'],
    queryFn: () => apiFetchJson('/platform/v1/history/baselines') as Promise<BaselineResponse>,
    staleTime: 120_000,
  });

  const runs = historyData?.data?.items ?? [];
  const baselines = baselineData?.data?.items ?? [];

  // Build compare buttons
  const compareOptions = [
    { label: 'vs Last Run', baseline: 'LAST' },
    { label: 'vs Last Pass', baseline: 'LAST_PASS' },
    { label: 'vs Known Good', baseline: 'KNOWN_GOOD' },
    { label: 'vs Baseline', baseline: 'BASELINE' },
  ];

  const handleCompare = (runId: string, baseline: string) => {
    router.push(`/platform/history/compare?current=${encodeURIComponent(runId)}&baseline=${baseline}`);
  };

  return (
    <div className="flex flex-col gap-4 max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
            <History className="h-5 w-5 text-blue-400" />
            Run History
          </h1>
          <p className="text-xs text-[var(--text-tertiary)] mt-0.5">
            {runs.length} historical runs · verified against C50 evidence store
          </p>
        </div>
      </div>

      {/* Compare banner */}
      {runs.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <GitCompareArrows className="h-4 w-4 text-violet-400" />
          <span className="text-xs text-[var(--text-tertiary)]">Compare current run:</span>
          {compareOptions.map((opt) => (
            <button
              key={opt.baseline}
              onClick={() => runs[0] && handleCompare(runs[0].id, opt.baseline)}
              disabled={!runs[0]}
              className="text-xs px-3 py-1 rounded-full border border-[var(--border-subtle)] hover:border-[var(--border-default)] hover:bg-[var(--surface-raised)] transition-colors disabled:opacity-40"
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}

      {/* Runs list */}
      {historyLoading ? (
        <div className="flex items-center gap-2 text-sm text-[var(--text-tertiary)] py-8">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading history…
        </div>
      ) : runs.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="flex flex-col gap-2">
          {runs.map((run) => (
            <RunCard
              key={run.id}
              run={run}
              onInspect={() => router.push(`/platform/verification/history/${run.id}`)}
              onCompare={(baseline) => handleCompare(run.id, baseline)}
            />
          ))}
        </div>
      )}

      {/* Baselines reference */}
      {baselines.length > 0 && (
        <div className="border-t border-[var(--border-subtle)] pt-3 mt-2">
          <div className="text-xs font-semibold text-[var(--text-secondary)] mb-2 flex items-center gap-1">
            <CalendarDays className="h-3 w-3" /> Reference Baselines
          </div>
          <div className="flex flex-wrap gap-2">
            {baselines.map((b) => (
              <span
                key={b.id}
                className="text-xs font-mono px-2 py-1 rounded bg-[var(--surface-raised)] text-[var(--text-tertiary)]"
                title={b.run_id}
              >
                {b.label}: {b.run_id}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

function RunCard({
  run,
  onInspect,
  onCompare,
}: {
  run: RunItem;
  onInspect: () => void;
  onCompare: (baseline: string) => void;
}) {
  const passed = run.capabilities_passed;
  const failed = run.capabilities_failed;
  const total = run.capabilities_run;
  const isSuccess = run.status === 'HEALTHY' || run.status === 'CLOSED';

  return (
    <div className={cn(
      'flex items-center gap-4 px-4 py-3 rounded-lg border transition-colors hover:bg-[var(--surface-raised)]',
      isSuccess ? 'border-emerald-500/20' : 'border-red-500/20',
    )}>
      <HealthBadge status={run.status} size="sm" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-mono text-[var(--text-primary)] truncate">{run.id}</span>
          <span className="text-xs text-[var(--text-tertiary)] font-mono">{run.environment}</span>
        </div>
        <div className="flex items-center gap-3 mt-0.5">
          <span className="text-xs text-[var(--text-tertiary)] flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {run.started_at}
          </span>
          {run.duration_ms && (
            <span className="text-xs font-mono text-[var(--text-tertiary)]">
              {(run.duration_ms / 1000).toFixed(1)}s
            </span>
          )}
        </div>
      </div>

      {/* Results */}
      <div className="flex items-center gap-3 shrink-0">
        <div className="text-right">
          <div className="flex items-center gap-1 text-sm">
            {isSuccess ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            ) : (
              <XCircle className="h-4 w-4 text-red-400" />
            )}
            <span className={cn(
              'font-mono font-semibold',
              isSuccess ? 'text-emerald-400' : 'text-red-400',
            )}>
              {passed}/{total}
            </span>
          </div>
          {failed > 0 && (
            <div className="text-xs text-red-400 font-mono">{failed} failed</div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={onInspect}
          className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] hover:border-[var(--border-default)] hover:bg-[var(--surface-raised)] transition-colors"
        >
          Inspect
        </button>
        <button
          onClick={() => onCompare('LAST_PASS')}
          className="text-xs px-2 py-1.5 rounded-lg border border-[var(--border-subtle)] text-[var(--text-tertiary)] hover:border-[var(--border-default)] hover:text-[var(--text-primary)] transition-colors"
          title="Compare vs last pass"
        >
          ↕
        </button>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center gap-2 py-16 text-[var(--text-tertiary)]">
      <Clock className="h-8 w-8 opacity-40" />
      <span className="text-sm">No verification history yet</span>
      <span className="text-xs">Runs will appear here after execution</span>
      <Link
        href="/platform/verification"
        className="mt-3 text-xs px-4 py-2 rounded-lg border border-[var(--border-subtle)] hover:border-[var(--border-default)] hover:bg-[var(--surface-raised)] transition-colors"
      >
        Run verification →
      </Link>
    </div>
  );
}
