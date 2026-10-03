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
 *
 * M11 — FOUR STATES, NOT TWO
 * --------------------------
 * The binary state above was measured to be insufficient. On a cold start the
 * console sits for tens of seconds waiting on the backend, and "DEGRADED" told
 * an operator nothing about whether to WAIT or to ACT. `ConsoleUnavailableState`
 * now renders three distinct terminal states from evidence
 * (`lib/platform/backend-status.ts`): backend unavailable, backend starting,
 * and platform endpoint failed. See the docstring on that component.
 */

'use client';

import { RefreshCw } from 'lucide-react';
import type { ReactNode } from 'react';
import type { BackendStatusDetail } from '@/lib/platform/backend-status';

export type ConsoleStatus = 'DEGRADED' | 'UNKNOWN' | 'STARTING' | 'READY';

const STATUS_STYLES: Record<ConsoleStatus, string> = {
  DEGRADED: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
  UNKNOWN: 'bg-zinc-500/20 text-zinc-300 border-zinc-500/40',
  STARTING: 'bg-sky-500/20 text-sky-300 border-sky-500/40',
  READY: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
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
 * Shared retry affordance.
 *
 * A retry control is not a convenience here: it is the console's only recovery
 * path, because Platform API reads do not retry themselves
 * (`platformReadRetryPolicy`). Automatic retry was measured to be actively
 * harmful on this surface — a cold 5-way burst had four requests issued in
 * different milliseconds all return at the same instant, because the platform
 * handlers run synchronous builders on the event loop, so a retry appends to a
 * queue rather than bypassing it.
 */
function RetryButton({
  onRetry,
  retrying,
  label = 'Retry',
  testId = 'console-retry',
}: {
  onRetry: () => void;
  retrying?: boolean;
  label?: string;
  testId?: string;
}) {
  return (
    <button
      type="button"
      onClick={onRetry}
      disabled={retrying}
      data-testid={testId}
      className="mt-1 inline-flex items-center gap-1.5 rounded-lg border border-[var(--border-default)] px-3 py-1.5 text-sm text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-raised)] disabled:opacity-60"
    >
      <RefreshCw className={`h-3.5 w-3.5 ${retrying ? 'animate-spin' : ''}`} />
      {retrying ? 'Retrying…' : label}
    </button>
  );
}

/**
 * M11 — the console's terminal "cannot show data" state, driven by evidence.
 *
 * WHY ONE COMPONENT INSTEAD OF THREE
 * ----------------------------------
 * M9-C71 gave the console a binary out-of-band state: data, or `DEGRADED`. M11
 * measured why that was not enough. On a cold start the console sits in a window
 * where the backend is booting, and the operator needs to know whether to WAIT
 * or to ACT:
 *
 *   backend-unavailable — nothing is listening. Act: start or restart the backend.
 *   backend-starting    — the connection was accepted and nothing came back.
 *                         Act: wait. Restarting a process that is 40 s into
 *                         importing its module graph destroys the warm-up.
 *   backend-ready + a
 *   failed platform read — the backend is healthy and an endpoint is at fault.
 *                         Act: investigate the endpoint, not the process.
 *
 * Collapsing the middle case into "DEGRADED" is what makes a control room lie:
 * it tells an operator to intervene precisely when intervening is most
 * expensive. All three are therefore rendered from one component so the
 * vocabulary cannot drift per page.
 *
 * SELECTOR CONTRACT (do not change)
 * ---------------------------------
 * The outer `data-testid="console-unavailable"` and the headline's
 * `data-testid="console-api-unavailable"` are the pre-M11 contract and are
 * asserted by three Playwright specs (`platform-dashboard`, `platform-c67.2`,
 * `m10-agent3-console`) as "the console reached a terminal state". They are
 * kept verbatim; the specific state is exposed additively as
 * `[data-testid="console-unavailable"][data-console-state="<state>"]`. Widening
 * the outer testid would have silently changed what those specs assert.
 *
 * ARCHITECTURE AUTHORITY
 * ---------------------
 * Unchanged from M9-C71 and non-negotiable: the console never computes a health
 * verdict. It reports which state it is in and the backend's own reason string.
 */
export function ConsoleUnavailableState({
  heading = 'Platform',
  subject,
  message,
  detail,
  onRetry,
  retrying,
}: {
  heading?: string;
  subject?: string;
  message?: string;
  /** Classified cause from `classifyLiveness` / `classifyPlatformRead`. */
  detail?: BackendStatusDetail;
  onRetry?: () => void;
  retrying?: boolean;
}) {
  // M11 guard: a healthy backend must never be able to render an "unavailable"
  // banner, even through a logic bug in a caller. Every other verdict collapses
  // to `unavailable`, which would silently invert the message for `ready` and
  // `unknown`. Returning nothing is the only safe fallback for those two: the
  // caller renders live data instead, which is the correct thing to do.
  if (detail?.status === 'ready' || detail?.status === 'unknown') return null;

  const state: TerminalState =
    detail?.status === 'starting' || detail?.status === 'endpoint-failed'
      ? detail.status
      : 'unavailable';
  const presentation = STATE_PRESENTATION[state];

  return (
    <div
      data-testid="console-unavailable"
      data-console-state={state}
      data-console-timed-out={detail?.timedOut ? 'true' : 'false'}
      className="flex flex-col items-start gap-3 py-12 text-left"
    >
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-bold text-[var(--text-primary)]" data-testid="console-heading">
          {heading}
        </h1>
        <ConsoleStatusBadge
          status={presentation.badge}
          label={presentation.badgeLabel}
        />
      </div>

      <p
        className={`text-sm font-semibold ${presentation.headlineClass}`}
        data-testid="console-api-unavailable"
      >
        {presentation.headline}
      </p>

      {subject ? (
        <p className="text-sm text-[var(--text-secondary)]" data-testid="console-subject">
          {subject}
        </p>
      ) : null}

      <p
        className="max-w-2xl text-xs text-[var(--text-tertiary)]"
        data-testid="console-state-explanation"
      >
        {presentation.explanation}
      </p>

      {detail?.reason ? (
        <p
          className="max-w-2xl break-words font-mono text-xs text-[var(--text-tertiary)]"
          data-testid={`console-state-${state}`}
        >
          {detail.reason}
        </p>
      ) : null}

      {typeof detail?.elapsedMs === 'number' ? (
        <p
          className="font-mono text-xs text-[var(--text-tertiary)]"
          data-testid="console-state-elapsed"
        >
          {`probe took ${Math.round(detail.elapsedMs)} ms`}
        </p>
      ) : null}

      {message ? (
        <p
          className="max-w-2xl break-words font-mono text-xs text-[var(--text-tertiary)]"
          data-testid="console-error-detail"
        >
          {message}
        </p>
      ) : null}

      {onRetry ? (
        <RetryButton
          onRetry={onRetry}
          retrying={retrying}
          label={state === 'starting' ? 'Check again' : 'Retry'}
        />
      ) : null}
    </div>
  );
}

type TerminalState = 'unavailable' | 'starting' | 'endpoint-failed';

interface StatePresentation {
  badge: ConsoleStatus;
  badgeLabel: string;
  headline: string;
  headlineClass: string;
  explanation: string;
}

const STATE_PRESENTATION: Record<TerminalState, StatePresentation> = {
  unavailable: {
    badge: 'DEGRADED',
    badgeLabel: 'BACKEND UNAVAILABLE',
    headline: 'API UNAVAILABLE',
    headlineClass: 'text-red-400',
    explanation:
      'The console cannot reach the backend, so it cannot list or verify anything. Framework status is UNAVAILABLE — it is decided by the backend and is never computed here.',
  },
  starting: {
    badge: 'STARTING',
    badgeLabel: 'BACKEND STARTING',
    headline: 'BACKEND STARTING — WAIT, DO NOT RESTART',
    headlineClass: 'text-sky-300',
    explanation:
      'The connection was accepted and no response came, which is what a booting backend looks like. The financial application imports its module graph before it binds the port, and the first uncached Platform API read then runs a synchronous build while the backend is serving. Both are expected to finish on their own; restarting now discards the warm-up.',
  },
  'endpoint-failed': {
    badge: 'DEGRADED',
    badgeLabel: 'PLATFORM ENDPOINT FAILED',
    headline: 'PLATFORM ENDPOINT FAILED — BACKEND IS SERVING',
    headlineClass: 'text-amber-300',
    explanation:
      'The backend answered its liveness probe, so this is an endpoint failure and not a cold start — the process is not the problem. Framework status is UNAVAILABLE for the failed read; it is decided by the backend and is never computed here.',
  },
};

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
