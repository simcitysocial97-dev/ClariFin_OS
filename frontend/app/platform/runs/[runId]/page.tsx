/**
 * Platform Run Detail Page — M9-C67.2
 *
 * Canonical run detail from /platform/v1/runs/{run_id}.
 * Preserves runtime identity fields — never transforms a runtime failure
 * into a generic frontend error.
 *
 * Organized into sections: Identity, Execution, Plan, Result,
 * Classification, Evidence, Artifacts, Timeline.
 */

'use client';

import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { usePlatformRun, isRunSuccess, isRunFailed } from '@/lib/hooks/use-platform-runs';
import { HealthBadge } from '@/components/platform/health-badge';
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Loader2,
  GitCommit,
  FileText,
  ShieldCheck,
  Target,
  CalendarDays,
  Activity,
  History,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function PlatformRunDetailPage() {
  const params = useParams<{ runId: string }>();
  const router = useRouter();
  const runId = params.runId;

  const { data, isLoading, error } = usePlatformRun(runId);

  if (isLoading) {
    return <LoadingState />;
  }

  if (error) {
    if ('status' in error && (error as { status: number }).status === 404) {
      return <NotFoundState runId={runId} onBack={() => router.push('/platform/runs')} />;
    }
    return <ApiErrorState message={error.message} onBack={() => router.push('/platform/runs')} />;
  }

  const run = data?.data;
  if (!run) {
    return <EmptyState runId={runId} onBack={() => router.push('/platform/runs')} />;
  }

  const success = isRunSuccess(run.status);
  const failed = isRunFailed(run.status);

  return (
    <div className="flex flex-col gap-5 max-w-5xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.back()}
          className="p-1.5 rounded-lg border border-[var(--border-subtle)] hover:bg-[var(--surface-raised)] transition-colors"
        >
          <ArrowLeft className="h-4 w-4 text-[var(--text-tertiary)]" />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-lg font-bold text-[var(--text-primary)]">Run Detail</h1>
            <span className="text-sm font-mono text-[var(--text-tertiary)]">{run.id}</span>
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <HealthBadge status={run.status} size="sm" />
            {run.command && (
              <span className="text-xs font-mono text-violet-400">{run.command}</span>
            )}
            {run.profile && (
              <span className="text-xs font-mono text-[var(--text-tertiary)]">profile: {run.profile}</span>
            )}
          </div>
        </div>
        {run.commit && (
          <div className="text-xs font-mono text-[var(--text-tertiary)] shrink-0">
            <GitCommit className="h-3 w-3 inline mr-1" />
            {run.commit.slice(0, 12)}
          </div>
        )}
      </div>

      {/* Identity */}
      <SectionCard title="Identity" icon={<Target className="h-4 w-4 text-blue-400" />}>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <MetaField label="Run ID" value={run.id} />
           <MetaField label="Status" value={run.status} />
           {run.commit && <MetaField label="Commit" value={run.commit.slice(0, 12)} />}
          {run.command && <MetaField label="Command" value={run.command} />}
          {run.profile && <MetaField label="Profile" value={run.profile} />}
          <MetaField label="Duration" value={run.duration_ms ? `${(run.duration_ms / 1000).toFixed(1)}s` : '—'} />
        </div>
      </SectionCard>

      {/* Execution */}
      <SectionCard title="Execution" icon={<Activity className="h-4 w-4 text-violet-400" />}>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <MetaField label="Started" value={run.started_at} />
          <MetaField label="Finished" value={run.finished_at ?? 'Running...'} />
          <MetaField label="Capabilities Run" value={String(run.capabilities_run)} />
          <MetaField label="Capabilities Passed" value={String(run.capabilities_passed)} />
          <MetaField label="Capabilities Failed" value={String(run.capabilities_failed)} />
          {run.duration_ms && (
            <MetaField label="Duration" value={`${(run.duration_ms / 1000).toFixed(1)}s`} />
          )}
        </div>
      </SectionCard>

      {/* Result */}
      <SectionCard title="Result" icon={success ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : failed ? <XCircle className="h-4 w-4 text-red-400" /> : <Loader2 className="h-4 w-4 text-slate-400 animate-spin" />}>
        <div className="flex items-center gap-3 mb-3">
          <span className={cn(
            'text-lg font-bold font-mono',
            success ? 'text-emerald-400' : failed ? 'text-red-400' : 'text-slate-400',
          )}>
            {run.status}
          </span>
          <HealthBadge status={run.status} size="md" />
        </div>
        <div className="text-xs text-[var(--text-secondary)]">
          {success
            ? `All ${run.capabilities_passed} capabilities passed.`
            : failed
              ? `${run.capabilities_failed} of ${run.capabilities_run} capabilities failed.`
              : `Run in progress: ${run.capabilities_passed}/${run.capabilities_run} completed.`
          }
        </div>
      </SectionCard>

      {/* Classification */}
      <SectionCard title="Classification" icon={<ShieldCheck className="h-4 w-4 text-amber-400" />}>
        <div className="text-xs text-[var(--text-secondary)]">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[var(--text-tertiary)]">Runtime classification:</span>
            <span className="font-mono text-[var(--text-primary)]">{run.status}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[var(--text-tertiary)]">Authority:</span>
            <span className="font-mono text-[var(--text-primary)]">EngineeringEventStore</span>
          </div>
          <div className="mt-2 text-[var(--text-tertiary)]">
            This is the canonical runtime status. The frontend does not recalculate or reinterpret it.
          </div>
        </div>
      </SectionCard>

      {/* Evidence */}
      <SectionCard title="Evidence" icon={<FileText className="h-4 w-4 text-cyan-400" />}>
        {run.evidence_ids && run.evidence_ids.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {run.evidence_ids.slice(0, 20).map((eid) => (
              <Link
                key={eid}
                href={`/platform/evidence`}
                className="text-xs font-mono px-2 py-1 rounded bg-[var(--surface-raised)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-interactive)] border border-[var(--border-subtle)] transition-colors"
              >
                {eid}
              </Link>
            ))}
            {run.evidence_ids.length > 20 && (
              <span className="text-xs text-[var(--text-tertiary)]">
                +{run.evidence_ids.length - 20} more
              </span>
            )}
          </div>
        ) : (
          <div className="text-xs text-[var(--text-tertiary)]">No evidence IDs recorded for this run.</div>
        )}
      </SectionCard>

      {/* Capability Results */}
      {run.capability_results && run.capability_results.length > 0 && (
        <SectionCard title="Capability Results" icon={<Target className="h-4 w-4 text-purple-400" />}>
          <div className="flex flex-col gap-1">
            {run.capability_results.slice(0, 30).map((r, i) => (
              <div key={i} className="flex items-center gap-3 text-xs py-1 border-b border-[var(--border-subtle)] last:border-0">
                <HealthBadge status={r.status} size="sm" showLabel={false} />
                <span className="font-mono text-[var(--text-primary)] w-48 truncate">{r.capability_id}</span>
                {r.duration_ms != null && (
                  <span className="text-[var(--text-tertiary)] font-mono">{(r.duration_ms / 1000).toFixed(1)}s</span>
                )}
                {r.error && (
                  <span className="text-red-400 font-mono truncate flex-1" title={r.error}>{r.error}</span>
                )}
                {r.evidence_ids && r.evidence_ids.length > 0 && (
                  <span className="text-[var(--text-tertiary)] font-mono text-[10px]">
                    {r.evidence_ids.length} evidence
                  </span>
                )}
              </div>
            ))}
            {run.capability_results.length > 30 && (
              <div className="text-xs text-[var(--text-tertiary)] pt-1">
                Showing 30 of {run.capability_results.length} capability results
              </div>
            )}
          </div>
        </SectionCard>
      )}

      {/* Timeline */}
      <SectionCard title="Timeline" icon={<CalendarDays className="h-4 w-4 text-slate-400" />}>
        <div className="flex flex-col gap-2 text-xs">
          <TimelineEvent label="Started" time={run.started_at} />
          {run.finished_at && (
            <TimelineEvent label="Finished" time={run.finished_at} />
          )}
          {run.duration_ms && (
            <TimelineEvent label="Duration" time={`${(run.duration_ms / 1000).toFixed(1)}s`} />
          )}
        </div>
      </SectionCard>

      {/* Footer */}
      <div className="border-t border-[var(--border-subtle)] pt-3 flex items-center justify-between text-xs text-[var(--text-tertiary)] font-mono">
        <span>Source: runtime.system.observability.event_store.EngineeringEventStore</span>
        <span>
          <Link href="/platform/runs" className="hover:text-[var(--text-primary)] transition-colors">
            ← Back to runs
          </Link>
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

function SectionCard({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-raised)] p-4 flex flex-col gap-3">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-sm font-semibold text-[var(--text-primary)]">{title}</span>
      </div>
      {children}
    </div>
  );
}

function MetaField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-[var(--text-tertiary)]">{label}</span>
      <div className="text-sm font-mono text-[var(--text-secondary)] truncate" title={value}>
        {value}
      </div>
    </div>
  );
}

function TimelineEvent({ label, time }: { label: string; time: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-[var(--text-tertiary)] w-24 shrink-0">{label}</span>
      <span className="font-mono text-[var(--text-secondary)]">{time}</span>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="flex items-center gap-2 text-sm text-[var(--text-tertiary)]">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading run details...
      </div>
    </div>
  );
}

function ApiErrorState({ message, onBack }: { message: string; onBack: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center border border-red-500/30 rounded-lg bg-red-500/5">
      <div className="text-red-400 text-lg font-semibold">API UNAVAILABLE</div>
      <div className="text-sm text-[var(--text-secondary)] max-w-md">{message}</div>
      <button
        onClick={onBack}
        className="mt-2 px-4 py-2 text-sm rounded-lg border border-red-500/30 text-red-300 hover:bg-red-500/10 transition-colors flex items-center gap-1"
      >
        <ArrowLeft className="h-3 w-3" /> Back to runs
      </button>
    </div>
  );
}

function NotFoundState({ runId, onBack }: { runId: string; onBack: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center border border-amber-500/30 rounded-lg bg-amber-500/5">
      <div className="text-amber-400 text-lg font-semibold">RUN NOT FOUND</div>
      <div className="text-sm text-[var(--text-secondary)] font-mono">{runId}</div>
      <div className="text-xs text-[var(--text-tertiary)]">
        This run ID does not exist in the EngineeringEventStore.
      </div>
      <button
        onClick={onBack}
        className="mt-2 px-4 py-2 text-sm rounded-lg border border-amber-500/30 text-amber-300 hover:bg-amber-500/10 transition-colors flex items-center gap-1"
      >
        <ArrowLeft className="h-3 w-3" /> Back to runs
      </button>
    </div>
  );
}

function EmptyState({ runId, onBack }: { runId: string; onBack: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <History className="h-12 w-12 text-[var(--text-tertiary)] opacity-40" />
      <div className="text-sm text-[var(--text-secondary)]">No run data available</div>
      <div className="text-xs text-[var(--text-tertiary)] font-mono">{runId}</div>
      <button
        onClick={onBack}
        className="mt-2 px-4 py-2 text-sm rounded-lg border border-[var(--border-subtle)] hover:bg-[var(--surface-raised)] transition-colors flex items-center gap-1"
      >
        <ArrowLeft className="h-3 w-3" /> Back to runs
      </button>
    </div>
  );
}
