/**
 * Workspace Runtime - Owns current workspace, breadcrumbs, title, filters.
 */

import type { WorkspaceName, WorkspaceState, WorkspaceConfig } from './runtime-types';

const DEFAULT_WORKSPACE: WorkspaceState = {
  current: 'dashboard',
  breadcrumbs: ['Dashboard'],
  title: 'Dashboard',
  dateRange: null,
  member: null,
  filters: {},
};

let _state: WorkspaceState = DEFAULT_WORKSPACE;
const _configs: Map<WorkspaceName, WorkspaceConfig> = new Map();
const _listeners: Set<() => void> = new Set();

function notify() {
  _listeners.forEach(fn => fn());
}

// ===== Public API =====

export function getWorkspaceState(): WorkspaceState {
  return _state;
}

export function setWorkspaceState(updater: (prev: WorkspaceState) => WorkspaceState) {
  _state = updater(_state);
  notify();
}

export function navigateTo(name: WorkspaceName, title?: string, breadcrumbs?: string[]) {
  _state = {
    ..._state,
    current: name,
    title: title ?? name.charAt(0).toUpperCase() + name.slice(1),
    breadcrumbs: breadcrumbs ?? [title ?? name.charAt(0).toUpperCase() + name.slice(1)],
  };
  notify();
}

export function setBreadcrumbs(crumbss: string[]) {
  _state = { ..._state, breadcrumbs: crumbss };
  notify();
}

export function setTitle(title: string) {
  _state = { ..._state, title };
  notify();
}

export function setDateRange(from?: string, to?: string) {
  _state = {
    ..._state,
    dateRange: from || to ? { from, to } : null,
  };
  notify();
}

export function setMember(member: string | null) {
  _state = { ..._state, member };
  notify();
}

export function setFilters(filters: Record<string, unknown>) {
  _state = { ..._state, filters };
  notify();
}

export function registerWorkspace(config: WorkspaceConfig) {
  _configs.set(config.name, config);
}

export function getWorkspaceConfig(name: WorkspaceName): WorkspaceConfig | undefined {
  return _configs.get(name);
}

export function subscribe(fn: () => void) {
  _listeners.add(fn);
  return () => {
    _listeners.delete(fn);
  };
}

export function reset() {
  _state = DEFAULT_WORKSPACE;
  _configs.clear();
  notify();
}

// ===== React Hook =====

import { useState, useCallback, useEffect } from 'react';

export function useWorkspaceRuntime() {
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
    navigateTo,
    setBreadcrumbs,
    setTitle,
    setDateRange,
    setMember,
    setFilters,
    registerWorkspace,
    getWorkspaceConfig,
  };
}

// ===== Singleton Export =====

export const workspaceRuntime = {
  get state() { return _state; },
  set state(s: WorkspaceState) { _state = s; notify(); },
  navigateTo,
  setBreadcrumbs,
  setTitle,
  setDateRange,
  setMember,
  setFilters,
  registerWorkspace,
  getWorkspaceConfig,
  subscribe,
  reset,
};

export function resetWorkspaceRuntime() {
  reset();
}
