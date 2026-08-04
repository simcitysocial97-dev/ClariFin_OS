/**
 * Timeline Segment Utilities - Stage 8C Timeline Experience
 *
 * Pure functions for generating time rail segments at different granularities.
 * No runtime dependencies — pure calculation.
 */

import type { TimeGranularity } from '@/lib/runtime/runtime-types';

// ===== Segment Types =====
export interface RailSegment {
  start: number;    // percentage 0–100
  end: number;      // percentage 0–100
  label: string;
  dateStart: string; // ISO date YYYY-MM-DD
  dateEnd: string;   // ISO date YYYY-MM-DD
}

/**
 * Generate rail segments for a given granularity and count.
 * Segments are evenly spaced across the 0–100% track.
 */
export function generateSegments(granularity: TimeGranularity, count: number = 24): RailSegment[] {
  const now = new Date();
  const segments: RailSegment[] = [];
  const segWidth = 100 / count;

  for (let i = 0; i < count; i++) {
    const startPct = i * segWidth;
    const endPct = (i + 1) * segWidth;

    let label = '';
    let dateStart = '';
    let dateEnd = '';

    if (granularity === 'year') {
      const year = now.getFullYear() - Math.floor(count / 2) + i;
      label = `${year}`;
      dateStart = `${year}-01-01`;
      dateEnd = `${year}-12-31`;
    } else if (granularity === 'quarter') {
      const year = now.getFullYear();
      const q = i % 4;
      label = `Q${q + 1}`;
      const months = [[1, 3], [4, 6], [7, 9], [10, 12]][q] as [number, number];
      dateStart = `${year}-${String(months[0]).padStart(2, '0')}-01`;
      dateEnd = `${year}-${String(months[1]).padStart(2, '0')}-28`;
    } else if (granularity === 'month') {
      const year = now.getFullYear();
      const month = i % 12;
      label = new Date(year, month, 1).toLocaleDateString('en-US', { month: 'short' });
      dateStart = `${year}-${String(month + 1).padStart(2, '0')}-01`;
      dateEnd = `${year}-${String(month + 1).padStart(2, '0')}-28`;
    } else if (granularity === 'week') {
      const weekNum = i;
      label = `W${weekNum + 1}`;
      dateStart = `2024-01-${String((weekNum * 7) % 28 + 1).padStart(2, '0')}`;
      dateEnd = `2024-01-${String((weekNum * 7 + 6) % 28 + 1).padStart(2, '0')}`;
    } else {
      // day
      const dayOffset = i - Math.floor(count / 2);
      const d = new Date(now);
      d.setDate(d.getDate() + dayOffset);
      label = d.toLocaleDateString('en-US', { weekday: 'short' });
      dateStart = d.toISOString().slice(0, 10);
      dateEnd = dateStart;
    }

    segments.push({ start: startPct, end: endPct, label, dateStart, dateEnd });
  }

  return segments;
}
