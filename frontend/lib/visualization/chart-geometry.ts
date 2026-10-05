/**
 * Chart Geometry - finite-only projection into an SVG viewport.
 *
 * Why this exists
 * ---------------
 * The forecast charts emitted `NaN` geometry and the browser rejected it:
 *
 *   Error: <path> attribute d: Expected number, "M 10,NaN 44.545454545..."
 *   Error: <polyline> attribute points: Expected number, "10,NaN 44.54545..."
 *
 * Three independent causes, all of which the arithmetic below makes impossible:
 *
 *   1. A single data point. `i / (projections.length - 1)` is `0 / 0` = `NaN`
 *      when the series has exactly one entry.
 *   2. A zero range. `maxValue - minValue` is `0` when every value is
 *      identical (an all-zero series, or a flat one), so `(v - min) / range`
 *      is `0 / 0` = `NaN`.
 *   3. Non-finite input. A backend value that is `null`, `undefined`, a string,
 *      `NaN` or `Infinity` propagates straight into the path.
 *
 * The contract here is TOTAL: every function returns finite numbers for every
 * input, including empty arrays, single points, zero ranges and non-numeric
 * fields. Non-numeric or non-finite samples are REJECTED and reported, never
 * coerced into a plausible-looking number — an invalid backend value must not
 * silently become fabricated geometry.
 */

/** A sample that survived validation and can be drawn. */
export interface FiniteSample {
  /** Index within the accepted subset, so keys stay stable after rejection. */
  index: number;
  /** Horizontal position in SVG user units. Always finite. */
  x: number;
  /** Vertical position in SVG user units. Always finite. */
  y: number;
  /** The validated value the position was computed from. */
  value: number;
}

/** Why a sample could not be drawn. */
export type RejectedReason = 'not-finite' | 'not-a-number';

/** A sample that was dropped, and why. */
export interface RejectedSample {
  /** Index within the ORIGINAL series, so the caller can point at it. */
  index: number;
  reason: RejectedReason;
  /** The value as received, for the rejection report. */
  received: unknown;
}

/** Result of projecting a series into a viewport. */
export interface ProjectionResult {
  /** Samples that can be drawn. Finite by construction. */
  samples: FiniteSample[];
  /** Samples that were dropped, in original order. */
  rejected: RejectedSample[];
  /** True when nothing survived validation. */
  isEmpty: boolean;
  /** True when exactly one sample survived, so a line would be undefined. */
  isSinglePoint: boolean;
  /** The measured value range actually used, or null when nothing was drawn. */
  valueRange: { min: number; max: number } | null;
  /** Whether the range was zero and every sample was placed on one level. */
  isDegenerateRange: boolean;
}

/** Default plot area, matching the viewBox the forecast charts use. */
export interface Viewport {
  width: number;
  height: number;
  /** Inset from the left edge. */
  paddingLeft: number;
  /** Inset from the right edge. */
  paddingRight: number;
  /** Inset from the top edge. */
  paddingTop: number;
  /** Inset from the bottom edge. */
  paddingBottom: number;
}

export const DEFAULT_VIEWPORT: Viewport = {
  width: 400,
  height: 180,
  paddingLeft: 10,
  paddingRight: 10,
  paddingTop: 30,
  paddingBottom: 30,
};

/**
 * Classify a sample value.
 *
 * @returns null when the value is usable, otherwise the rejection reason.
 */
export function classifySample(value: unknown): RejectedReason | null {
  if (typeof value !== 'number') return 'not-a-number';
  if (!Number.isFinite(value)) return 'not-finite';
  return null;
}

/**
 * Project a series of values into SVG coordinates.
 *
 * Guarantees, for every input including the empty array:
 *   - every returned `x` and `y` is a finite number;
 *   - no division by zero occurs (a zero range collapses to the vertical
 *     centre of the plot area rather than producing `NaN`);
 *   - a single sample is placed at the horizontal centre;
 *   - non-numeric or non-finite samples are reported in `rejected`, not drawn.
 *
 * @param values Raw sample values, as received. May contain anything.
 * @param viewport Plot area in SVG user units.
 */
export function projectSeries(
  values: readonly unknown[],
  viewport: Viewport = DEFAULT_VIEWPORT
): ProjectionResult {
  const rejected: RejectedSample[] = [];
  const accepted: { index: number; value: number }[] = [];

  values.forEach((value, index) => {
    const reason = classifySample(value);
    if (reason) {
      rejected.push({ index, reason, received: value });
      return;
    }
    accepted.push({ index, value: value as number });
  });

  const plotWidth = viewport.width - viewport.paddingLeft - viewport.paddingRight;
  const plotHeight = viewport.height - viewport.paddingTop - viewport.paddingBottom;

  if (accepted.length === 0) {
    return {
      samples: [],
      rejected,
      isEmpty: true,
      isSinglePoint: false,
      valueRange: null,
      isDegenerateRange: false,
    };
  }

  const min = Math.min(...accepted.map((s) => s.value));
  const max = Math.max(...accepted.map((s) => s.value));
  const range = max - min;
  const isDegenerateRange = range === 0;

  // Guard the denominators rather than trusting the inputs. `count - 1` is 0
  // for a single sample and `range` is 0 for a flat series; both are the exact
  // conditions that produced `NaN` before.
  const lastIndex = accepted.length - 1;
  const horizontalDenominator = lastIndex === 0 ? 1 : lastIndex;

  const samples: FiniteSample[] = accepted.map((sample, i) => {
    const x =
      viewport.paddingLeft +
      (plotWidth * i) / horizontalDenominator;
    const y = isDegenerateRange
      ? viewport.paddingTop + plotHeight / 2
      : viewport.paddingTop + plotHeight * (1 - (sample.value - min) / range);
    return {
      index: sample.index,
      // Round so the emitted attribute string cannot carry a float artefact
      // that a strict SVG parser would reject.
      x: Math.round(x * 100) / 100,
      y: Math.round(y * 100) / 100,
      value: sample.value,
    };
  });

  return {
    samples,
    rejected,
    isEmpty: false,
    isSinglePoint: samples.length === 1,
    valueRange: { min, max },
    isDegenerateRange,
  };
}

/**
 * Render samples as an SVG polyline `points` string.
 *
 * Returns an empty string when fewer than two samples exist: a polyline needs
 * two points to have a segment, and emitting a one-point `points` produces
 * exactly the parser warning this module exists to prevent.
 */
export function toPolylinePoints(samples: readonly FiniteSample[]): string {
  if (samples.length < 2) return '';
  return samples.map((s) => `${s.x},${s.y}`).join(' ');
}

/**
 * Render samples as an SVG path `d` string.
 *
 * Returns an empty string when fewer than two samples exist.
 */
export function toPathData(samples: readonly FiniteSample[]): string {
  if (samples.length < 2) return '';
  return `M ${samples.map((s) => `${s.x},${s.y}`).join(' L ')}`;
}

/**
 * Whether a rendered SVG geometry string can be parsed.
 *
 * Used as a regression tripwire: an attribute carrying `NaN`, `undefined` or
 * `Infinity` fails this, so a test can assert on the rendered output rather
 * than on the arithmetic that produced it.
 */
export function isParseableGeometry(value: string): boolean {
  if (value.length === 0) return true;
  const numbers = value.match(/-?\d+(\.\d+)?/g);
  if (!numbers) return false;
  return !/NaN|Infinity|undefined|null/i.test(value);
}

/** A short, human-readable rejection report for the UI. */
export function describeRejections(rejected: readonly RejectedSample[]): string {
  if (rejected.length === 0) return '';
  const notNumbers = rejected.filter((r) => r.reason === 'not-a-number').length;
  const notFinite = rejected.filter((r) => r.reason === 'not-finite').length;
  const parts: string[] = [];
  if (notNumbers > 0) parts.push(`${notNumbers} non-numeric`);
  if (notFinite > 0) parts.push(`${notFinite} non-finite`);
  return parts.join(' and ');
}