/**
 * M11 — Platform Console backend-state classifier
 * ================================================
 *
 * The console's entire M11 deliverable is a single question answered four ways:
 * can the console see the backend, and if not, what should the operator DO?
 *
 *   unavailable      -> start or restart the backend
 *   starting         -> WAIT; restarting discards the warm-up
 *   ready            -> the application is serving
 *   endpoint-failed  -> the process is fine, the endpoint is not
 *
 * Getting this wrong is not cosmetic. Before M11 the console collapsed every
 * failure into "DEGRADED / API UNAVAILABLE", so an operator watching a backend
 * that was 40 s into importing `camelot`, `cv2` and `pandas` was told the API
 * was unavailable — the one message that invites a restart, at the exact moment
 * a restart is most expensive.
 *
 * These tests pin the classification logic against the error shapes the
 * transport actually produces, so the four states cannot collapse back into one.
 * The rendering is covered separately by the Playwright console specs; this file
 * covers the decision, which is the part with no UI to fail loudly.
 */

import { describe, expect, it } from 'vitest';
import { ApiError, ApiTimeoutError } from '@/lib/api/gateway';
import {
  BACKEND_STATUS_LABEL,
  BACKEND_STATUS_SHORT,
  classifyLiveness,
  classifyPlatformRead,
  resolveConsoleTerminalState,
  type BackendStatus,
} from '@/lib/platform/backend-status';

const REFUSED = new TypeError('Failed to fetch');
const ABORTED = Object.assign(new Error('The operation was aborted.'), {
  name: 'AbortError',
});

describe('console backend states — liveness probe (GET /health)', () => {
  it('reports ready when the application answers', () => {
    const detail = classifyLiveness({ served: true, elapsedMs: 4 });
    expect(detail.status).toBe('ready');
    expect(detail.timedOut).toBe(false);
    expect(detail.elapsedMs).toBe(4);
  });

  it('reports starting — not unavailable — when the connection was accepted but silent', () => {
    // The decisive case. A timeout is the ONLY positive evidence the browser has
    // that something accepted the TCP connection.
    const detail = classifyLiveness({
      served: false,
      error: new ApiTimeoutError('/health', 3_000),
      elapsedMs: 3_000,
    });
    expect(detail.status).toBe('starting');
    expect(detail.timedOut).toBe(true);
    expect(detail.reason).toContain('still starting up');
  });

  it('reports unavailable when nothing is listening', () => {
    const detail = classifyLiveness({ served: false, error: REFUSED });
    expect(detail.status).toBe('unavailable');
    expect(detail.timedOut).toBe(false);
    // The reason must name EVERY cause that produces this verdict: during the
    // import window the port is genuinely not bound, so "not running" alone
    // would be a false statement; and `fetch` reports a cross-origin rejection
    // as the same TypeError, so a CORS misconfiguration must be nameable or an
    // operator will restart a healthy backend.
    expect(detail.reason).toMatch(/not running/i);
    expect(detail.reason).toMatch(/importing/i);
    expect(detail.reason).toMatch(/CORS/i);
  });

  it('treats a caller abort as a transport failure, not as a starting backend', () => {
    // An abort is something the *page* did. Reporting "starting" here would let
    // a component unmount masquerade as a booting backend.
    expect(classifyLiveness({ served: false, error: ABORTED }).status).toBe('unavailable');
  });

  it('reports starting when the app answers the liveness probe with a non-2xx', () => {
    // The socket is open and the app responded, so it is up but not serving.
    const detail = classifyLiveness({
      served: false,
      error: new ApiError(503, '/health', '{"status":"not_ready"}'),
    });
    expect(detail.status).toBe('starting');
    expect(detail.httpStatus).toBe(503);
  });
});

describe('console backend states — platform read (/platform/v1/*)', () => {
  it('reports starting for a timeout while the backend is not yet confirmed', () => {
    const detail = classifyPlatformRead(
      { error: new ApiTimeoutError('/platform/v1/health', 20_000), path: '/platform/v1/health' },
      false,
    );
    expect(detail.status).toBe('starting');
    expect(detail.timedOut).toBe(true);
    expect(detail.reason).toContain('/platform/v1/health');
  });

  it('reports endpoint-failed for the SAME timeout once the backend is healthy', () => {
    // This is the pair that matters most. Identical transport evidence, opposite
    // operator action, and the only thing that separates them is whether the
    // fast liveness probe already answered.
    const detail = classifyPlatformRead(
      { error: new ApiTimeoutError('/platform/v1/health', 20_000), path: '/platform/v1/health' },
      true,
    );
    expect(detail.status).toBe('endpoint-failed');
    expect(detail.timedOut).toBe(true);
    expect(detail.reason).toMatch(/stalled/i);
  });

  it('reports endpoint-failed for an HTTP error after the backend is healthy', () => {
    const detail = classifyPlatformRead(
      { error: new ApiError(500, '/platform/v1/evidence', 'boom'), path: '/platform/v1/evidence' },
      true,
    );
    expect(detail.status).toBe('endpoint-failed');
    expect(detail.httpStatus).toBe(500);
    expect(detail.reason).not.toMatch(/still starting/i);
  });

  it('reports starting for an HTTP error before the backend is confirmed', () => {
    const detail = classifyPlatformRead(
      { error: new ApiError(500, '/platform/v1/health', 'boom'), path: '/platform/v1/health' },
      false,
    );
    expect(detail.status).toBe('starting');
  });

  it('reports unavailable when a platform read cannot reach the backend at all', () => {
    const detail = classifyPlatformRead({ error: REFUSED, path: '/platform/v1/tasks' }, false);
    expect(detail.status).toBe('unavailable');
    expect(detail.reason).toContain('/platform/v1/tasks');
  });

  it('never claims a health verdict of its own', () => {
    // Architecture authority: the console reports transport state, never health.
    // A classifier that emitted HEALTHY/UNHEALTHY would be inventing a verdict
    // the backend owns.
    const verdicts: BackendStatus[] = [
      classifyLiveness({ served: true }).status,
      classifyLiveness({ served: false, error: REFUSED }).status,
      classifyLiveness({ served: false, error: new ApiTimeoutError('/health', 1) }).status,
      classifyPlatformRead({ error: new ApiError(500, '/p', '') }, true).status,
    ];
    for (const v of verdicts) {
      expect(v).not.toBe('HEALTHY' as BackendStatus);
      expect(v).not.toBe('UNHEALTHY' as BackendStatus);
    }
  });
});

describe('console backend states — vocabulary', () => {
  it('gives every state a distinct operator label', () => {
    const labels = Object.values(BACKEND_STATUS_LABEL);
    expect(new Set(labels).size).toBe(labels.length);
    // The three non-ready states must not read alike; an operator has to be able
    // to tell WAIT from ACT from the badge alone.
    expect(BACKEND_STATUS_LABEL.starting).not.toBe(BACKEND_STATUS_LABEL.unavailable);
    expect(BACKEND_STATUS_LABEL['endpoint-failed']).not.toBe(BACKEND_STATUS_LABEL.unavailable);
    expect(BACKEND_STATUS_LABEL.ready).not.toBe(BACKEND_STATUS_LABEL.starting);
  });

  it('gives every state a distinct short form for the status strip', () => {
    const shorts = Object.values(BACKEND_STATUS_SHORT);
    expect(new Set(shorts).size).toBe(shorts.length);
  });
});

/**
 * The terminal-state gate every platform screen applies before rendering its
 * dashboard.
 *
 * REGRESSION. The first implementation inlined
 * `backend.status === 'unavailable' || backend.status === 'starting'` as the
 * terminal condition. That made `starting` terminal, and on CI it broke a
 * console spec outright: during a cold start `GET /health` exceeds the 3 s
 * LIVENESS deadline while the application is still importing `camelot`, `cv2`
 * and `pandas`, so the screen rendered the terminal panel and the health
 * dimensions grid never appeared.
 *
 * Two independent faults, both pinned below:
 *   - `starting` must never be terminal, because "the backend is booting" is a
 *     WAIT condition, not an ACT condition.
 *   - data that has already landed must always win over a 3 s liveness opinion.
 */
describe('resolveConsoleTerminalState', () => {
  const terminal = (over: Partial<Parameters<typeof resolveConsoleTerminalState>[0]> = {}) =>
    resolveConsoleTerminalState({
      readFailure: null,
      backendStatus: 'unknown' as BackendStatus,
      hasData: false,
      ...over,
    });

  it('never treats a starting backend as terminal', () => {
    // The regression. Cold start, nothing read yet: the screen must fall through
    // to the loading state, which carries the "wait, do not restart" copy.
    expect(terminal({ backendStatus: 'starting' })).toBeNull();
  });

  it('reports nothing-listening as terminal even before any read fails', () => {
    const verdict = terminal({ backendStatus: 'unavailable' });
    expect(verdict?.status).toBe('unavailable');
    expect(verdict?.source).toBe('liveness');
  });

  it('lets real data win over a starting or unavailable verdict', () => {
    // A read landed, so the dashboard is correct to render. The liveness probe
    // is a 3 s opinion; the read is the authority.
    expect(terminal({ backendStatus: 'starting', hasData: true })).toBeNull();
    expect(terminal({ backendStatus: 'unavailable', hasData: true })).toBeNull();
  });

  it('passes a classified read failure straight through', () => {
    const failure = classifyPlatformRead({ error: new ApiTimeoutError('/platform/v1/health', 20_000), path: '/platform/v1/health' }, false);
    expect(terminal({ readFailure: failure, backendStatus: 'ready', hasData: true })).toBe(failure);
  });

  it('still returns null while a healthy backend has simply not answered yet', () => {
    expect(terminal({ backendStatus: 'ready' })).toBeNull();
    expect(terminal({ backendStatus: 'unknown' })).toBeNull();
  });
});
