/**
 * TimelineControls - Stage 8C Timeline Experience
 *
 * Controls for the Timeline Experience:
 * - Granularity toggle (day / week / month / quarter / year)
 * - Comparison mode toggle
 * - Forecast mode toggle
 * - Historical playback controls (play/pause/step)
 *
 * No business logic — all actions dispatch to TimelineRuntime.
 */

'use client';

import { useCallback, useRef } from 'react';
import { timelineRuntime } from '@/lib/runtime';
import { cn } from '@/lib/utils';
import { Play, Pause, SkipBack, SkipForward, BarChart3, TrendingUp } from 'lucide-react';
import type { TimeGranularity } from '@/lib/runtime/runtime-types';

// ===== Props =====
interface TimelineControlsProps {
  className?: string;
  onPlaybackTick?: (position: number) => void;
}

// ===== Component =====
export function TimelineControls({ className, onPlaybackTick }: TimelineControlsProps) {
  const state = timelineRuntime.state;

  const granularities: TimeGranularity[] = ['day', 'week', 'month', 'quarter', 'year'];

  const setGranularity = useCallback((g: TimeGranularity) => {
    timelineRuntime.setGranularity(g);
  }, []);

  const toggleCompare = useCallback(() => {
    timelineRuntime.toggleComparison();
  }, []);

  const toggleForecast = useCallback(() => {
    timelineRuntime.setForecastMode(!state.forecastMode);
  }, [state.forecastMode]);

  // Playback position is read directly from the runtime store during render
  // (no local mirror kept in sync via setState-in-effect).
  const playbackPos = timelineRuntime.state.playbackPosition;

  const playRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startPlayback = useCallback(() => {
    if (playbackPos === null) {
      timelineRuntime.setPlaybackPosition(0);
    }
    playRef.current = setInterval(() => {
      const current = timelineRuntime.state.playbackPosition ?? 0;
      const next = current + 0.5;
      if (next >= 100) {
        if (playRef.current) clearInterval(playRef.current);
        playRef.current = null;
        timelineRuntime.setPlaybackPosition(100);
        return;
      }
      timelineRuntime.setPlaybackPosition(next);
      onPlaybackTick?.(0);
    }, 100);
  }, [playbackPos, onPlaybackTick]);

  const stopPlayback = useCallback(() => {
    if (playRef.current) {
      clearInterval(playRef.current);
      playRef.current = null;
    }
    timelineRuntime.setPlaybackPosition(null);
  }, []);

  const stepBack = useCallback(() => {
    const next = Math.max(0, (timelineRuntime.state.playbackPosition ?? 50) - 5);
    timelineRuntime.setPlaybackPosition(next);
  }, []);

  const stepForward = useCallback(() => {
    const next = Math.min(100, (timelineRuntime.state.playbackPosition ?? 50) + 5);
    timelineRuntime.setPlaybackPosition(next);
  }, []);

  const isPlaying = playbackPos !== null;

  return (
    <div className={cn('flex items-center gap-1', className)}>
      {/* Granularity buttons */}
      <div className="flex items-center gap-0.5">
        {granularities.map(g => (
          <button
            key={g}
            onClick={() => setGranularity(g)}
            className={cn(
              'fin-caption px-1.5 py-0.5 rounded-[var(--radius-sm)] transition-colors',
              state.granularity === g
                ? 'bg-[var(--surface-selected)] text-[var(--text-primary)] font-medium'
                : 'text-[var(--text-tertiary)] hover:bg-[var(--surface-interactive)] hover:text-[var(--text-primary)]',
            )}
            aria-pressed={state.granularity === g}
            title={`${g.charAt(0).toUpperCase() + g.slice(1)} view`}
          >
            {g.charAt(0).toUpperCase() + g.slice(1)}
          </button>
        ))}
      </div>

      <div className="h-4 w-px bg-[var(--border-default)] mx-1 shrink-0" />

      {/* Comparison toggle */}
      <button
        onClick={toggleCompare}
        className={cn(
          'flex items-center gap-1 fin-caption px-1.5 py-0.5 rounded-[var(--radius-sm)] transition-colors',
          state.isComparing
            ? 'bg-[var(--color-warning-100)] text-[var(--color-warning-700)]'
            : 'text-[var(--text-tertiary)] hover:bg-[var(--surface-interactive)] hover:text-[var(--text-primary)]',
        )}
        aria-pressed={state.isComparing}
        title="Comparison mode — compare two periods"
      >
        <BarChart3 className="h-3 w-3" />
        <span className="hidden sm:inline">Compare</span>
      </button>

      {/* Forecast toggle */}
      <button
        onClick={toggleForecast}
        className={cn(
          'flex items-center gap-1 fin-caption px-1.5 py-0.5 rounded-[var(--radius-sm)] transition-colors',
          state.forecastMode
            ? 'bg-[var(--color-info-100)] text-[var(--color-info-700)]'
            : 'text-[var(--text-tertiary)] hover:bg-[var(--surface-interactive)] hover:text-[var(--text-primary)]',
        )}
        aria-pressed={state.forecastMode}
        title="Forecast mode — show projected values"
      >
        <TrendingUp className="h-3 w-3" />
        <span className="hidden sm:inline">Forecast</span>
      </button>

      <div className="h-4 w-px bg-[var(--border-default)] mx-1 shrink-0" />

      {/* Playback controls */}
      <div className="flex items-center gap-0.5">
        <button
          onClick={stepBack}
          className="flex items-center justify-center h-5 w-5 rounded-[var(--radius-sm)] text-[var(--text-tertiary)] hover:bg-[var(--surface-interactive)] hover:text-[var(--text-primary)] transition-colors"
          aria-label="Step back"
          title="Step back"
        >
          <SkipBack className="h-3 w-3" />
        </button>
        <button
          onClick={isPlaying ? stopPlayback : startPlayback}
          className={cn(
            'flex items-center justify-center h-5 w-5 rounded-[var(--radius-sm)] transition-colors',
            isPlaying
              ? 'bg-[var(--color-selection)] text-[var(--text-inverse)]'
              : 'text-[var(--text-tertiary)] hover:bg-[var(--surface-interactive)] hover:text-[var(--text-primary)]',
          )}
          aria-label={isPlaying ? 'Pause playback' : 'Play historical playback'}
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? (
            <Pause className="h-3 w-3" />
          ) : (
            <Play className="h-3 w-3" />
          )}
        </button>
        <button
          onClick={stepForward}
          className="flex items-center justify-center h-5 w-5 rounded-[var(--radius-sm)] text-[var(--text-tertiary)] hover:bg-[var(--surface-interactive)] hover:text-[var(--text-primary)] transition-colors"
          aria-label="Step forward"
          title="Step forward"
        >
          <SkipForward className="h-3 w-3" />
        </button>
      </div>

      {/* Playback progress */}
      {playbackPos !== null && (
        <div className="flex items-center gap-1 ml-1">
          <span className="fin-caption text-[var(--text-tertiary)]">{Math.round(playbackPos)}%</span>
        </div>
      )}
    </div>
  );
}
