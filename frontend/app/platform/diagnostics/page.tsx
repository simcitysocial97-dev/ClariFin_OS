/**
 * Platform Diagnostics Page — M9-C57 Phase 9
 *
 * Entry point for deterministic diagnostics. Links to change intelligence,
 * error deep-dive, and future diagnostic sub-pages.
 * The AI diagnostic assistant is deferred to Band D (Phase 17).
 */

'use client';

import Link from 'next/link';
import { useCurrentErrorCount } from '@/lib/hooks/use-platform-errors';
import { usePlatformHealth } from '@/lib/hooks/use-platform-health';
import { usePlatformEvents } from '@/lib/hooks/use-platform-events';
import {
  Bug,
  FileSearch,
  Activity,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function DiagnosticsPage() {
  const errorCount = useCurrentErrorCount();
  const { data: healthData } = usePlatformHealth();
  const { data: eventsData } = usePlatformEvents(10);

  return (
    <div className="flex flex-col gap-4 max-w-3xl">
      {/* Header */}
      <div>
        <h1 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
          <Bug className="h-5 w-5 text-red-400" />
          Diagnostics
        </h1>
        <p className="text-xs text-[var(--text-tertiary)] mt-0.5">
          Deterministic analysis first. AI assistance deferred to Level 2+.
        </p>
      </div>

      {/* System health snapshot */}
      <HealthSnapshot platform={healthData?.data?.platform ?? 'UNKNOWN'} verification={healthData?.data?.verification ?? 'UNKNOWN'} />

      {/* Diagnostic actions */}
      <div className="flex flex-col gap-3">
        <DiagnosticAction
          icon={<FileSearch className="h-5 w-5 text-blue-400" />}
          title="Change Intelligence"
          description="Inspect blast radius of repository changes and recommended verification targets."
          href="/platform/diagnostics/change"
          badge="L1"
        />
        <DiagnosticAction
          icon={<AlertTriangle className="h-5 w-5 text-red-400" />}
          title={`Error Deep-Dive (${errorCount})`}
          description="Browse current errors with frequency analysis and per-error detail."
          href="/platform/errors"
          variant={errorCount > 0 ? 'alert' : undefined}
        />
        <DiagnosticAction
          icon={<Activity className="h-5 w-5 text-violet-400" />}
          title="Recent Activity"
          description="Review the last 10 platform events to trace execution lineage."
          href="/platform/events"
        />
        <DiagnosticAction
          icon={<ShieldCheck className="h-5 w-5 text-emerald-400" />}
          title="Architecture Safety"
          description="Inspect authority boundaries, duplicates, bypasses, and deprecations."
          href="/platform/architecture"
        />
      </div>

      {/* Event feed */}
      {eventsData?.data?.items && eventsData.data.items.length > 0 && (
        <div className="border-t border-[var(--border-subtle)] pt-3 mt-2">
          <div className="text-xs font-semibold text-[var(--text-secondary)] mb-2">Latest events</div>
          <div className="flex flex-col gap-1">
            {eventsData.data.items.slice(0, 5).map((ev) => (
              <div key={ev.id} className="flex items-center gap-3 text-xs font-mono text-[var(--text-tertiary)]">
                <span className="w-20 shrink-0">{ev.emitted_at.slice(11, 19)}</span>
                <span className="text-[var(--text-secondary)]">{ev.event_type}</span>
                <span className="truncate">{ev.task_id ?? ev.execution_id ?? ''}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

function HealthSnapshot({
  platform,
  verification,
}: {
  platform: string;
  verification: string;
}) {
  return (
    <div className={cn(
      'rounded-lg border p-4 flex items-center gap-4',
      platform === 'HEALTHY' ? 'border-emerald-500/20 bg-emerald-500/5' :
      platform === 'DEGRAD' ? 'border-amber-500/20 bg-amber-500/5' :
      'border-red-500/20 bg-red-500/5',
    )}>
      <div className={cn(
        'text-2xl font-bold font-mono',
        platform === 'HEALTHY' ? 'text-emerald-400' :
        platform === 'DEGRAD' ? 'text-amber-400' : 'text-red-400',
      )}>
        {platform}
      </div>
      <div className="flex-1">
        <div className="text-sm text-[var(--text-primary)]">System Status</div>
        <div className="text-xs text-[var(--text-tertiary)]">
          Verification: <span className="font-mono">{verification}</span>
        </div>
      </div>
      <div className="text-xs text-[var(--text-tertiary)] font-mono">
        Deterministic · No LLM required
      </div>
    </div>
  );
}

function DiagnosticAction({
  icon,
  title,
  description,
  href,
  badge,
  variant,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  href: string;
  badge?: string;
  variant?: 'alert';
}) {
  return (
    <Link
      href={href}
      className={cn(
        'flex items-center gap-4 px-4 py-3 rounded-lg border transition-colors hover:bg-[var(--surface-raised)]',
        variant === 'alert'
          ? 'border-red-500/30 hover:border-red-500/50'
          : 'border-[var(--border-subtle)] hover:border-[var(--border-default)]',
      )}
    >
      <span className="shrink-0">{icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-[var(--text-primary)]">{title}</span>
          {badge && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--surface-raised)] text-[var(--text-tertiary)] font-mono">
              {badge}
            </span>
          )}
        </div>
        <div className="text-xs text-[var(--text-tertiary)] mt-0.5">{description}</div>
      </div>
      <ArrowRight className="h-4 w-4 text-[var(--text-tertiary)] shrink-0" />
    </Link>
  );
}
