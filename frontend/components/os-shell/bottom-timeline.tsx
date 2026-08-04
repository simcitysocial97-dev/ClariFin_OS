/**
 * Bottom Timeline - Stage 8C Timeline Experience
 *
 * Operating timeline panel (88px collapsed / 136px expanded).
 * Contains: TimeRail, TimelineScrubber, TimelineControls.
 * Supports: Year / Quarter / Month / Week / Day granularity,
 *           Comparison mode, Forecast mode, Historical playback.
 * No graph. Pure timeline experience.
 */

'use client';

import { useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { TimeRail } from './timeline-rail';
import { TimelineScrubber } from './timeline-scrubber';
import { TimelineControls } from './timeline-controls';

// ===== Bottom Timeline Component =====
interface BottomTimelineProps {
  className?: string;
}

export function BottomTimeline({ className }: BottomTimelineProps) {
  const [collapsed, setCollapsed] = useState(false);

  const handlePlaybackTick = useCallback(() => {
    // Could dispatch events or update parent state here
  }, []);

  if (collapsed) {
    return (
      <footer
        className={cn(
          'fixed bottom-0 left-[180px] right-0 z-20 h-7',
          'border-t border-[var(--border-default)]',
          'bg-[var(--surface-timeline)]',
          className,
        )}
      >
        <button
          onClick={() => setCollapsed(false)}
          className="flex items-center justify-start h-7 px-3 gap-1.5 w-full text-[var(--text-tertiary)] hover:bg-[var(--surface-interactive)] transition-colors"
          aria-label="Expand timeline"
        >
          <ChevronUp className="h-3 w-3" />
          <span className="fin-caption">Timeline</span>
        </button>
      </footer>
    );
  }

  return (
    <footer
      className={cn(
        'fixed bottom-0 left-[180px] right-0 z-20',
        'border-t border-[var(--border-default)]',
        'bg-[var(--surface-timeline)]',
        'h-36',
        className,
      )}
    >
      {/* Controls bar */}
      <div className="flex items-center gap-2 px-3 h-8 border-b border-[var(--border-default)]">
        <TimelineControls onPlaybackTick={handlePlaybackTick} />

        <div className="ml-auto flex items-center gap-1.5">
          <button
            onClick={() => setCollapsed(true)}
            className="flex items-center justify-center h-5 w-5 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)] transition-colors"
            aria-label="Collapse timeline"
            title="Collapse timeline"
          >
            <ChevronDown className="h-2.5 w-2.5" />
          </button>
        </div>
      </div>

      {/* TimeRail + Scrubber */}
      <div className="px-3 py-2">
        <div className="relative h-12">
          {/* The rail and scrubber are layered — scrubber sits on top */}
          <TimeRail className="absolute inset-0" />
          <TimelineScrubber className="absolute inset-0" />
        </div>
      </div>

      {/* Period detail strip */}
      <div className="px-3 h-5 flex items-center gap-3 border-t border-[var(--border-default)] bg-[var(--surface-default)]">
        <span className="fin-caption text-[var(--text-tertiary)]">
          Drag the rail to scrub • Click periods to navigate
        </span>
      </div>
    </footer>
  );
}
