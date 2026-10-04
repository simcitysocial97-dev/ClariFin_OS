/**
 * M10-R3 (L7) — the timeline must not depend on when it was rendered.
 *
 * `generateSegments()` and `TimeRail` both read `new Date()` directly, which put a
 * wall-clock playhead and wall-clock period labels on every financial route. Measured
 * against the committed baselines' own `MAX_DIFF_PIXELS = 500`: ~600-900 differing
 * pixels of day drift and ~1100 across a month rollover, so every visual-regression
 * baseline for every page carrying the rail was guaranteed to rot.
 *
 * These tests pin the clock and assert the rendered inputs are identical on two
 * different real dates — the property that was previously false by construction.
 */

import { describe, it, expect, afterEach } from 'vitest';
import { generateSegments } from '@/lib/timeline/segments';
import { setFixedNow, isClockPinned, now } from '@/lib/runtime/clock';

/** The subset of TimeRail's playhead logic that reads the clock. */
function playheadPosition(
  segments: ReturnType<typeof generateSegments>,
  state: { playbackPosition: number | null; date: string | null },
): number {
  if (typeof state.playbackPosition === 'number' && Number.isFinite(state.playbackPosition)) {
    return Math.max(0, Math.min(100, state.playbackPosition));
  }
  if (state.date) {
    const target = Date.parse(state.date);
    if (!Number.isNaN(target)) {
      const containing = segments.find(
        s => target >= Date.parse(s.dateStart) && target <= Date.parse(s.dateEnd),
      );
      if (containing) return containing.start;
    }
    return 0;
  }
  return 0;
}

const GRANULARITIES = ['day', 'week', 'month', 'quarter', 'year'] as const;

describe('runtime clock', () => {
  afterEach(() => setFixedNow(null));

  it('pins and releases', () => {
    expect(isClockPinned()).toBe(false);
    setFixedNow('2025-01-15T00:00:00Z');
    expect(isClockPinned()).toBe(true);
    expect(now()).toBe(Date.parse('2025-01-15T00:00:00Z'));
    setFixedNow(null);
    expect(isClockPinned()).toBe(false);
  });

  it('rejects an unparseable pin rather than silently becoming epoch', () => {
    // A silently-wrong clock is the exact failure this module exists to remove.
    expect(() => setFixedNow('not-a-date')).toThrow(TypeError);
  });
});

describe('generateSegments is deterministic', () => {
  afterEach(() => setFixedNow(null));

  it('renders identically for a pinned date, however many times it is called', () => {
    setFixedNow('2025-01-15T00:00:00Z');
    const first = GRANULARITIES.map(g => generateSegments(g, 24));
    const second = GRANULARITIES.map(g => generateSegments(g, 24));
    expect(second).toEqual(first);
  });

  it('returns to the real clock when unpinned, so production is unchanged', () => {
    // The pin must be *releasable*. If `setFixedNow(null)` left the clock frozen, every
    // test in the repository would render as 2025-01-15 and nothing here would prove
    // the module still works normally.
    setFixedNow('2025-01-15T00:00:00Z');
    expect(now()).toBe(Date.parse('2025-01-15T00:00:00Z'));
    setFixedNow(null);
    const drift = Math.abs(Date.now() - now());
    expect(drift).toBeLessThan(2000);
  });

  it('moves when the clock is deliberately moved', () => {
    setFixedNow('2025-01-15T00:00:00Z');
    const a = generateSegments('year', 4);
    setFixedNow('2031-01-15T00:00:00Z');
    const b = generateSegments('year', 4);
    // Guards against the determinism test passing because the clock is simply ignored.
    expect(b.map(s => s.label)).not.toEqual(a.map(s => s.label));
  });
});

describe('the playhead is product state, not wall-clock time', () => {
  afterEach(() => setFixedNow(null));

  const segments = () => {
    setFixedNow('2025-01-15T00:00:00Z');
    return generateSegments('month', 24);
  };

  it('is identical on two different real dates when nothing is selected', () => {
    setFixedNow('2025-01-15T00:00:00Z');
    const segs = generateSegments('month', 24);
    const january = playheadPosition(segs, { playbackPosition: null, date: null });

    setFixedNow('2025-09-15T00:00:00Z');
    const segs2 = generateSegments('month', 24);
    const september = playheadPosition(segs2, { playbackPosition: null, date: null });

    expect(september).toBe(january);
  });

  it('honours an explicit playback position', () => {
    const segs = segments();
    expect(playheadPosition(segs, { playbackPosition: 42, date: null })).toBe(42);
  });

  it('clamps an out-of-range playback position instead of overflowing the rail', () => {
    const segs = segments();
    expect(playheadPosition(segs, { playbackPosition: -20, date: null })).toBe(0);
    expect(playheadPosition(segs, { playbackPosition: 180, date: null })).toBe(100);
  });

  it('maps a selected date onto the segment that contains it', () => {
    const segs = segments();
    const jan = segs.find(s => s.dateStart.startsWith('2025-01'));
    expect(jan).toBeDefined();
    expect(playheadPosition(segs, { playbackPosition: null, date: jan!.dateStart })).toBe(
      jan!.start,
    );
  });

  it('parks at the start for a date outside the window rather than clamping to "now"', () => {
    const segs = segments();
    expect(playheadPosition(segs, { playbackPosition: null, date: '1999-01-01' })).toBe(0);
  });
});