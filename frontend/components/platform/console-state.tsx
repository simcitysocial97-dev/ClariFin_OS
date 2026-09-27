/**
 * Platform Console Canonical States — M9-C71
 *
 * Single source of truth for the operational console's out-of-band states.
 *
 * WHY THIS EXISTS
 * ---------------
 * The console previously carried a private copy of an "API UNAVAILABLE" block
 * on every page, and the dashboard had no error path at all: it gated only on
 * `isLoading`, so an unreachable platform API left the primary operations
 * screen showing "Loading platform state…" forever. For a console whose job is
 * to report system state, silently looking busy is the worst possible failure
 * mode — an operator cannot distinguish "still working" from "not working".
 *
 * RUNTIME AUTHORITY (do not regress this)
 * ---------------------------------------
 * Framework health is decided by the backend. The console NEVER computes a
 * health verdict. When the platform API cannot be reached the console reports
 * its OWN status — DEGRADED, meaning "I cannot verify" — and states explicitly
 * that the framework verdict is unavailable. `DEGRADED` is the console's
 * existing amber "not fully determined" token (see SystemStatusCard), so no
 * new vocabulary is invented.
 *
 * Every state is assertable: a titled heading, a status badge, the explicit
 * unavailability statement, and a retry affordance. That is what makes the
 * console's contract testable in an environment where the backend is
 * intentionally absent.
 */

'use client';

import { RefreshCw } from 'lucide-react';
import type { ReactNode } from 'react';

export type ConsoleStatus = 'DEGRADED' | 'UNKNOWN';

const STATUS_STYLES: Record<ConsoleStatus, string> = {
  DEGRADED: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
  UNKNOWN: 'bg-zinc-500/20 text-zinc-300 border-zinc-500/40',
};

/**
 * Console status badge. `rounded-full` + `font-bold` are part of the console's
 * status contract: operations screens read status by badge, so the badge must
 * be visually and programmatically identifiable.
 */
export function ConsoleStatusBadge({
  status = 'DEGRADED',
  label,
}: {
  status?: ConsoleStatus;
  label?: string;
}) {
  return (
    <span
      data-testid="console-status-badge"
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-bold uppercase tracking-wide ${STATUS_STYLES[status]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
      {label ?? status}
    </span>
  );
}

/**
 * Loading state with the same structure as the terminal states, so the console
 * never collapses to a bare sentence.
 */
export function ConsoleLoadingState({ label = 'Loading platform state…' }: { label?: string }) {
  return (
    <div className="flex flex-col gap-3 py-12">
      <h1 className="text-xl font-bold text-[var(--text-primary)]" data-testid="console-heading">
        Platform
      </h1>
      <div
        className="flex items-center gap-2 text-sm text-[var(--text-tertiary)]"
        data-testid="console-loading"
      >
        <RefreshCw className="h-4 w-4 animate-spin" />
        {label}
      </div>
    </div>
  );
}

/**
 * Terminal state for an unreachable platform API.
 *
 * `subject` is the inventory line the page owns — e.g. "No workflows to list".
 * It is rendered *together with* the explicit unavailability statement, never
 * instead of it, so an operator can never read "unavailable" as "genuinely
 * empty".
 */
export function ConsoleUnavailableState({
  heading,
  subject,
  message,
  onRetry,
}: {
  heading: string;
  subject: string;
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div
      data-testid="console-unavailable"
      className="flex flex-col items-start gap-3 py-12 text-left"
    >
      <div className="flex flex-wrap items-center gap-3">
        <h1
          className="text-xl font-bold text-[var(--text-primary)]"
          data-testid="console-heading"
        >
          {heading}
        </h1>
        <ConsoleStatusBadge status="DEGRADED" label="DEGRADED" />
      </div>

      <div className="text-sm font-semibold text-red-400" data-testid="console-api-unavailable">
        API UNAVAILABLE
      </div>

      <p className="text-sm text-[var(--text-secondary)]" data-testid="console-subject">
        {subject}
      </p>

      <p className="max-w-2xl text-xs text-[var(--text-tertiary)]">
        The platform API is unreachable, so the console cannot list or verify anything.
        Framework status is <span className="font-mono">UNAVAILABLE</span> — it is decided by
        the backend and is never computed here.
      </p>

      {message ? (
        <p className="max-w-2xl break-words font-mono text-xs text-[var(--text-tertiary)]">
          {message}
        </p>
      ) : null}

      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          data-testid="console-retry"
          className="mt-1 inline-flex items-center gap-1.5 rounded-lg border border-[var(--border-default)] px-3 py-1.5 text-sm text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-raised)]"
        >
          <RefreshCw className="h-3.5 w-3.5" /> Retry
        </button>
      ) : null}
    </div>
  );
}

/**
 * Terminal state for a reachable API that returned no items.
 */
export function ConsoleEmptyState({
  heading,
  subject,
  detail,
  action,
}: {
  heading: string;
  subject: string;
  detail?: string;
  action?: ReactNode;
}) {
  return (
    <div
      data-testid="console-empty"
      className="flex flex-col items-start gap-2 py-12 text-left"
    >
      <div className="flex flex-wrap items-center gap-3">
        <h1
          className="text-xl font-bold text-[var(--text-primary)]"
          data-testid="console-heading"
        >
          {heading}
        </h1>
        <ConsoleStatusBadge status="UNKNOWN" label="NO DATA" />
      </div>
      <p className="text-sm text-[var(--text-secondary)]" data-testid="console-subject">
        {subject}
      </p>
      {detail ? (
        <p className="max-w-2xl text-xs text-[var(--text-tertiary)]">{detail}</p>
      ) : null}
      {action}
    </div>
  );
}
