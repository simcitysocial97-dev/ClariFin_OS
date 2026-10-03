/**
 * Operator-facing error description — M10-A3
 *
 * The console renders whatever the canonical gateway throws, and the gateway
 * throws `ApiError`, whose own `message` is the terse `API <status> <path>`.
 * `String(error)` on an `ApiError` yields the stringified *object* — status,
 * transient flag, and the full escaped response body — so screens that used it
 * directly showed an operator a wall of raw JSON instead of a sentence.
 *
 * The platform API returns a structured error envelope
 * (`runtime.platform.api.envelope.error_envelope`) carrying
 * `error.code`, `error.layer` and `error.message`. That envelope is the
 * authority's own explanation of the failure, so it is what an operator should
 * read. This helper unwraps it, falling back to the transport-level message
 * when the body is not an envelope (a proxy error page, an empty 502, ...).
 *
 * It never invents a diagnosis: the text is the backend's own message, and the
 * layer/code identify which authority produced it.
 */

import { ApiError } from './gateway';

interface PlatformErrorEnvelope {
  kind?: string;
  error?: {
    code?: string;
    layer?: string;
    message?: string;
  };
}

/**
 * Turn a thrown value into a single operator-readable line.
 * Never throws; never returns the raw serialised error object.
 */
export function describeError(error: unknown): string {
  if (error === null || error === undefined) return 'No error detail available.';

  if (error instanceof ApiError) {
    const envelope = parseEnvelope(error.body);
    const parts: string[] = [];
    if (envelope?.error?.message) parts.push(envelope.error.message);
    if (envelope?.error?.code) parts.push(`[${envelope.error.code}]`);
    if (envelope?.error?.layer) parts.push(`via ${envelope.error.layer}`);
    if (parts.length > 0) return `${parts.join(' ')} (HTTP ${error.status})`;
    return `HTTP ${error.status} from ${error.path ?? 'the platform API'}`;
  }

  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  return 'Unrecognised error value.';
}

function parseEnvelope(body: string): PlatformErrorEnvelope | null {
  if (!body) return null;
  try {
    const parsed: unknown = JSON.parse(body);
    if (parsed && typeof parsed === 'object' && 'error' in parsed) {
      return parsed as PlatformErrorEnvelope;
    }
  } catch {
    // Not JSON (proxy/HTML error page) — fall through to the transport message.
  }
  return null;
}
