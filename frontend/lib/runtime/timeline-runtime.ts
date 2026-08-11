'use client';

/**
 * Timeline Runtime - Owns current timeline position and comparison period.
 */

import type { TimelinePosition, TimeGranularity } from './runtime-types';
import { runtimeEventBus, TIMELINE_CHANGED, TIMELINE_GRANULARITY_CHANGED } from '../event-bus';

const DEFAULT_TIMELINE: TimelinePosition = {
  date: null,
  granularity: 'month',
  comparisonPeriod: null,
  isComparing: false,
  forecastMode: false,
  playbackPosition: null,
};

let _state: TimelinePosition = DEFAULT_TIMELINE;
const _listeners: Set<() => void> = new Set();

function notify() {
  _listeners.forEach(fn => fn());
}

// ===== Public API =====

export function getTimelineState(): TimelinePosition {
  return _state;
}

export function setTimelineState(updater: (prev: TimelinePosition) => TimelinePosition) {
  _state = updater(_state);
  notify();
}

export function setPosition(date: string | null) {
  _state = { ..._state, date };
  runtimeEventBus.publish({
    type: TIMELINE_CHANGED,
    timestamp: Date.now(),
    source: 'timeline-runtime',
    payload: {
      activePeriod: { start: date ?? '', end: date ?? '', label: date ?? '' },
      granularity: _state.granularity,
      comparisonPeriod: _state.comparisonPeriod,
    },
  });
  notify();
}

export function setGranularity(granularity: TimeGranularity) {
  _state = { ..._state, granularity };
  runtimeEventBus.publish({
    type: TIMELINE_GRANULARITY_CHANGED,
    timestamp: Date.now(),
    source: 'timeline-runtime',
    payload: { granularity: granularity as 'day' | 'week' | 'month' | 'quarter' | 'year' },
  });
  notify();
}

export function setComparisonPeriod(from?: string, to?: string) {
  _state = {
    ..._state,
    comparisonPeriod: from || to ? { from, to } : null,
  };
  notify();
}

export function setForecastMode(enabled: boolean) {
  _state = { ..._state, forecastMode: enabled };
  notify();
}

export function setPlaybackPosition(position: number | null) {
  _state = { ..._state, playbackPosition: position };
  notify();
}

export function toggleComparison() {
  _state = { ..._state, isComparing: !_state.isComparing };
  if (!_state.isComparing) {
    _state = { ..._state, comparisonPeriod: null };
  }
  notify();
}

export function subscribe(fn: () => void) {
  _listeners.add(fn);
  return () => {
    _listeners.delete(fn);
  };
}

export function reset() {
  _state = DEFAULT_TIMELINE;
  notify();
}

// ===== React Hook =====

import { useState, useCallback, useEffect } from 'react';

export function useTimelineRuntime() {
  const [, tick] = useState(0);

  const subscribeRef = useCallback(() => {
    const tickFn = () => tick(n => n + 1);
    _listeners.add(tickFn);
    return (): void => {
      _listeners.delete(tickFn);
    };
  }, []);

  useEffect(() => {
    const unsubscribe = subscribeRef();
    return unsubscribe;
  }, [subscribeRef]);

  return {
    get state() { return _state; },
    setPosition,
    setGranularity,
    setComparisonPeriod,
    setForecastMode,
    setPlaybackPosition,
    toggleComparison,
  };
}

// ===== Singleton Export =====

export const timelineRuntime = {
  get state() { return _state; },
  set state(s: TimelinePosition) { _state = s; notify(); },
  setPosition,
  setGranularity,
  setComparisonPeriod,
  setForecastMode,
  setPlaybackPosition,
  toggleComparison,
  subscribe,
  reset,
};

export function resetTimelineRuntime() {
  reset();
}
