/**
 * Canonical API Gateway Transport — M9-C37
 *
 * Single source of truth for every HTTP call the frontend makes to the backend.
 * All capability hooks, lib/hooks/*, and lib/api/client.ts route through here.
 * Zero per-entity special-casing. Zero double standards.
 *
 * Architecture:
 *   1. Deterministic upstream resolution: NEXT_PUBLIC_API_URL env var
 *      (default http://localhost:8000). Same value in CI and local.
 *   2. Error classification: transient (retryable) vs permanent (fatal).
 *      - Network errors (TypeError): transient
 *      - HTTP 5xx / 429: transient
 *      - HTTP 4xx (except 429): permanent — do NOT retry
 *   3. Semantic retry policy: only transient failures are retried, bounded
 *      to 3 attempts with fixed 1s delay. No magic numbers in individual
 *      components.
 *   4. No path normalization hacks. Absolute URLs bypass Next.js trailingSlash
 *      redirects and static-export proxy gaps entirely.
 *   5. Per-call deadlines (M11). `fetch` has no built-in timeout, so an
 *      unbounded request never rejects and the caller can only wait. Callers
 *      that need a deadline pass `timeoutMs`; the platform console passes
 *      `PLATFORM_API_DEADLINE_MS` for every `/platform/v1/*` read. Requests
 *      made without a deadline keep their previous behaviour — see
 *      `NO_DEADLINE` below for why that is a recorded gap, not an oversight.
 *
 * Usage:
 *   import { apiFetchJson, transientRetryPolicy } from '@/lib/api/gateway';
 *
 *   // In a React Query hook:
 *   const { data } = useQuery({
 *     queryKey: ['cards'],
 *     queryFn: () => apiFetchJson<CardSummary[]>('/api/v1/credit-cards'),
 *     retry: transientRetryPolicy,
 *   });
 */

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

/**
 * Canonical backend upstream. All API calls route here deterministically.
 * In production CI this points to the deployed backend; locally defaults to
 * the seeded sqlite-backed FastAPI server on :8000.
 *
 * M9-C37: Using absolute URLs avoids Next.js trailingSlash redirect (308)
 * entirely — every request goes straight to the backend via CORS.
 */
export const API_BACKEND_URL: string =
  typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL
    : 'http://localhost:8000';

/**
 * Base URL that keeps a request on the Next.js origin.
 *
 * M10-A3: a relative path passed to `apiFetch`/`apiFetchJson` is resolved
 * against `API_BACKEND_URL`, so a same-origin call to one of this app's own
 * route handlers (e.g. `/api/diagnostic-signatures`) would silently be sent to
 * the FastAPI backend, which has no such route. Passing this constant as
 * `baseUrl` yields a relative URL, which `fetch` resolves against the document
 * — the behaviour the caller actually asked for. It is named rather than passed
 * as a bare `''` so the intent survives review.
 */
export const SAME_ORIGIN_BASE_URL = '';

/**
 * Deadline applied to a request when the caller asks for a bounded one.
 *
 * `undefined` means "no deadline" and preserves the pre-M11 behaviour for
 * callers that do not opt in. That is a deliberate, recorded gap rather than
 * a neutral default: `fetch` without `AbortSignal` never rejects, so an
 * unbounded request renders an indefinite spinner instead of an error. The
 * platform console opts in everywhere (see `PLATFORM_API_DEADLINE_MS`), which
 * is where the defect was actually observed. Raising a deadline for the
 * financial API's non-platform paths requires measured worst-case latencies
 * for those paths, which this milestone has NOT measured; inventing a number
 * there would convert a visible stall into an invisible failure.
 */
export type Deadline = number | undefined;

// ---------------------------------------------------------------------------
// Deadlines (M11 — Platform Console cold-start readiness)
// ---------------------------------------------------------------------------

/**
 * Liveness probe deadline.
 *
 * `GET /health` is a constant-return handler (`backend/src/health.py:23`) and
 * measured 3.8–17.3 ms once the socket is serving, against 13.8–37.8 s for the
 * first `/platform/v1/health` and 53.8–118.6 s for a cold
 * `/platform/v1/evidence`. Three seconds is therefore ~170x the observed warm
 * cost, and a miss means the application is not serving yet rather than merely
 * slow.
 */
export const LIVENESS_DEADLINE_MS = 3_000;

/**
 * Deadline for a `/platform/v1/*` read that the console renders inline.
 *
 * Re-derived from GitHub-hosted runner measurements after M11 CI contradicted
 * the original local derivation.
 *
 * Local (contended development host):
 *   - warm (cache hit) platform reads 1.0–122 ms;
 *   - slowest cached read 5.4 s;
 *   - slowest uncached read 118.6 s.
 *
 * GitHub-hosted runner, M11 PR #17 (`ubuntu-latest`, cold application):
 *   - GET /platform/v1/health      200 in 43.8 s
 *   - GET /platform/v1/architecture/*  200 in 35.7 s (a batch, queued behind
 *     one blocking snapshot build on the event loop)
 *
 * The original 20 s value was derived from the local numbers and assumed the
 * uncached builds were pathological outliers worth reporting instead of waiting
 * out. CI shows they are not outliers — 43.8 s is what a healthy backend
 * actually takes on a cold runner. A deadline BELOW the endpoint's real service
 * time does not "report slowness", it manufactures a false failure: the console
 * declares a healthy backend's platform endpoint failed, and
 * `m10-agent3-console.spec.ts` can never observe the authority's real statuses,
 * which is the entire thing that test exists to verify.
 *
 * 60 s covers the measured CI ceiling (43.8 s) with ~1.4x margin for runner
 * contention. It is still a bounded, honest ceiling, not an indefinite wait:
 *
 *   - LIVENESS_DEADLINE_MS (3 s) keeps the transport verdict separate and fast,
 *     so "nothing is listening" and "the backend is booting" are distinguished
 *     within 3 s regardless of this value;
 *   - `starting` renders a labelled, retryable state rather than a bare
 *     spinner, and the shell-level status bar carries the verdict throughout;
 *   - a genuinely wedged endpoint is still reported — at 60 s, not never.
 *
 * Re-derive from measurement, not taste. If the platform handlers are ever made
 * to build off the event loop and the cold service time drops, this should fall
 * with it; the console spec's own 120 s budget is the upper bound that would
 * then need revisiting too.
 */
export const PLATFORM_API_DEADLINE_MS = 60_000;

// ---------------------------------------------------------------------------
// Error taxonomy
// ---------------------------------------------------------------------------

/**
 * Typed API error carrying the HTTP status so callers can distinguish
 * transient (retryable) from permanent (fatal) failures.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly transient: boolean;
  readonly body: string;
  /**
   * The request path that failed.
   *
   * M10-A3: previously only folded into `message`, so anything that wanted to
   * report WHICH request failed had to parse the message string back apart. The
   * platform console needs it to name the endpoint in its unavailable state.
   */
  readonly path: string;

  constructor(status: number, path: string, body: string = '') {
    super(`API ${status} ${path}`);
    this.name = 'ApiError';
    this.status = status;
    // 5xx and 429 are transient — the server may recover
    this.transient = status >= 500 || status === 429;
    this.body = body;
    this.path = path;
  }
}

/** True when the error indicates a recoverable transient failure. */
export function isTransientError(error: unknown): boolean {
  if (error instanceof ApiError) return error.transient;
  if (error instanceof ApiTimeoutError) return true;
  // fetch() TypeError = connection refused / DNS / abort: transient
  return error instanceof TypeError;
}

/**
 * Raised when a request exceeded its deadline.
 *
 * This is deliberately NOT an `ApiError`: an `ApiError` carries an HTTP status
 * the server produced, and a timeout means no response was produced at all.
 * The distinction matters to the console, which reports "the platform endpoint
 * did not answer" differently from "the platform endpoint answered with an
 * error" — the first is a cold-start symptom, the second is a defect.
 *
 * It is also the only positive evidence the browser has that the backend
 * accepted a connection and then failed to answer: a refused connection fails
 * with `TypeError` instead, so `ApiTimeoutError` is what distinguishes
 * "backend is starting" from "backend is not running".
 */
export class ApiTimeoutError extends Error {
  readonly path: string;
  readonly timeoutMs: number;

  constructor(path: string, timeoutMs: number) {
    super(`API timeout ${timeoutMs}ms ${path}`);
    this.name = 'ApiTimeoutError';
    this.path = path;
    this.timeoutMs = timeoutMs;
  }
}

/** True when the error is a deadline breach rather than a response failure. */
export function isTimeoutError(error: unknown): error is ApiTimeoutError {
  return error instanceof ApiTimeoutError;
}

/**
 * Semantic retry policy for React Query.
 * Retries ONLY transient failures (network, 5xx, 429), at most 3 attempts.
 * Permanent failures (4xx except 429) surface immediately — never masked.
 */
export const transientRetryPolicy = (failureCount: number, error: unknown): boolean =>
  isTransientError(error) && failureCount < 3;

// ---------------------------------------------------------------------------
// Transport
// ---------------------------------------------------------------------------

/**
 * Per-call transport options.
 *
 * Added as a fourth positional parameter rather than by extending
 * `RequestInit` so that a deadline can never be smuggled in as a bogus fetch
 * option, and so existing three-argument call sites are untouched.
 */
export interface ApiFetchOptions {
  /**
   * Milliseconds after which the request is aborted and `ApiTimeoutError` is
   * thrown. `undefined` (the default) means no deadline.
   */
  timeoutMs?: Deadline;
}

/**
 * Compose a caller-supplied signal with a deadline.
 *
 * A caller that already owns cancellation (an effect cleanup, a React Query
 * `signal`) keeps it: whichever fires first wins. The deadline is reported
 * separately from the caller's abort so a timeout is never mis-reported as a
 * cancelled request — the two mean opposite things to the console.
 */
function withDeadline(
  init: RequestInit | undefined,
  timeoutMs: Deadline,
): { signal: AbortSignal; timedOut: () => boolean; done: () => void } {
  const controller = new AbortController();
  let deadlineFired = false;
  let timer: ReturnType<typeof setTimeout> | undefined;

  const upstream = init?.signal ?? undefined;
  if (upstream) {
    if (upstream.aborted) {
      controller.abort(upstream.reason);
    } else {
      upstream.addEventListener(
        'abort',
        () => controller.abort(upstream.reason),
        { once: true },
      );
    }
  }

  if (typeof timeoutMs === 'number' && timeoutMs >= 0 && !upstream?.aborted) {
    timer = setTimeout(() => {
      deadlineFired = true;
      controller.abort();
    }, timeoutMs);
  }

  return {
    signal: controller.signal,
    timedOut: () => deadlineFired,
    done: () => {
      if (timer !== undefined) clearTimeout(timer);
    },
  };
}

/**
 * Canonical JSON fetch. Every backend request in the app goes through here.
 * @param path    Relative path against the backend root (e.g. '/api/v1/credit-cards').
 * @param init    Optional RequestInit overrides (headers, method, body).
 * @param options Optional deadline (see `ApiFetchOptions`).
 * @returns       Parsed JSON body, or throws ApiError on non-ok status /
 *                ApiTimeoutError on deadline breach.
 */
export async function apiFetchJson(
  path: string,
  init?: RequestInit,
  baseUrl?: string,
  options?: ApiFetchOptions,
): Promise<unknown> {
  const res = await apiFetch(path, init, baseUrl, options);
  return await res.json();
}

/**
 * Canonical fetch returning the raw Response. Callers that need headers,
 * stream processing, or non-JSON bodies should use this instead of raw fetch().
 */
export async function apiFetch(
  path: string,
  init?: RequestInit,
  baseUrl?: string,
  options?: ApiFetchOptions,
): Promise<Response> {
  // Always use absolute URL — bypasses Next.js trailingSlash redirect (308)
  const base = (typeof baseUrl !== 'undefined' ? baseUrl : API_BACKEND_URL).replace(/\/$/, '');
  const url = path.startsWith('http') ? path : `${base}${path}`;

  const timeoutMs = resolveDeadline(path, options);
  const deadline =
    typeof timeoutMs === 'number' ? withDeadline(init, timeoutMs) : undefined;

  let response: Response;
  try {
    response = await fetch(url, deadline ? { ...init, signal: deadline.signal } : init);
  } catch (err) {
    if (deadline?.timedOut()) {
      throw new ApiTimeoutError(path, timeoutMs as number);
    }
    throw err;
  } finally {
    deadline?.done();
  }

  if (!response.ok) {
    let body = '';
    try {
      body = await response.text();
    } catch { /* body may already be consumed */ }
    throw new ApiError(response.status, path, body);
  }
  return response;
}

// ---------------------------------------------------------------------------
// Platform Console transport (M11)
// ---------------------------------------------------------------------------

/** True when `path` targets the Platform API surface. */
export function isPlatformApiPath(path: string): boolean {
  return path.startsWith('/platform/v1/');
}

/**
 * React Query retry policy for Platform Console reads: no automatic retry.
 *
 * `transientRetryPolicy` retries up to 3 times, which is right for an
 * interactive financial surface and wrong here. Measured, a timed-out platform
 * read has already queued a heavy build behind the request that timed out: on a
 * cold 5-way burst, four requests issued in different milliseconds all returned
 * at the *same* instant (identical server-side `duration_ms=5405.8`), because
 * the platform handlers run synchronous builders on the event loop. Retrying
 * immediately therefore does not recover the read, it appends another request to
 * the same queue, and with a 20 s deadline the operator would wait 4 x 20 s
 * before being told anything.
 *
 * A control room must report a state, not perform speculative work. The retry
 * is the operator's explicit action (the console's Retry control), which is also
 * the only way to retry from a screen that is not focused.
 */
export const platformReadRetryPolicy = (): boolean => false;

/**
 * Same policy, typed for React Query's `retry` slot.
 *
 * React Query calls `retry(failureCount, error)`. A zero-parameter function is
 * assignable to that type, but writing the unused parameters out keeps the two
 * call sites honest: it is obvious that both inputs are deliberately ignored,
 * rather than looking like an oversight.
 */
export function platformReadRetry<TError = unknown>(
  _failureCount: number,
  _error: TError | null,
): boolean {
  return platformReadRetryPolicy();
}

/**
 * Resolve the deadline for one request.
 *
 * Precedence: explicit per-call option, then the Platform API default, then no
 * deadline. Applying the platform default by *path* rather than by call site is
 * deliberate — the console reaches `/platform/v1/*` from hooks, from page
 * components and from inline mutations, and an unbounded call site is exactly
 * how this defect survived. There is now no way to reach the platform API
 * without a deadline unless a caller passes `timeoutMs: undefined` explicitly.
 */
export function resolveDeadline(path: string, options?: ApiFetchOptions): Deadline {
  if (options && 'timeoutMs' in options) return options.timeoutMs;
  return isPlatformApiPath(path) ? PLATFORM_API_DEADLINE_MS : undefined;
}

/**
 * JSON fetch for a `/platform/v1/*` read.
 *
 * Equivalent to `apiFetchJson(path, init, baseUrl)` — which already applies
 * the platform deadline by path. Exists so a page that wants a different
 * deadline for one specific read says so at the call site instead of changing
 * the default for everything.
 */
export async function apiFetchPlatformJson(
  path: string,
  init?: RequestInit,
  baseUrl?: string,
  timeoutMs: Deadline = PLATFORM_API_DEADLINE_MS,
): Promise<unknown> {
  return await apiFetchJson(path, init, baseUrl, { timeoutMs });
}

/**
 * Fetch the backend's liveness probe (`GET /health`).
 *
 * This is the console's readiness signal and it is deliberately NOT a platform
 * endpoint. `GET /health` is a constant-return handler, so it answers in
 * single-digit milliseconds as soon as the application is serving — measured
 * 3.8 ms and 17.3 ms on two cold starts. That is what lets the console say
 * "backend ready" while the much more expensive platform data reads are still
 * building, instead of holding every page in one undifferentiated spinner.
 *
 * `GET /ready` is deliberately not used here: it is also fast (measured
 * 5.2–24.3 ms) but its 503 carries database/upload-directory semantics, and
 * "the database is unreachable" is a different verdict from "the application is
 * not serving yet".
 */
export async function fetchLiveness(
  timeoutMs: Deadline = LIVENESS_DEADLINE_MS,
): Promise<{ served: true; body: unknown } | { served: false; error: unknown }> {
  try {
    const body = await apiFetchJson('/health', undefined, undefined, { timeoutMs });
    return { served: true, body };
  } catch (error) {
    return { served: false, error };
  }
}

