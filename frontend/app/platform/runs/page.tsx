/**
 * Platform Runs Page — M9-C67.2
 *
 * Canonical runtime runs list from /platform/v1/runs.
 * Alias for /platform/v1/history/runs (C67.1).
 *
 * Navigation to /platform/runs/{run_id} for run detail.
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { usePlatformRuns, isRunSuccess, isRunFailed } from '@/lib/hooks/use-platform-runs';
import { HealthBadge } from '@/components/platform/health-badge';
import {
  History,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const PAGE_SIZE = 20;

export default function PlatformRunsPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = usePlatformRuns(page, PAGE_SIZE);

  const runs = data?.data?.items ?? [];
  const total = data?.data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  if (isLoading) {
    return <LoadingState />;
  }

  if (error) {
    return <ApiErrorState message={error.message} />;
  }

  return (
    <div className="flex flex-col gap-4 max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
            <History className="h-5 w-5 text-blue-400" />
            Run History
          </h1>
          <p className="text-sm text-[var(--text-tertiary)] mt-0.5">
            {total} runs · canonical source: EngineeringEventStore
          </p>
        </div>
        <Link
          href="/platform/history"
          className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)] flex items-center gap-1 transition-colors"
        >
          <ChevronLeft className="h-3 w-3" />
          Also in History
        </Link>
      </div>

      {/* Runs list */}
      {runs.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="flex flex-col gap-2">
          {runs.map((run) => (
            <RunCard key={run.id} run={run} onClick={() => router.push(`/platform/runs/${encodeURIComponent(run.id)}`)} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 text-xs rounded-lg border border-[var(--border-subtle)] hover:bg-[var(--surface-raised)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>
          <span className="text-xs text-[var(--text-tertiary)] font-mono">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1.5 text-xs rounded-lg border border-[var(--border-subtle)] hover:bg-[var(--surface-raised)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Next
          </button>
        </div>
      )}

      {/* Footer */}
      <div className="border-t border-[var(--border-subtle)] pt-3 text-xs text-[var(--text-tertiary)] font-mono">
        UI → Platform API → EngineeringEventStore → no second execution path
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

function RunCard({ run, onClick }: { run: { id: string; started_at: string; finished_at: string | null; duration_ms: number | null; status: string; capabilities_run: number; capabilities_passed: number; capabilities_failed: number; environment: string; intent: string; commit?: string; command?: string }; onClick: () => void }) {
  const success = isRunSuccess(run.status);
  const failed = isRunFailed(run.status);

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left rounded-lg border px-4 py-3 transition-colors hover:bg-[var(--surface-raised)]',
        success ? 'border-emerald-500/20' : failed ? 'border-red-500/20' : 'border-[var(--border-subtle)]',
      )}
    >
      <div className="flex items-center gap-3">
        <HealthBadge status={run.status} size="sm" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-mono text-[var(--text-primary)] truncate">{run.id}</span>
            {run.commit && (
              <span className="text-xs font-mono text-[var(--text-tertiary)] shrink-0">
                {run.commit.slice(0, 8)}
              </span>
            )}
            <span className="text-xs font-mono text-[var(--text-tertiary)] shrink-0">{run.environment}</span>
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
            {run.command && (
              <span className="text-xs font-mono text-violet-400 shrink-0">{run.command}</span>
            )}
          </div>
        </div>

        {/* Results */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="text-right">
            <div className="flex items-center gap-1 text-sm">
              {success ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              ) : failed ? (
                <XCircle className="h-4 w-4 text-red-400" />
              ) : (
                <Loader2 className="h-4 w-4 text-slate-400 animate-spin" />
              )}
              <span className={cn(
                'font-mono font-semibold',
                success ? 'text-emerald-400' : failed ? 'text-red-400' : 'text-slate-400',
              )}>
                {run.capabilities_passed}/{run.capabilities_run}
              </span>
            </div>
            {run.capabilities_failed > 0 && (
              <div className="text-xs text-red-400 font-mono">{run.capabilities_failed} failed</div>
            )}
          </div>
          <ChevronRight className="h-4 w-4 text-[var(--text-tertiary)] shrink-0" />
        </div>
      </div>
    </button>
  );
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="flex items-center gap-2 text-sm text-[var(--text-tertiary)]">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading runs...
      </div>
    </div>
  );
}

function ApiErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center border border-red-500/30 rounded-lg bg-red-500/5">
      <div className="text-red-400 text-lg font-semibold">API UNAVAILABLE</div>
      <div className="text-sm text-[var(--text-secondary)] max-w-md">{message}</div>
      <div className="text-xs text-[var(--text-tertiary)] font-mono">
        Unable to retrieve run history from the backend.
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center gap-2 py-16 text-[var(--text-tertiary)]">
      <History className="h-8 w-8 opacity-40" />
      <span className="text-sm">No runs recorded yet</span>
      <span className="text-xs">Runs will appear here after verification execution</span>
      <Link
        href="/platform/verification"
        className="mt-3 text-xs px-4 py-2 rounded-lg border border-[var(--border-subtle)] hover:border-[var(--border-default)] hover:bg-[var(--surface-raised)] transition-colors"
      >
        Run verification →
      </Link>
    </div>
  );
}
