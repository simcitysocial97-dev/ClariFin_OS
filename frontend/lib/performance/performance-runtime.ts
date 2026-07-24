/**
 * Performance Runtime - Stage 7.5 Runtime Consolidation
 *
 * Shared caching, memoization, and synchronization for all workspaces.
 * Provides a unified performance layer for the Financial Operating System.
 *
 * Architecture: PerformanceRuntime → Cache/Memoization → Workspace Data
 */

// ===== Cache Types =====
export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in milliseconds
  hits: number;
}

export interface CacheStats {
  size: number;
  hits: number;
  misses: number;
  evictions: number;
}

// ===== Memoization Types =====
export interface MemoEntry<T> {
  result: T;
  args: unknown[];
  timestamp: number;
}

// ===== Synchronization Types =====
export type SyncStatus = 'idle' | 'syncing' | 'error' | 'success';

export interface SyncState {
  status: SyncStatus;
  lastSync: Date | null;
  error: string | null;
  pendingChanges: number;
}

// ===== Performance Runtime =====
/**
 * Main runtime for performance management across all workspaces.
 * Provides caching, memoization, and synchronization capabilities.
 */
export class PerformanceRuntime {
  private cache: Map<string, CacheEntry<unknown>> = new Map();
  private memoCache: Map<string, MemoEntry<unknown>> = new Map();
  private syncStates: Map<string, SyncState> = new Map();
  private stats: CacheStats = { size: 0, hits: 0, misses: 0, evictions: 0 };

  // ===== Cache Operations =====
  /**
   * Set a cache entry
   */
  set<T>(key: string, data: T, ttl: number = 300000): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
      hits: 0,
    });
    this.stats.size = this.cache.size;
  }

  /**
   * Get a cache entry
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) {
      this.stats.misses++;
      return null;
    }

    // Check TTL
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      this.stats.evictions++;
      this.stats.size = this.cache.size;
      this.stats.misses++;
      return null;
    }

    entry.hits++;
    this.stats.hits++;
    return entry.data as T;
  }

  /**
   * Check if cache has a valid entry
   */
  has(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return false;
    return Date.now() - entry.timestamp <= entry.ttl;
  }

  /**
   * Delete a cache entry
   */
  delete(key: string): boolean {
    const result = this.cache.delete(key);
    this.stats.size = this.cache.size;
    return result;
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
    this.stats.size = 0;
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): CacheStats {
    return { ...this.stats };
  }

  // ===== Memoization Operations =====
  /**
   * Memoize a function result
   */
  memoize<T>(key: string, args: unknown[], result: T): void {
    this.memoCache.set(key, {
      result,
      args,
      timestamp: Date.now(),
    });
  }

  /**
   * Get memoized result if args match
   */
  getMemoized<T>(key: string, args: unknown[]): T | null {
    const entry = this.memoCache.get(key);
    if (!entry) return null;

    // Check if args match
    if (JSON.stringify(entry.args) === JSON.stringify(args)) {
      return entry.result as T;
    }

    return null;
  }

  /**
   * Clear memoization cache
   */
  clearMemo(): void {
    this.memoCache.clear();
  }

  // ===== Synchronization Operations =====
  /**
   * Get sync state for a workspace
   */
  getSyncState(workspace: string): SyncState {
    return (
      this.syncStates.get(workspace) ?? {
        status: 'idle',
        lastSync: null,
        error: null,
        pendingChanges: 0,
      }
    );
  }

  /**
   * Set sync state for a workspace
   */
  setSyncState(workspace: string, state: Partial<SyncState>): void {
    const current = this.getSyncState(workspace);
    this.syncStates.set(workspace, { ...current, ...state });
  }

  /**
   * Start syncing for a workspace
   */
  startSync(workspace: string): void {
    this.setSyncState(workspace, { status: 'syncing' });
  }

  /**
   * Complete syncing for a workspace
   */
  completeSync(workspace: string, error?: string): void {
    this.setSyncState(workspace, {
      status: error ? 'error' : 'success',
      lastSync: new Date(),
      error: error ?? null,
    });
  }

  /**
   * Increment pending changes for a workspace
   */
  incrementPending(workspace: string): void {
    const current = this.getSyncState(workspace);
    this.setSyncState(workspace, {
      pendingChanges: current.pendingChanges + 1,
    });
  }

  /**
   * Decrement pending changes for a workspace
   */
  decrementPending(workspace: string): void {
    const current = this.getSyncState(workspace);
    this.setSyncState(workspace, {
      pendingChanges: Math.max(0, current.pendingChanges - 1),
    });
  }

  // ===== Cleanup =====
  /**
   * Clean up expired cache entries
   */
  cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key);
        this.stats.evictions++;
      }
    }
    this.stats.size = this.cache.size;
  }

  /**
   * Reset the runtime
   */
  reset(): void {
    this.cache.clear();
    this.memoCache.clear();
    this.syncStates.clear();
    this.stats = { size: 0, hits: 0, misses: 0, evictions: 0 };
  }
}

// ===== Convenience Export =====
export const performanceRuntime = new PerformanceRuntime();