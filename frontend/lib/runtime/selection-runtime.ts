/**
 * Selection Runtime - Owns selected entity across all workspaces.
 */

import type { SelectionEntity, SelectionState } from './runtime-types';

const DEFAULT_SELECTION: SelectionState = {
  active: null,
  multi: new Set(),
  history: [],
};

let _state: SelectionState = DEFAULT_SELECTION;
const _listeners: Set<() => void> = new Set();

function notify() {
  _listeners.forEach(fn => fn());
}

// ===== Public API =====

export function getSelectionState(): SelectionState {
  return _state;
}

export function setSelectionState(updater: (prev: SelectionState) => SelectionState) {
  _state = updater(_state);
  notify();
}

export function selectEntity(entity: SelectionEntity) {
  _state = {
    ..._state,
    active: entity,
    history: [..._state.history.slice(-19), entity],
  };
  notify();
}

export function toggleMulti(id: string, selected: boolean) {
  _state = {
    ..._state,
    multi: selected
      ? new Set([..._state.multi, id])
      : new Set([..._state.multi].filter(i => i !== id)),
  };
  notify();
}

export function clearSelection() {
  _state = { ..._state, active: null };
  notify();
}

export function clearMultiSelection() {
  _state = { ..._state, multi: new Set() };
  notify();
}

export function subscribe(fn: () => void) {
  _listeners.add(fn);
  return () => {
    _listeners.delete(fn);
  };
}

export function reset() {
  _state = DEFAULT_SELECTION;
  notify();
}

// ===== React Hook =====

import { useState, useCallback, useEffect } from 'react';

export function useSelectionRuntime() {
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
    selectEntity,
    toggleMulti,
    clearSelection,
    clearMultiSelection,
  };
}

// ===== Singleton Export =====

export const selectionRuntime = {
  get state() { return _state; },
  set state(s: SelectionState) { _state = s; notify(); },
  selectEntity,
  toggleMulti,
  clearSelection,
  clearMultiSelection,
  subscribe,
  reset,
};

export function resetSelectionRuntime() {
  reset();
}
