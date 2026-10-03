'use client';

/**
 * Platform Console backend status strip — M11
 * ===========================================
 *
 * The console's per-page terminal state tells an operator what happened to *this
 * page*. This strip tells them what is happening to the *backend*, on every page,
 * including pages whose data has not started loading yet.
 *
 * Why it is a strip and not a per-page concern:
 *   - a control room is read across routes, and an operator who lands on
 *     `/platform/evidence` during a cold start has no reason to know they should
 *     have gone to the dashboard first;
 *   - the strip is the one surface that must never itself be blocked by a slow
 *     data read, so it is driven by the fast liveness probe only
 *     (`GET /health`, measured 3.8–17.3 ms) and never by a platform read.
 *
 * What it does NOT do: decide health. It renders the backend's own words and the
 * transport-level classification. `DEGRADED` still means "the console cannot
 * verify", and the framework verdict remains the backend's alone.
 *
 * M11 measurement this is built on is recorded in
 * `docs/audits/m11-agent4-cold-start-readiness.md`.
 */

import { Loader2, PlugZap, Server, ServerCrash } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import {
  BACKEND_STATUS_LABEL,
  useBackendStatus,
  type BackendStatus,
  type UseBackendStatusOptions,
} from '@/lib/platform/backend-status';
import { cn } from '@/lib/utils';

const ICONS: Record<BackendStatus, LucideIcon> = {
  unknown: Loader2,
  unavailable: PlugZap,
  starting: Loader2,
  ready: Server,
  'endpoint-failed': ServerCrash,
};

const TONE: Record<BackendStatus, string> = {
  unknown: 'text-slate-400',
  unavailable: 'text-red-400',
  starting: 'text-sky-300',
  ready: 'text-emerald-300',
  'endpoint-failed': 'text-amber-300',
};

export function PlatformBackendStatus({
  className,
  ...options
}: UseBackendStatusOptions & { className?: string }) {
  const { status, reason, label, short, elapsedMs, refresh, lastProbedAt } =
    useBackendStatus(options);
  const Icon = ICONS[status];
  const spinning = status === 'starting' || status === 'unknown';

  return (
    <div
      data-testid="platform-backend-status"
      data-backend-status={status}
      role="status"
      aria-live="polite"
      className={cn(
        'flex shrink-0 flex-wrap items-center gap-x-3 gap-y-1 border-b border-[var(--border-subtle)] bg-[var(--surface-base)] px-5 py-1.5 font-mono text-xs',
        TONE[status],
        className,
      )}
    >
      <span className="inline-flex items-center gap-1.5" data-testid="platform-backend-status-label">
        <Icon className={cn('h-3.5 w-3.5', spinning && 'animate-spin')} aria-hidden="true" />
        <span className="font-bold uppercase tracking-wide" data-testid="platform-backend-status-value">
          {label}
        </span>
      </span>

      <span className="text-[var(--text-tertiary)]" data-testid="platform-backend-status-short">
        {short}
        {typeof elapsedMs === 'number' ? ` (${Math.round(elapsedMs)} ms)` : ''}
      </span>

      {status !== 'ready' ? (
        <>
          <span
            className="min-w-0 flex-1 truncate text-[var(--text-tertiary)]"
            data-testid="platform-backend-status-reason"
            title={reason}
          >
            {reason}
          </span>
          <button
            type="button"
            onClick={() => {
              void refresh();
            }}
            data-testid="platform-backend-status-retry"
            className="rounded border border-[var(--border-default)] px-2 py-0.5 text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-raised)]"
          >
            Re-check
          </button>
        </>
      ) : (
        <span
          className="min-w-0 flex-1 truncate text-[var(--text-tertiary)]"
          data-testid="platform-backend-status-ready-at"
        >
          {lastProbedAt ? `confirmed ${lastProbedAt}` : BACKEND_STATUS_LABEL.ready}
        </span>
      )}
    </div>
  );
}
