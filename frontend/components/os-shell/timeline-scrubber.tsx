/**
 * TimelineScrubber - Stage 8C Timeline Experience
 *
 * Draggable scrubber handle for the TimeRail.
 * Click-and-drag to scrub through time.
 * Reads position from TimelineRuntime, writes back via setter.
 * No business logic — pure composition layer.
 */

'use client';

import { useRef, useCallback, useEffect } from 'react';
import { timelineRuntime } from '@/lib/runtime';
import { cn } from '@/lib/utils';

// ===== Props =====
interface TimelineScrubberProps {
  className?: string;
}

// ===== Component =====
export function TimelineScrubber({ className }: TimelineScrubberProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);

  const setPositionFromEvent = useCallback((clientX: number) => {
    const track = trackRef.current;
    if (!track) return;
    const rect = track.getBoundingClientRect();
    const pct = ((clientX - rect.left) / rect.width) * 100;
    const clamped = Math.max(0, Math.min(100, pct));
    // Map percentage to a date offset (roughly: each percent ≈ 3.65 days)
    const now = new Date();
    const offsetDays = Math.round((clamped - 50) * 7.3); // ±~180 day range
    const targetDate = new Date(now.getTime() + offsetDays * 86400000);
    timelineRuntime.setPosition(targetDate.toISOString().slice(0, 10));
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    isDragging.current = true;
    e.preventDefault();
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return;
      setPositionFromEvent(e.clientX);
    };
    const handleMouseUp = () => {
      isDragging.current = false;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [setPositionFromEvent]);

  return (
    <div
      ref={trackRef}
      className={cn('relative h-full w-full cursor-pointer', className)}
      onMouseDown={handleMouseDown}
      role="slider"
      aria-label="Timeline scrubber"
      tabIndex={0}
    >
      {/* Invisible drag target */}
      <div className="absolute inset-0" />
    </div>
  );
}
