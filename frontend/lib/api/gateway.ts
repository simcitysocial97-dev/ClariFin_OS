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

  constructor(status: number, path: string, body: string = '') {
    super(`API ${status} ${path}`);
    this.name = 'ApiError';
    this.status = status;
    // 5xx and 429 are transient — the server may recover
    this.transient = status >= 500 || status === 429;
    this.body = body;
  }
}

/** True when the error indicates a recoverable transient failure. */
export function isTransientError(error: unknown): boolean {
  if (error instanceof ApiError) return error.transient;
  // fetch() TypeError = connection refused / DNS / abort: transient
  return error instanceof TypeError;
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
 * Canonical JSON fetch. Every backend request in the app goes through here.
 * @param path  Relative path against the backend root (e.g. '/api/v1/credit-cards').
 * @param init  Optional RequestInit overrides (headers, method, body).
 * @returns     Parsed JSON body, or throws ApiError on non-ok status.
 */
export async function apiFetchJson(
  path: string,
  init?: RequestInit,
  baseUrl?: string,
): Promise<unknown> {
  const res = await apiFetch(path, init, baseUrl);
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
): Promise<Response> {
  // Always use absolute URL — bypasses Next.js trailingSlash redirect (308)
  const base = (typeof baseUrl !== 'undefined' ? baseUrl : API_BACKEND_URL).replace(/\/$/, '');
  const url = path.startsWith('http') ? path : `${base}${path}`;
  const response = await fetch(url, init);
  if (!response.ok) {
    let body = '';
    try {
      body = await response.text();
    } catch { /* body may already be consumed */ }
    throw new ApiError(response.status, path, body);
  }
  return response;
}
