/**
 * Timeline Runtime - Owns current timeline position and comparison period.
 */

import type { TimelinePosition, TimeGranularity } from './runtime-types';

const DEFAULT_TIMELINE: TimelinePosition = {
  date: null,
  granularity: 'month',
  comparisonPeriod: null,
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
  notify();
}

export function setGranularity(granularity: TimeGranularity) {
  _state = { ..._state, granularity };
  notify();
}

export function setComparisonPeriod(from?: string, to?: string) {
  _state = {
    ..._state,
    comparisonPeriod: from || to ? { from, to } : null,
  };
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
  };
}

// ===== Singleton Export =====

export const timelineRuntime = {
  get state() { return _state; },
  set state(s: TimelinePosition) { _state = s; notify(); },
  setPosition,
  setGranularity,
  setComparisonPeriod,
  subscribe,
  reset,
};

export function resetTimelineRuntime() {
  reset();
}
