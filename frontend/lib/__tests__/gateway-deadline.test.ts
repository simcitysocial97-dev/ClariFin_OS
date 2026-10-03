/**
 * M11 — Gateway deadline regression
 * =================================
 *
 * The defect: `lib/api/gateway.ts` called `fetch(url, init)` with no
 * `AbortSignal`, so no request could ever reject for taking too long. M10
 * measured the consequence on a cold start — the first `/platform/v1/health` at
 * 39 s and a console request batch at 117 s — and the console rendered an
 * indefinite "Loading…" for the whole of it.
 *
 * These tests pin the properties that fix that, and they are written against
 * behaviour rather than implementation so a refactor of `withDeadline` cannot
 * silently reintroduce an unbounded platform read:
 *
 *   1. a bounded request that does not answer REJECTS (it does not hang);
 *   2. the rejection is distinguishable from every other failure, so the console
 *      can tell "accepted but silent" from "not listening" from "answered with
 *      an error" — that distinction is the whole M11 operator-facing fix;
 *   3. no path can reach the Platform API without a deadline;
 *   4. a caller's own cancellation still works and is NOT reported as a timeout;
 *   5. a caller's own signal still wins when it aborts first;
 *   6. non-platform paths keep their pre-M11 (unbounded) behaviour, which is the
 *      recorded gap this milestone deliberately did not close.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  ApiError,
  ApiTimeoutError,
  LIVENESS_DEADLINE_MS,
  PLATFORM_API_DEADLINE_MS,
  apiFetch,
  apiFetchJson,
  isPlatformApiPath,
  isTimeoutError,
  isTransientError,
  platformReadRetry,
  resolveDeadline,
  transientRetryPolicy,
} from '@/lib/api/gateway';

/** A fetch that never settles, so only an abort can end it. */
function neverResolving() {
  return (_url: string, init?: RequestInit) =>
    new Promise<Response>((_resolve, reject) => {
      // A signal that is ALREADY aborted never fires another `abort` event, so
      // the already-aborted case has to be handled before waiting for one.
      if (init?.signal?.aborted) {
        const err = new Error('The operation was aborted.');
        err.name = 'AbortError';
        reject(err);
        return;
      }
      init?.signal?.addEventListener('abort', () => {
        const err = new Error('The operation was aborted.');
        err.name = 'AbortError';
        reject(err);
      });
    });
}

function jsonResponse(status: number, body: unknown = {}) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as unknown as Response;
}

describe('gateway deadlines (M11)', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  // --- 1. a bounded request that does not answer REJECTS --------------------

  it('rejects a platform read that never answers, instead of hanging', async () => {
    fetchMock.mockImplementation(neverResolving());
    const pending = apiFetchJson('/platform/v1/health', undefined, undefined, {
      timeoutMs: 40,
    });
    const error = await pending.then(
      () => null,
      (e: unknown) => e,
    );
    expect(error).toBeInstanceOf(ApiTimeoutError);
    expect((error as ApiTimeoutError).path).toBe('/platform/v1/health');
    expect((error as ApiTimeoutError).timeoutMs).toBe(40);
  });

  // --- 2. the rejection is distinguishable ---------------------------------

  it('separates a deadline breach from a refused connection and from an error response', async () => {
    // (a) deadline breach
    fetchMock.mockImplementation(neverResolving());
    const timedOut = await apiFetchJson('/platform/v1/health', undefined, undefined, {
      timeoutMs: 40,
    }).catch((e: unknown) => e);
    expect(isTimeoutError(timedOut)).toBe(true);
    expect(timedOut).not.toBeInstanceOf(ApiError);

    // (b) connection refused — what fetch() raises when nothing is listening
    fetchMock.mockImplementation(() => Promise.reject(new TypeError('Failed to fetch')));
    const refused = await apiFetchJson('/platform/v1/health', undefined, undefined, {
      timeoutMs: 40,
    }).catch((e: unknown) => e);
    expect(isTimeoutError(refused)).toBe(false);
    expect(isTransientError(refused)).toBe(true);

    // (c) the server answered with an HTTP error
    fetchMock.mockResolvedValue(jsonResponse(500, { detail: 'boom' }));
    const serverError = await apiFetchJson('/platform/v1/health', undefined, undefined, {
      timeoutMs: 40,
    }).catch((e: unknown) => e);
    expect(serverError).toBeInstanceOf(ApiError);
    expect((serverError as ApiError).status).toBe(500);
    expect(isTimeoutError(serverError)).toBe(false);
  });

  it('treats a deadline breach as transient so the caller can choose to retry', () => {
    expect(isTransientError(new ApiTimeoutError('/platform/v1/health', 20_000))).toBe(true);
  });

  // --- 3. no platform path is reachable without a deadline ------------------

  it('gives every Platform API path the platform deadline by default', () => {
    for (const path of [
      '/platform/v1/health',
      '/platform/v1/errors/current',
      '/platform/v1/evidence',
      '/platform/v1/history/runs/abc',
      '/platform/v1/executions/xyz',
    ]) {
      expect(isPlatformApiPath(path)).toBe(true);
      expect(resolveDeadline(path)).toBe(PLATFORM_API_DEADLINE_MS);
    }
  });

  it('applies the platform deadline even when the caller does not ask for one', async () => {
    // Fake time so the real 20 s default can elapse without a 20 s test.
    vi.useFakeTimers();
    try {
      fetchMock.mockImplementation(neverResolving());
      // No options at all: this is the call shape every platform hook used.
      const pending = apiFetchJson('/platform/v1/tasks').catch((e: unknown) => e);
      await vi.advanceTimersByTimeAsync(PLATFORM_API_DEADLINE_MS + 5);
      const error = await pending;
      expect(error).toBeInstanceOf(ApiTimeoutError);
      expect((error as ApiTimeoutError).timeoutMs).toBe(PLATFORM_API_DEADLINE_MS);
    } finally {
      vi.useRealTimers();
    }
  });

  it('passes the platform deadline to fetch as a real AbortSignal', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { ok: true }));
    await apiFetchJson('/platform/v1/health');
    const [, init] = fetchMock.mock.calls[0];
    expect(init?.signal).toBeInstanceOf(AbortSignal);
  });

  it('honours a caller-supplied deadline for a platform path', () => {
    expect(resolveDeadline('/platform/v1/health', { timeoutMs: 1234 })).toBe(1234);
    // Explicit opt-out is the only way to reach the platform API unbounded.
    expect(resolveDeadline('/platform/v1/health', { timeoutMs: undefined })).toBeUndefined();
  });

  // --- 4/5. caller cancellation is preserved and never mislabelled ---------

  it('does not report a caller abort as a timeout', async () => {
    const controller = new AbortController();
    fetchMock.mockImplementation(neverResolving());
    const pending = apiFetchJson(
      '/platform/v1/health',
      { signal: controller.signal },
      undefined,
      { timeoutMs: 5_000 },
    );
    controller.abort();
    const error = await pending.catch((e: unknown) => e);
    // The deadline never fired, so the caller owns this failure.
    expect(isTimeoutError(error)).toBe(false);
    expect((error as Error).name).toBe('AbortError');
  });

  it('lets a caller abort win over a longer deadline', async () => {
    const controller = new AbortController();
    fetchMock.mockImplementation(neverResolving());
    const pending = apiFetch(
      '/platform/v1/evidence',
      { signal: controller.signal },
      undefined,
      { timeoutMs: 60_000 },
    );
    controller.abort();
    const error = await pending.catch((e: unknown) => e);
    // The deadline never fired, so this must NOT be a timeout.
    expect(isTimeoutError(error)).toBe(false);
  });

  it('honours a signal that is already aborted before the request starts', async () => {
    const controller = new AbortController();
    controller.abort();
    fetchMock.mockImplementation(neverResolving());
    const error = await apiFetchJson(
      '/platform/v1/health',
      { signal: controller.signal },
      undefined,
      { timeoutMs: 60_000 },
    ).catch((e: unknown) => e);
    expect(isTimeoutError(error)).toBe(false);
  });

  // --- 6. the recorded gap, pinned so it cannot drift silently -------------

  it('leaves non-platform paths unbounded — the recorded, unmeasured gap', () => {
    // Not an endorsement. This is asserted so that closing the gap later is a
    // visible, deliberate change rather than an accident, and so that anyone
    // reading the code sees that it is still open.
    expect(resolveDeadline('/api/v1/members')).toBeUndefined();
    expect(resolveDeadline('/api/v1/forecast')).toBeUndefined();
  });

  it('still issues a non-platform request with no signal when no deadline is set', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, []));
    await apiFetchJson('/api/v1/members');
    const [, init] = fetchMock.mock.calls[0];
    expect(init?.signal).toBeUndefined();
  });

  // --- policy -------------------------------------------------------------

  it('does not auto-retry platform reads, but still retries transient financial failures', () => {
    // Platform: no automatic retry. Measured justification is in the gateway
    // docstring — a cold 5-way burst had four requests issued in different
    // milliseconds return at the same instant, so a retry joins a queue.
    expect(platformReadRetry(0, new ApiTimeoutError('/platform/v1/health', 20_000))).toBe(false);
    expect(platformReadRetry(2, new TypeError('Failed to fetch'))).toBe(false);
    // Even the "always retryable" classes get no platform retry: a server error
    // on a platform read is a defect to surface, not to paper over.
    expect(platformReadRetry(0, new ApiError(503, '/platform/v1/health', ''))).toBe(false);
    expect(platformReadRetry(0, null)).toBe(false);

    // Financial: unchanged pre-M11 behaviour, still bounded to 3 attempts.
    expect(transientRetryPolicy(0, new TypeError('Failed to fetch'))).toBe(true);
    expect(transientRetryPolicy(2, new TypeError('Failed to fetch'))).toBe(true);
    expect(transientRetryPolicy(3, new TypeError('Failed to fetch'))).toBe(false);
  });

  it('sizes the liveness probe against the measured cost of /health', () => {
    // GET /health measured 3.8 ms and 17.3 ms once serving. The probe must be
    // far above that and far below any platform read, or it cannot be used to
    // distinguish "not serving" from "still building".
    expect(LIVENESS_DEADLINE_MS).toBeGreaterThan(1000);
    expect(LIVENESS_DEADLINE_MS).toBeLessThan(PLATFORM_API_DEADLINE_MS / 4);
  });
});
