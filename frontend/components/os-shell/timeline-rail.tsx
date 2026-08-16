/**
 * TimeRail - Stage 8C Timeline Experience
 *
 * Horizontal visual track showing a time range with period markers.
 * Supports day / week / month / quarter / year granularity.
 * Shows current position indicator and comparison period overlay.
 * No business logic — reads from TimelineRuntime only.
 */

'use client';

import { useMemo } from 'react';
import { timelineRuntime } from '@/lib/runtime';
import { cn } from '@/lib/utils';
import { generateSegments, type RailSegment } from '@/lib/timeline/segments';

// ===== Props =====
interface TimeRailProps {
  className?: string;
  onPositionChange?: (position: number) => void;
}

// ===== TimeRail Component =====
export function TimeRail({ className, onPositionChange }: TimeRailProps) {
  const granularity = timelineRuntime.state.granularity;
  const segments = useMemo(() => generateSegments(granularity, 24), [granularity]);

  // Current position as percentage (based on current date)
  const currentPosition = useMemo(() => {
    const now = new Date();
    const yearStart = new Date(now.getFullYear(), 0, 1);
    const yearEnd = new Date(now.getFullYear(), 11, 31);
    const total = yearEnd.getTime() - yearStart.getTime();
    const elapsed = now.getTime() - yearStart.getTime();
    return total > 0 ? (elapsed / total) * 100 : 50;
  }, []);

  const handleRailClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = ((e.clientX - rect.left) / rect.width) * 100;
    onPositionChange?.(Math.max(0, Math.min(100, pct)));
  };

  return (
    <div className={cn('flex flex-col gap-1', className)}>
      {/* Rail track */}
      <div
        className="relative h-6 cursor-pointer select-none"
        onClick={handleRailClick}
        role="slider"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(currentPosition)}
        aria-label="Timeline position"
        tabIndex={0}
      >
        {/* Background track */}
        <div className="absolute inset-0 rounded-full bg-[var(--surface-interactive)]" />

        {/* Segments */}
        {segments.map((seg, i) => {
          const isPast = seg.end <= currentPosition;
          const isCurrent = seg.start <= currentPosition && seg.end >= currentPosition;
          return (
            <div
              key={i}
              className={cn(
                'absolute top-0 h-full rounded-sm transition-colors duration-75',
                isCurrent ? 'bg-[var(--color-selection)]' : isPast ? 'bg-[var(--color-selection-foreground)]' : 'bg-transparent',
              )}
              style={{ left: `${seg.start}%`, width: `${seg.end - seg.start}%` }}
            />
          );
        })}

        {/* Comparison period overlay */}
        {timelineRuntime.state.isComparing && timelineRuntime.state.comparisonPeriod?.from && (
          <div
            className="absolute top-0 h-full bg-[var(--color-warning-200)] opacity-40 rounded-sm"
            style={{ left: '30%', width: '20%' }}
            title="Comparison period"
          />
        )}

        {/* Forecast overlay */}
        {timelineRuntime.state.forecastMode && (
          <div
            className="absolute top-0 h-full bg-[var(--color-info-200)] opacity-30 rounded-sm"
            style={{ left: `${currentPosition}%`, width: '25%' }}
            title="Forecast mode"
          />
        )}

        {/* Position indicator (scrubber) */}
        <div
          className="absolute top-0 h-full w-0.5 bg-[var(--text-primary)] shadow-sm"
          style={{ left: `${currentPosition}%`, transform: 'translateX(-50%)' }}
        >
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-[var(--text-primary)] border-2 border-[var(--surface-default)]" />
        </div>

        {/* Playhead for playback */}
        {timelineRuntime.state.playbackPosition !== null && (
          <div
            className="absolute top-0 h-full w-0.5 bg-[var(--color-positive-500)] opacity-70"
            style={{ left: `${timelineRuntime.state.playbackPosition}%`, transform: 'translateX(-50%)' }}
          />
        )}
      </div>

      {/* Period labels */}
      <div className="relative h-4">
        {segments.map((seg, i) => {
          const showLabel =
            granularity === 'year' ||
            granularity === 'quarter' ||
            (granularity === 'month' && i % 1 === 0) ||
            (granularity === 'week' && i % 2 === 0) ||
            (granularity === 'day' && i % 3 === 0);

          if (!showLabel) return null;
          return (
            <span
              key={i}
              className="absolute fin-caption text-[var(--text-tertiary)] whitespace-nowrap"
              style={{ left: `${seg.start + (seg.end - seg.start) / 2 - 2}%`, transform: 'translateX(-50%)' }}
            >
              {seg.label}
            </span>
          );
        })}
      </div>
    </div>
  );
}

// ===== Segment data for tests =====
export { generateSegments };
export type { RailSegment };
