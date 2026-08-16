/**
 * Workspace Lifecycle Tests - Stage 8B Navigation Experience
 *
 * Tests for workspace LRU cache, snapshot capture/restore, and transition management.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { LRUCache } from '../lru-cache';
import {
  captureSnapshot,
  getSnapshot,
  removeSnapshot,
  clearAllSnapshots,
} from '../workspace-snapshot';
import { WorkspaceLifecycleManager } from '../workspace-lifecycle';
import type { WorkspaceName } from '../workspace-context';

const WORKSPACES: WorkspaceName[] = [
  'dashboard',
  'transactions',
  'accounts',
  'cards',
  'loans',
  'investments',
  'net-worth',
  'cashflow',
  'behaviour',
  'forecast',
  'reconciliation',
  'settings',
];

function makeSnapshot(workspaceId: string) {
  return {
    workspaceId,
    scrollPosition: { x: 100, y: 200 },
    filters: { date: '2024-01' },
    sortConfig: { field: 'date', direction: 'desc' as const },
    selectionIds: ['tx1', 'tx2'],
    timestamp: Date.now(),
  };
}

describe('LRUCache', () => {
  let cache: LRUCache<string, number>;

  beforeEach(() => {
    cache = new LRUCache<string, number>(3);
  });

  it('stores and retrieves values', () => {
    cache.set('a', 1);
    expect(cache.get('a')).toBe(1);
  });

  it('evicts least recently used when full', () => {
    cache.set('a', 1);
    cache.set('b', 2);
    cache.set('c', 3);
    // Access 'a' to make it MRU
    cache.get('a');
    // Add 'd' — should evict 'b' (LRU)
    cache.set('d', 4);
    expect(cache.get('a')).toBe(1);
    expect(cache.get('b')).toBeUndefined();
    expect(cache.get('c')).toBe(3);
    expect(cache.get('d')).toBe(4);
  });

  it('promotes accessed entries to MRU', () => {
    cache.set('a', 1);
    cache.set('b', 2);
    cache.set('c', 3);
    cache.get('a'); // promote 'a'
    cache.set('d', 4); // evict 'b' (now LRU)
    expect(cache.get('b')).toBeUndefined();
    expect(cache.get('a')).toBe(1);
  });

  it('updates value on duplicate key without changing access order', () => {
    cache.set('a', 1);
    cache.set('a', 2);
    expect(cache.get('a')).toBe(2);
  });

  it('deletes specific keys', () => {
    cache.set('a', 1);
    cache.set('b', 2);
    cache.delete('a');
    expect(cache.has('a')).toBe(false);
    expect(cache.has('b')).toBe(true);
  });

  it('clears all entries', () => {
    cache.set('a', 1);
    cache.set('b', 2);
    cache.clear();
    expect(cache.size).toBe(0);
    expect(cache.has('a')).toBe(false);
  });

  it('returns LRU key', () => {
    cache.set('a', 1);
    cache.set('b', 2);
    cache.set('c', 3);
    expect(cache.getLRUKey()).toBe('a');
    cache.get('a'); // promote
    expect(cache.getLRUKey()).toBe('b');
  });

  it('returns null for empty cache', () => {
    expect(cache.getLRUKey()).toBeNull();
  });
});

describe('WorkspaceStateSnapshot', () => {
  beforeEach(() => {
    clearAllSnapshots();
  });

  it('captures and retrieves a snapshot', () => {
    const snap = makeSnapshot('transactions');
    captureSnapshot(snap);
    const retrieved = getSnapshot('transactions');
    expect(retrieved).not.toBeNull();
    expect(retrieved!.scrollPosition.y).toBe(200);
    expect(retrieved!.filters.date).toBe('2024-01');
  });

  it('returns null for missing snapshot', () => {
    expect(getSnapshot('nonexistent')).toBeNull();
  });

  it('removes a snapshot', () => {
    captureSnapshot(makeSnapshot('accounts'));
    removeSnapshot('accounts');
    expect(getSnapshot('accounts')).toBeNull();
  });

  it('clears all snapshots', () => {
    captureSnapshot(makeSnapshot('dashboard'));
    captureSnapshot(makeSnapshot('transactions'));
    clearAllSnapshots();
    expect(getSnapshot('dashboard')).toBeNull();
    expect(getSnapshot('transactions')).toBeNull();
  });

  it('lists all snapshot keys', () => {
    captureSnapshot(makeSnapshot('dashboard'));
    captureSnapshot(makeSnapshot('transactions'));
    expect(getAllSnapshotKeys()).toEqual(expect.arrayContaining(['dashboard', 'transactions']));
  });
});

// Need to import getAllSnapshotKeys
import { getAllSnapshotKeys } from '../workspace-snapshot';

describe('WorkspaceLifecycleManager', () => {
  let manager: WorkspaceLifecycleManager;

  beforeEach(() => {
    manager = new WorkspaceLifecycleManager();
    clearAllSnapshots();
  });

  it('starts with no transitions', () => {
    const t = manager.getTransition();
    expect(t.isTransitioning).toBe(false);
    expect(t.fromWorkspace).toBeNull();
    expect(t.toWorkspace).toBeNull();
  });

  it('activates a workspace as cold-mount when not cached', () => {
    const result = manager.activate('transactions', null);
    expect(result.strategy).toBe('cold-mount');
    expect(result.snapshot).toBeNull();
  });

  it('restores a workspace when cached', () => {
    // First activation mounts it
    manager.activate('transactions', null);
    // Deactivate to populate cache
    manager.deactivate('transactions');
    // Now restore snapshot
    captureSnapshot(makeSnapshot('transactions'));

    const result = manager.activate('transactions', null);
    expect(result.strategy).toBe('restored');
    expect(result.snapshot).not.toBeNull();
    expect(result.snapshot!.scrollPosition.x).toBe(100);
  });

  it('captures snapshot of outgoing workspace on switch', () => {
    manager.activate('dashboard', null);
    manager.activate('transactions', 'dashboard');
    // Dashboard should have been captured
    const snap = getSnapshot('dashboard');
    expect(snap).not.toBeNull();
  });

  it('starts a transition', () => {
    manager.startTransition('dashboard', 'transactions');
    const t = manager.getTransition();
    expect(t.isTransitioning).toBe(true);
    expect(t.fromWorkspace).toBe('dashboard');
    expect(t.toWorkspace).toBe('transactions');
    expect(t.duration).toBe(150);
  });

  it('ends a transition', () => {
    manager.startTransition('dashboard', 'transactions');
    manager.endTransition();
    const t = manager.getTransition();
    expect(t.isTransitioning).toBe(false);
    expect(t.fromWorkspace).toBeNull();
    expect(t.toWorkspace).toBeNull();
  });

  it('checks transition completion after duration', () => {
    manager.startTransition('dashboard', 'transactions');
    // isTransitioning is true, so not complete yet
    expect(manager.isTransitionComplete()).toBe(false);
    manager.endTransition();
    expect(manager.isTransitionComplete()).toBe(true);
  });

  it('deactivates a mounted workspace into cache', () => {
    manager.ensureMounted('dashboard');
    manager.deactivate('dashboard');
    expect(manager.isCached('dashboard')).toBe(true);
    expect(manager.isMounted('dashboard')).toBe(false);
  });

  it('destroys a workspace completely', () => {
    manager.ensureMounted('dashboard');
    manager.destroy('dashboard');
    expect(manager.isCached('dashboard')).toBe(false);
    expect(manager.isMounted('dashboard')).toBe(false);
    expect(getSnapshot('dashboard')).toBeNull();
  });

  it('enforces max cache size of 5', () => {
    // Activate and deactivate each to populate cache
    for (let i = 0; i < 6; i++) {
      manager.activate(WORKSPACES[i], i > 0 ? WORKSPACES[i - 1] : null);
      manager.deactivate(WORKSPACES[i]);
    }
    // First workspace should be evicted (LRU)
    expect(manager.isCached(WORKSPACES[0])).toBe(false);
    // Last workspace should be cached
    expect(manager.isCached(WORKSPACES[5])).toBe(true);
    expect(manager.cachedCount).toBe(5);
  });

  it('promotes accessed workspace in cache', () => {
    manager.activate('dashboard', null);
    manager.activate('transactions', 'dashboard');
    manager.activate('accounts', 'transactions');
    // Access dashboard again
    manager.activate('dashboard', 'accounts');
    // Now activate two more to fill cache
    manager.activate('cards', 'dashboard');
    manager.activate('loans', 'cards');
    // 'transactions' should be evicted (was LRU after dashboard promotion)
    expect(manager.isCached('transactions')).toBe(false);
  });

  it('reset clears all state', () => {
    manager.activate('dashboard', null);
    manager.ensureMounted('dashboard');
    captureSnapshot(makeSnapshot('dashboard'));
    manager.reset();
    expect(manager.isMounted('dashboard')).toBe(false);
    expect(manager.isCached('dashboard')).toBe(false);
    expect(getSnapshot('dashboard')).toBeNull();
  });

  it('getMountRecord returns undefined for unknown workspace', () => {
    expect(manager.getMountRecord('dashboard')).toBeUndefined();
  });

  it('ensuresMounted creates or promotes record', () => {
    const r1 = manager.ensureMounted('dashboard');
    expect(r1.state).toBe('mounted');
    expect(r1.workspaceId).toBe('dashboard');

    // Deactivate then ensure again
    manager.deactivate('dashboard');
    const r2 = manager.ensureMounted('dashboard');
    expect(r2.state).toBe('mounted');
  });
});
