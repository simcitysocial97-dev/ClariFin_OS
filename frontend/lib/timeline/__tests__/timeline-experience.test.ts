/**
 * Timeline Experience Tests - Stage 8C Timeline Experience
 *
 * Tests for TimeRail segment generation, TimelineRuntime methods,
 * and granularity handling.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { generateSegments } from '../../timeline/segments';
import {
  timelineRuntime,
  resetTimelineRuntime,
} from '../../runtime/timeline-runtime';

describe('generateSegments', () => {
  it('generates 24 segments by default', () => {
    const segs = generateSegments('month');
    expect(segs).toHaveLength(24);
  });

  it('year granularity produces year labels', () => {
    const segs = generateSegments('year', 5);
    expect(segs[0].label).toMatch(/^\d{4}$/);
    expect(segs[0].dateStart.startsWith(segs[0].label)).toBe(true);
  });

  it('quarter granularity produces Q1–Q4 labels', () => {
    const segs = generateSegments('quarter', 8);
    for (const seg of segs) {
      expect(seg.label).toMatch(/^Q[1-4]$/);
    }
  });

  it('month granularity produces short month names', () => {
    const segs = generateSegments('month', 12);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    for (let i = 0; i < 12; i++) {
      expect(segs[i].label).toBe(months[i]);
    }
  });

  it('week granularity produces W1, W2, ... labels', () => {
    const segs = generateSegments('week', 6);
    expect(segs[0].label).toBe('W1');
    expect(segs[5].label).toBe('W6');
  });

  it('day granularity produces weekday short names', () => {
    const segs = generateSegments('day', 7);
    for (const seg of segs) {
      expect(seg.label.length).toBeLessThanOrEqual(3);
    }
  });

  it('segments cover 0–100% without gaps', () => {
    const segs = generateSegments('month', 12);
    expect(segs[0].start).toBe(0);
    expect(segs[11].end).toBe(100);
    for (let i = 1; i < segs.length; i++) {
      expect(segs[i].start).toBe(segs[i - 1].end);
    }
  });

  it('each segment has ISO date strings', () => {
    const segs = generateSegments('month', 3);
    for (const seg of segs) {
      expect(seg.dateStart).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(seg.dateEnd).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    }
  });
});

describe('TimelineRuntime — Granularity', () => {
  beforeEach(() => {
    resetTimelineRuntime();
  });

  it('starts with month granularity', () => {
    expect(timelineRuntime.state.granularity).toBe('month');
  });

  it('accepts day granularity', () => {
    timelineRuntime.setGranularity('day');
    expect(timelineRuntime.state.granularity).toBe('day');
  });

  it('accepts week granularity', () => {
    timelineRuntime.setGranularity('week');
    expect(timelineRuntime.state.granularity).toBe('week');
  });

  it('accepts quarter granularity', () => {
    timelineRuntime.setGranularity('quarter');
    expect(timelineRuntime.state.granularity).toBe('quarter');
  });

  it('accepts year granularity', () => {
    timelineRuntime.setGranularity('year');
    expect(timelineRuntime.state.granularity).toBe('year');
  });
});

describe('TimelineRuntime — Forecast Mode', () => {
  beforeEach(() => {
    resetTimelineRuntime();
  });

  it('starts with forecastMode false', () => {
    expect(timelineRuntime.state.forecastMode).toBe(false);
  });

  it('enables forecast mode', () => {
    timelineRuntime.setForecastMode(true);
    expect(timelineRuntime.state.forecastMode).toBe(true);
  });

  it('disables forecast mode', () => {
    timelineRuntime.setForecastMode(true);
    timelineRuntime.setForecastMode(false);
    expect(timelineRuntime.state.forecastMode).toBe(false);
  });
});

describe('TimelineRuntime — Comparison Mode', () => {
  beforeEach(() => {
    resetTimelineRuntime();
  });

  it('starts with isComparing false', () => {
    expect(timelineRuntime.state.isComparing).toBe(false);
  });

  it('toggleComparison enables comparison', () => {
    timelineRuntime.toggleComparison();
    expect(timelineRuntime.state.isComparing).toBe(true);
  });

  it('toggleComparison disables when already on', () => {
    timelineRuntime.toggleComparison();
    timelineRuntime.toggleComparison();
    expect(timelineRuntime.state.isComparing).toBe(false);
  });

  it('clears comparison period when disabling', () => {
    timelineRuntime.setComparisonPeriod('2024-01-01', '2024-06-30');
    timelineRuntime.toggleComparison();
    expect(timelineRuntime.state.comparisonPeriod).not.toBeNull();
    timelineRuntime.toggleComparison();
    expect(timelineRuntime.state.comparisonPeriod).toBeNull();
  });
});

describe('TimelineRuntime — Playback Position', () => {
  beforeEach(() => {
    resetTimelineRuntime();
  });

  it('starts with null playback position', () => {
    expect(timelineRuntime.state.playbackPosition).toBeNull();
  });

  it('sets playback position to a number', () => {
    timelineRuntime.setPlaybackPosition(42);
    expect(timelineRuntime.state.playbackPosition).toBe(42);
  });

  it('clears playback position when set to null', () => {
    timelineRuntime.setPlaybackPosition(50);
    timelineRuntime.setPlaybackPosition(null);
    expect(timelineRuntime.state.playbackPosition).toBeNull();
  });
});

describe('TimelineRuntime — Subscription', () => {
  beforeEach(() => {
    resetTimelineRuntime();
  });

  it('notifies subscribers on granularity change', () => {
    const fn = vi.fn();
    timelineRuntime.subscribe(fn);
    timelineRuntime.setGranularity('year');
    expect(fn).toHaveBeenCalledOnce();
  });

  it('notifies subscribers on forecast mode change', () => {
    const fn = vi.fn();
    timelineRuntime.subscribe(fn);
    timelineRuntime.setForecastMode(true);
    expect(fn).toHaveBeenCalledOnce();
  });

  it('unsubscribes correctly', () => {
    const fn = vi.fn();
    const unsub = timelineRuntime.subscribe(fn);
    unsub();
    timelineRuntime.setGranularity('day');
    expect(fn).not.toHaveBeenCalled();
  });
});

describe('generateSegments — label consistency', () => {
  it('produces consistent label count for year mode', () => {
    const segs = generateSegments('year', 10);
    expect(segs.filter(s => s.label.match(/^\d{4}$/))).toHaveLength(10);
  });

  it('produces consistent label count for quarter mode', () => {
    const segs = generateSegments('quarter', 8);
    expect(segs.filter(s => /^Q[1-4]$/.test(s.label))).toHaveLength(8);
  });
});
