/**
 * Workspace Lifecycle Manager - Stage 8B Navigation Experience
 *
 * Manages workspace mounting, caching, and restoration using an LRU cache.
 * Captures state snapshots on deactivation and restores them on re-activation.
 * Coordinates cross-fade transitions between workspaces.
 *
 * Does NOT modify frozen runtimes. Works alongside WorkspaceRuntime and
 * NavigationRuntime as a pure composition layer.
 */

import { LRUCache } from './lru-cache';
import {
  captureSnapshot,
  getSnapshot,
  removeSnapshot,
  clearAllSnapshots,
  type WorkspaceStateSnapshot,
} from './workspace-snapshot';
import type { WorkspaceName } from './workspace-context';

const MAX_CACHED = 5;

// ===== Workspace Mount State =====
export type MountState = 'mounted' | 'cached' | 'destroyed';

export interface WorkspaceMountRecord {
  workspaceId: string;
  state: MountState;
  mountTimestamp: number;
  snapshot: WorkspaceStateSnapshot | null;
}

// ===== Transition State =====
export interface TransitionState {
  isTransitioning: boolean;
  fromWorkspace: WorkspaceName | null;
  toWorkspace: WorkspaceName | null;
  startTime: number;
  duration: number; // ms
}

// ===== Lifecycle Manager =====
export class WorkspaceLifecycleManager {
  private readonly cache = new LRUCache<WorkspaceName, unknown>(MAX_CACHED);
  private readonly mounts = new Map<WorkspaceName, WorkspaceMountRecord>();
  private transition: TransitionState = {
    isTransitioning: false,
    fromWorkspace: null,
    toWorkspace: null,
    startTime: 0,
    duration: 150,
  };

  constructor() {
    this.loadFromStorage();
  }

  // ===== Workspace Activation =====
  /**
   * Activate a workspace. Returns 'restored' if found in cache,
   * 'cold-mount' if not. Captures snapshot of previous workspace.
   */
  activate(target: WorkspaceName, currentActive: WorkspaceName | null): {
    strategy: 'restored' | 'cold-mount';
    snapshot: WorkspaceStateSnapshot | null;
  } {
    // Capture snapshot of outgoing workspace
    if (currentActive && currentActive !== target) {
      this.captureForWorkspace(currentActive);
    }

    // Check cache first
    if (this.cache.has(target)) {
      this.cache.get(target); // promote to MRU
      const snapshot = getSnapshot(target);
      this.ensureMounted(target);
      return { strategy: 'restored', snapshot };
    }

    // Cold mount
    this.ensureMounted(target);
    return { strategy: 'cold-mount', snapshot: null };
  }

  /**
   * Deactivate a workspace — capture snapshot, mark as cached or destroyed.
   */
  deactivate(workspace: WorkspaceName): void {
    const snapshot = getSnapshot(workspace);
    const record = this.mounts.get(workspace);

    if (record?.state === 'mounted') {
      // Try to cache it
      this.cache.set(workspace, null);
      this.mounts.set(workspace, {
        ...record,
        state: 'cached',
        snapshot,
      });
    }
  }

  /**
   * Destroy a workspace — evict from cache, remove snapshot.
   */
  destroy(workspace: WorkspaceName): void {
    this.cache.delete(workspace);
    removeSnapshot(workspace);
    this.mounts.delete(workspace);
  }

  /**
   * Force destroy and cold-mount (bypass cache).
   */
  forceDestroy(workspace: WorkspaceName): void {
    this.destroy(workspace);
  }

  /**
   * Get mount record for a workspace.
   */
  getMountRecord(workspace: WorkspaceName): WorkspaceMountRecord | undefined {
    return this.mounts.get(workspace);
  }

  /**
   * Check if a workspace is currently active (mounted).
   */
  isMounted(workspace: WorkspaceName): boolean {
    const record = this.mounts.get(workspace);
    return record?.state === 'mounted';
  }

  /**
   * Check if a workspace is in the cache.
   */
  isCached(workspace: WorkspaceName): boolean {
    return this.cache.has(workspace);
  }

  /**
   * Get the number of cached workspaces.
   */
  get cachedCount(): number {
    return this.cache.size;
  }

  /**
   * Get all cached workspace names ordered LRU → MRU.
   */
  getCachedWorkspaces(): WorkspaceName[] {
    return this.cache.keysOrdered();
  }

  /**
   * Get the current transition state.
   */
  getTransition(): TransitionState {
    return { ...this.transition };
  }

  /**
   * Start a transition to a new workspace.
   */
  startTransition(from: WorkspaceName | null, to: WorkspaceName): void {
    this.transition = {
      isTransitioning: true,
      fromWorkspace: from,
      toWorkspace: to,
      startTime: Date.now(),
      duration: 150,
    };
  }

  /**
   * End a transition.
   */
  endTransition(): void {
    this.transition = {
      isTransitioning: false,
      fromWorkspace: null,
      toWorkspace: null,
      startTime: 0,
      duration: 150,
    };
  }

  /**
   * Check if a transition is complete based on elapsed time.
   */
  isTransitionComplete(): boolean {
    if (!this.transition.isTransitioning) return true;
    return Date.now() - this.transition.startTime >= this.transition.duration;
  }

  /**
   * Capture a state snapshot for a workspace.
   * Called when deactivating a workspace.
   */
  captureForWorkspace(workspace: WorkspaceName): void {
    // Snapshots are captured by individual workspaces via the captureSnapshot API.
    // This method ensures the snapshot key exists.
    if (!getSnapshot(workspace)) {
      captureSnapshot({
        workspaceId: workspace,
        scrollPosition: { x: 0, y: 0 },
        filters: {},
        sortConfig: null,
        selectionIds: [],
        timestamp: Date.now(),
      });
    }
  }

  /**
   * Get or create a mount record for a workspace.
   */
  ensureMounted(workspace: WorkspaceName): WorkspaceMountRecord {
    let record = this.mounts.get(workspace);
    if (!record) {
      record = {
        workspaceId: workspace,
        state: 'mounted',
        mountTimestamp: Date.now(),
        snapshot: null,
      };
      this.mounts.set(workspace, record);
    } else if (record.state === 'cached') {
      record = {
        ...record,
        state: 'mounted',
        mountTimestamp: Date.now(),
      };
      this.mounts.set(workspace, record);
    }
    return record;
  }

  // ===== Storage Persistence =====
  private loadFromStorage(): void {
    if (typeof window === 'undefined') return;
    try {
      const stored = sessionStorage.getItem('workspace-lifecycle');
      if (stored) {
        const data = JSON.parse(stored);
        // Restore active workspace tracking (not full cache)
        if (data.activeWorkspace) {
          this.ensureMounted(data.activeWorkspace as WorkspaceName);
        }
      }
    } catch {
      // Ignore storage errors
    }
  }

  /**
   * Reset all state (useful for testing).
   */
  reset(): void {
    this.cache.clear();
    this.mounts.clear();
    clearAllSnapshots();
    this.transition = {
      isTransitioning: false,
      fromWorkspace: null,
      toWorkspace: null,
      startTime: 0,
      duration: 150,
    };
  }
}

// ===== Singleton Instance =====
export const workspaceLifecycleManager = new WorkspaceLifecycleManager();

// ===== React Hook =====
export function useWorkspaceLifecycle() {
  // Hook provides reactive access to lifecycle state.
  // In a real implementation, this would subscribe to lifecycle events.
  return {
    manager: workspaceLifecycleManager,
  };
}
