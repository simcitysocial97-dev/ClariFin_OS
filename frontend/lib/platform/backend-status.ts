/**
 * Platform Console backend status — M11 (cold-start readiness)
 * ===========================================================
 *
 * THE DEFECT THIS FILE EXISTS TO FIX
 * ---------------------------------
 * M10 measured, on a cold start, `GET /platform/v1/health` at 39 s and one
 * console request batch at 117 s. The console had no request deadline
 * (`lib/api/gateway.ts` called `fetch` with no `AbortSignal`), so during that
 * window every console page rendered an indefinite "Loading…". For a control
 * room, "still working" and "not working" are the only two things an operator
 * must never be unable to tell apart, and the console could not tell them
 * apart at all.
 *
 * THE FOUR STATES
 * ---------------
 * This module names them once so every console surface reports the same
 * taxonomy, and derives them from evidence rather than from a timer.
 *
 *   `unavailable`  — the backend could not be reached. Evidence: the transport
 *                    failed with a network error (`TypeError` from `fetch`),
 *                    i.e. nothing is listening on the port.
 *   `starting`     — the backend accepted the connection and did not answer
 *                    within the deadline, OR the liveness probe did not answer
 *                    while the process is known to be alive. Evidence:
 *                    `ApiTimeoutError`, which `fetch` only produces from an
 *                    abort. This is the state the console was previously
 *                    unable to represent at all.
 *   `ready`        — `GET /health` answered 200. The application is serving.
 *   `endpoint-failed`
 *                  — the application answered, but a `/platform/v1/*` read
 *                    failed or blew its deadline. This is a *defect*, not a
 *                    cold-start symptom, and is reported separately so an
 *                    operator does not read it as "still booting".
 *
 * WHY THE SPLIT IS EVIDENCE-BASED
 * -------------------------------
 * A refused connection and an accepted-but-silent connection look identical to
 * a caller that only watches a clock. They are distinguishable because
 * `fetch` produces different errors: a network-level failure surfaces as
 * `TypeError`, while an abort we initiated surfaces as `ApiTimeoutError`. That
 * difference is load-bearing here and is the reason `ApiTimeoutError` is a
 * separate class rather than a flag on `ApiError`.
 *
 * ARCHITECTURE AUTHORITY
 * ---------------------
 * This module decides *what the console can see*, never *what is true*. It
 * computes no health verdict, reads no artifact, and invents no status. Every
 * status string it exposes came from the backend; a state here only ever says
 * whether the console was able to obtain one. `DEGRADED` continues to mean
 * "I cannot verify" (see `components/platform/console-state.tsx`).
 *
 * Measured latency evidence for the deadlines used here lives in
 * `docs/audits/m11-agent4-cold-start-readiness.md`.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ApiError,
  LIVENESS_DEADLINE_MS,
  fetchLiveness,
  isTimeoutError,
} from '@/lib/api/gateway';

// ---------------------------------------------------------------------------
// Taxonomy
// ---------------------------------------------------------------------------

/**
 * The four operator-visible backend states.
 *
 * `'unknown'` is the pre-probe state, not a fifth failure mode: it is what the
 * console shows for the few milliseconds before the first liveness probe
 * returns, and it deliberately looks like `starting` rather than like a
 * problem.
 */
export type BackendStatus =
  | 'unknown'
  | 'unavailable'
  | 'starting'
  | 'ready'
  | 'endpoint-failed';

export interface BackendStatusDetail {
  status: BackendStatus;
  /** Which probe produced this verdict. Surfaced so a report is traceable. */
  source: 'liveness' | 'platform-read';
  /** Endpoint that failed, when one did. */
  path?: string;
  /** Operator-readable reason. Never contains a stack trace or a raw body. */
  reason: string;
  /** True when the verdict came from a deadline breach rather than a response. */
  timedOut: boolean;
  /** HTTP status when the server actually produced one. */
  httpStatus?: number;
  /** Wall-clock ms of the probe that produced this verdict. */
  elapsedMs?: number;
}

/** One-line operator copy per state. The console's contract vocabulary. */
export const BACKEND_STATUS_LABEL: Record<BackendStatus, string> = {
  unknown: 'CHECKING',
  unavailable: 'BACKEND UNAVAILABLE',
  starting: 'BACKEND STARTING',
  ready: 'BACKEND READY',
  'endpoint-failed': 'PLATFORM ENDPOINT FAILED',
};

/** Terse form for the persistent status strip. */
export const BACKEND_STATUS_SHORT: Record<BackendStatus, string> = {
  unknown: 'checking',
  unavailable: 'unavailable',
  starting: 'starting',
  ready: 'ready',
  'endpoint-failed': 'endpoint failed',
};

/**
 * Classify a liveness (`GET /health`) outcome.
 *
 * A 200 means the application is serving. Anything else means it is not, and
 * `timedOut` separates "it accepted the connection and went quiet" (`starting`)
 * from "there is nothing listening" (`unavailable`).
 */
export function classifyLiveness(outcome: {
  served: boolean;
  error?: unknown;
  elapsedMs?: number;
}): BackendStatusDetail {
  if (outcome.served) {
    return {
      status: 'ready',
      source: 'liveness',
      reason: 'The application answered GET /health.',
      timedOut: false,
      elapsedMs: outcome.elapsedMs,
    };
  }
  const error = outcome.error;
  if (isTimeoutError(error)) {
    return {
      status: 'starting',
      source: 'liveness',
      reason: `The backend accepted the connection but did not answer GET /health within ${error.timeoutMs} ms. It is still starting up.`,
      timedOut: true,
      elapsedMs: outcome.elapsedMs,
    };
  }
  if (error instanceof ApiError) {
    return {
      status: 'starting',
      source: 'liveness',
      reason: `The backend answered GET /health with HTTP ${error.status}. It is up but not serving.`,
      timedOut: false,
      httpStatus: error.status,
      elapsedMs: outcome.elapsedMs,
    };
  }
  return {
    status: 'unavailable',
    source: 'liveness',
    // Named causes, in the order they actually occur. `fetch` reports a
    // cross-origin rejection as the same TypeError as a refused connection, so
    // without naming CORS here an operator would restart a perfectly healthy
    // backend to fix a header. Measured: a backend answering `/health` in
    // 1.1 ms with no `Access-Control-Allow-Origin` produces exactly this
    // verdict, and it was genuinely invisible before this was written down.
    reason:
      'Nothing is answering on the backend address from this browser. Causes, in the order they occur: it is not running; it is still importing its module graph and has not bound the port; or it is running but this origin is not in its CORS allow-list (backend/src/startup.py reads CORS_ORIGINS).',
    timedOut: false,
    elapsedMs: outcome.elapsedMs,
  };
}

/**
 * Classify a `/platform/v1/*` read outcome against the known backend state.
 *
 * `backendReady` matters: a platform read that fails while liveness has never
 * succeeded is a cold-start symptom, and the same failure after liveness has
 * succeeded is a platform-endpoint defect. Reporting those identically is how a
 * genuine `/platform/v1/evidence` regression gets dismissed as "the backend is
 * probably still booting".
 */
export function classifyPlatformRead(
  outcome: { error: unknown; path?: string; elapsedMs?: number },
  backendReady: boolean,
): BackendStatusDetail {
  const { error, path } = outcome;
  if (isTimeoutError(error)) {
    if (!backendReady) {
      return {
        status: 'starting',
        source: 'platform-read',
        path,
        reason: `${path} did not answer within ${error.timeoutMs} ms and the backend has not confirmed it is serving. It is still starting up.`,
        timedOut: true,
        elapsedMs: outcome.elapsedMs,
      };
    }
    return {
      status: 'endpoint-failed',
      source: 'platform-read',
      path,
      reason: `${path} did not answer within ${error.timeoutMs} ms while the backend itself is healthy. The endpoint is stalled.`,
      timedOut: true,
      elapsedMs: outcome.elapsedMs,
    };
  }
  if (error instanceof ApiError) {
    if (!backendReady) {
      return {
        status: 'starting',
        source: 'platform-read',
        path,
        reason: `${path} answered HTTP ${error.status} before the backend confirmed it was serving.`,
        timedOut: false,
        httpStatus: error.status,
        elapsedMs: outcome.elapsedMs,
      };
    }
    return {
      status: 'endpoint-failed',
      source: 'platform-read',
      path,
      reason: `${path} answered HTTP ${error.status}.`,
      timedOut: false,
      httpStatus: error.status,
      elapsedMs: outcome.elapsedMs,
    };
  }
  return {
    status: 'unavailable',
    source: 'platform-read',
    path,
    reason: path
      ? `${path} could not reach the backend.`
      : 'The console could not reach the backend.',
    timedOut: false,
    elapsedMs: outcome.elapsedMs,
  };
}

/**
 * Decide whether a console screen must show a TERMINAL "cannot show data" panel.
 *
 * This is the gate every platform page applies before rendering its dashboard,
 * so it lives here rather than inline in each page: the four-state vocabulary
 * must not be re-derived per page, which is how it drifted in the first place.
 *
 * Two rules, both of which the console got wrong on its first implementation:
 *
 * 1. `starting` is NOT terminal. It means the connection was accepted and
 *    `GET /health` did not answer inside the 3 s LIVENESS deadline — which is the
 *    normal condition during a cold start, because the application spends ~16 s
 *    importing its module graph before it can serve anything. Showing a terminal
 *    panel there tells the operator to intervene during the window where
 *    intervening is most expensive. `starting` falls through to the loading state,
 *    which already carries the correct "wait, do not restart" copy.
 *
 * 2. Real data always wins. Once a platform read has landed, the dashboard is
 *    correct to render regardless of the liveness probe, because the probe is a
 *    3 s opinion and the read is the authority.
 *
 * `unavailable` (nothing listening) is terminal on its own; `readFailure` (a real
 * deadline breach or error, already classified against the liveness verdict) is
 * terminal by construction.
 *
 * A screen in `starting` with reads still in flight converges on its own: the
 * platform read carries the 20 s PLATFORM_API deadline, so the breach arrives as
 * `readFailure` and this gate returns a terminal state. Nothing spins forever.
 */
export function resolveConsoleTerminalState(input: {
  /** Classified platform read failure, if the governing read errored. */
  readFailure: BackendStatusDetail | null;
  /** Current liveness verdict from {@link useBackendStatus}. */
  backendStatus: BackendStatus;
  /** Whether a platform read has already produced data for this screen. */
  hasData: boolean;
}): BackendStatusDetail | null {
  const { readFailure, backendStatus, hasData } = input;
  if (readFailure) return readFailure;
  if (!hasData && backendStatus === 'unavailable') {
    return {
      status: 'unavailable',
      source: 'liveness',
      reason: 'Nothing is listening on the backend port.',
      timedOut: false,
      elapsedMs: 0,
    };
  }
  return null;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export interface UseBackendStatusOptions {
  /** Initial state. Defaults to `unknown` (pre-probe). */
  initial?: BackendStatus;
  /** Liveness deadline override, for tests. */
  livenessTimeoutMs?: number;
  /** Disable the initial + interval probes (tests, or a page that only wants the classifier). */
  enabled?: boolean;
  /** Background re-probe interval while not ready. */
  pollIntervalMs?: number;
}

/** Re-probe cadence while the backend is not yet confirmed serving. */
export const DEFAULT_POLL_INTERVAL_MS = 2_000;

/**
 * Probe liveness and hold the resulting state.
 *
 * This is the console's single source of "can I see the backend at all", which
 * is what lets a console page render a *named* state instead of a spinner. It
 * is cheap by construction: `GET /health` measured 3.8 ms and 17.3 ms, versus
 * 13.8–37.8 s for the first platform health build.
 *
 * Polling stops as soon as the backend is ready. A ready backend is not polled
 * by this hook — the console's data queries own their own refresh, and a
 * control room's liveness indicator that polls forever is a second, quieter
 * version of the same problem.
 */
export function useBackendStatus(options: UseBackendStatusOptions = {}) {
  const {
    initial = 'unknown',
    livenessTimeoutMs = LIVENESS_DEADLINE_MS,
    enabled = true,
    pollIntervalMs = DEFAULT_POLL_INTERVAL_MS,
  } = options;

  const [detail, setDetail] = useState<BackendStatusDetail>(() => ({
    status: initial,
    source: 'liveness',
    reason: 'The console has not probed the backend yet.',
    timedOut: false,
  }));
  const [lastProbedAt, setLastProbedAt] = useState<string | null>(null);
  const mounted = useRef(true);
  const ready = useRef(false);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const probe = useCallback(async () => {
    const startedAt = Date.now();
    const outcome = await fetchLiveness(livenessTimeoutMs);
    if (!mounted.current) return;
    const elapsedMs = Date.now() - startedAt;
    const next = classifyLiveness({ ...outcome, elapsedMs });
    ready.current = next.status === 'ready';
    setDetail(next);
    setLastProbedAt(new Date().toISOString());
  }, [livenessTimeoutMs]);

  useEffect(() => {
    if (!enabled) return;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let cancelled = false;

    const tick = async () => {
      await probe();
      if (cancelled || ready.current) return;
      timer = setTimeout(tick, pollIntervalMs);
    };

    void tick();
    return () => {
      cancelled = true;
      if (timer !== undefined) clearTimeout(timer);
    };
  }, [enabled, probe, pollIntervalMs]);

  return {
    ...detail,
    label: BACKEND_STATUS_LABEL[detail.status],
    short: BACKEND_STATUS_SHORT[detail.status],
    lastProbedAt,
    /** Force an immediate re-probe. Wired to the console's Retry control. */
    refresh: probe,
  };
}

export type UseBackendStatusReturn = ReturnType<typeof useBackendStatus>;
