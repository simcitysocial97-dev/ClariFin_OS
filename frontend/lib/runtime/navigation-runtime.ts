/**
 * Navigation Runtime - Owns navigation history, back/forward, deep link support.
 */

import type { NavigationState, NavigationEntry, WorkspaceName } from './runtime-types';

const MAX_HISTORY = 50;
const DEFAULT_NAV: NavigationState = {
  history: [],
  currentIndex: -1,
};

let _state: NavigationState = DEFAULT_NAV;
const _listeners: Set<() => void> = new Set();

function notify() {
  _listeners.forEach(fn => fn());
}

// ===== Public API =====

export function getNavigationState(): NavigationState {
  return _state;
}

export function pushPath(path: string, workspace?: WorkspaceName) {
  _state = {
    history: [..._state.history.slice(0, _state.currentIndex + 1), { path, timestamp: Date.now(), workspace }],
    currentIndex: _state.currentIndex + 1,
  };
  if (_state.history.length > MAX_HISTORY) {
    _state.history.shift();
    _state.currentIndex--;
  }
  notify();
}

export function goBack(): NavigationEntry | null {
  if (_state.currentIndex > 0) {
    _state = { ..._state, currentIndex: _state.currentIndex - 1 };
    notify();
    return _state.history[_state.currentIndex];
  }
  return null;
}

export function goForward(): NavigationEntry | null {
  if (_state.currentIndex < _state.history.length - 1) {
    _state = { ..._state, currentIndex: _state.currentIndex + 1 };
    notify();
    return _state.history[_state.currentIndex];
  }
  return null;
}

export function getCurrent(): NavigationEntry | null {
  if (_state.currentIndex >= 0 && _state.currentIndex < _state.history.length) {
    return _state.history[_state.currentIndex];
  }
  return null;
}

export function canGoBack(): boolean {
  return _state.currentIndex > 0;
}

export function canGoForward(): boolean {
  return _state.currentIndex < _state.history.length - 1;
}

export function clearHistory() {
  _state = DEFAULT_NAV;
  notify();
}

export function subscribe(fn: () => void) {
  _listeners.add(fn);
  return () => {
    _listeners.delete(fn);
  };
}

export function reset() {
  _state = DEFAULT_NAV;
  notify();
}

// ===== React Hook =====

import { useState, useCallback, useEffect } from 'react';

export function useNavigationRuntime() {
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
    pushPath,
    goBack,
    goForward,
    current: getCurrent,
    canGoBack,
    canGoForward,
    clear: clearHistory,
  };
}

// ===== Singleton Export =====

export const navigationRuntime = {
  get state() { return _state; },
  set state(s: NavigationState) { _state = s; notify(); },
  pushPath,
  goBack,
  goForward,
  get current() { return getCurrent(); },
  get canGoBack() { return canGoBack(); },
  get canGoForward() { return canGoForward(); },
  clear: clearHistory,
  subscribe,
  reset,
};

export function resetNavigationRuntime() {
  reset();
}
