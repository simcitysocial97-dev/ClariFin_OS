/**
 * Runtime clock — the single source of "now" for rendering.
 *
 * M10-R3 (L7). `generateSegments()` and `TimeRail` both read `new Date()` directly.
 * That made every financial route's footer bar — and its period labels — depend on the
 * moment the page was rendered, so a visual-regression baseline captured in January is
 * *guaranteed* to differ in March. Measured against the committed baselines' own
 * `MAX_DIFF_PIXELS = 500`: day drift alone was ~600-900 differing pixels and a month
 * rollover ~1100.
 *
 * The defect is architectural, not cosmetic: a component whose pixels depend on when it
 * rendered is not reproducible by construction, and no baseline policy fixes that.
 *
 * Two ways to pin the clock, in precedence order:
 *
 * 1. `setFixedNow(iso)` — programmatic, for unit tests and for a harness that wants to
 *    control it in-process.
 * 2. `?__now=2025-01-15` in the URL — survives a page reload, which is what a
 *    Playwright `page.goto()` needs. Injected as a query parameter rather than a
 *    `window` hook so the pinned value is visible in the URL a developer can paste into
 *    a bug report ("open the app as of this date").
 *
 * When nothing is pinned, `now()` returns the real clock: production behaviour is
 * unchanged, and only the *deliberate* pinning path exists.
 */

const FIXED_NOW_PARAM = '__now';

let _fixedNowMs: number | null = null;
let _resolvedFromUrl = false;

function readUrlOverride(): number | null {
  if (typeof window === 'undefined') return null;
  if (!_resolvedFromUrl) {
    _resolvedFromUrl = true;
    try {
      const raw = new URL(window.location.href).searchParams.get(FIXED_NOW_PARAM);
      if (raw) {
        const parsed = Date.parse(raw);
        // An unparseable value is ignored rather than silently becoming epoch: a
        // silently-wrong clock is the exact failure this module exists to remove.
        if (!Number.isNaN(parsed)) _fixedNowMs = parsed;
      }
    } catch {
      // A malformed URL is not a reason to break rendering.
    }
  }
  return _fixedNowMs;
}

/** The current time in ms. Honours a pin if one is set, else the real clock. */
export function now(): number {
  return readUrlOverride() ?? Date.now();
}

/** The current time as a Date. */
export function nowDate(): Date {
  return new Date(now());
}

/** Pin the clock. Pass `null` to release the pin and return to the real clock. */
export function setFixedNow(iso: string | number | Date | null): void {
  if (iso === null) {
    _fixedNowMs = null;
    _resolvedFromUrl = true;
    return;
  }
  const parsed = iso instanceof Date ? iso.getTime() : typeof iso === 'number' ? iso : Date.parse(iso);
  if (Number.isNaN(parsed)) {
    throw new TypeError(`setFixedNow: unparseable time ${String(iso)}`);
  }
  _fixedNowMs = parsed;
  _resolvedFromUrl = true;
}

/** Whether the clock is currently pinned. */
export function isClockPinned(): boolean {
  return readUrlOverride() !== null;
}