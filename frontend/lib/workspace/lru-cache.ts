/**
 * LRU Cache - Least Recently Used eviction strategy.
 *
 * Implements the cache policy required by WorkspaceHost:
 * - Max N entries (default 5)
 * - On access, entry becomes most recently used
 * - On eviction, least recently used entry is removed
 */

export interface LRUEntry<V> {
  key: string;
  value: V;
  lastAccessed: number;
}

export class LRUCache<K extends string, V> {
  private readonly _maxSize: number;
  private readonly _entries = new Map<K, LRUEntry<V>>();
  private _accessCounter = 0;

  constructor(maxSize: number = 5) {
    this._maxSize = maxSize;
  }

  get size(): number {
    return this._entries.size;
  }

  has(key: K): boolean {
    return this._entries.has(key);
  }

  /**
   * Get an entry and promote it to most-recently-used.
   * Returns undefined if not present.
   */
  get(key: K): V | undefined {
    const entry = this._entries.get(key);
    if (!entry) return undefined;
    this._promote(key);
    return entry.value;
  }

  /**
   * Put an entry. If cache is full, evict the LRU entry first.
   */
  set(key: K, value: V): void {
    if (this._entries.has(key)) {
      this._entries.get(key)!.value = value;
      this._promote(key);
      return;
    }
    if (this._entries.size >= this._maxSize) {
      this._evict();
    }
    this._accessCounter++;
    this._entries.set(key, { key, value, lastAccessed: this._accessCounter });
  }

  /**
   * Remove a specific key.
   */
  delete(key: K): boolean {
    return this._entries.delete(key);
  }

  /**
   * Clear the entire cache.
   */
  clear(): void {
    this._entries.clear();
    this._accessCounter = 0;
  }

  /**
   * Get the key of the least recently used entry, or null if empty.
   */
  getLRUKey(): K | null {
    if (this._entries.size === 0) return null;
    let lruKey: K | null = null;
    let lruTime = Infinity;
    for (const [k, entry] of this._entries.entries()) {
      if (entry.lastAccessed < lruTime) {
        lruTime = entry.lastAccessed;
        lruKey = k;
      }
    }
    return lruKey;
  }

  /**
   * Get all keys ordered from least recently used to most recently used.
   */
  keysOrdered(): K[] {
    return Array.from(this._entries.keys());
  }

  // ===== Private helpers =====

  private _promote(key: K): void {
    const entry = this._entries.get(key);
    if (!entry) return;
    this._accessCounter++;
    this._entries.set(key, { ...entry, lastAccessed: this._accessCounter });
  }

  private _evict(): void {
    const lruKey = this.getLRUKey();
    if (lruKey !== null) {
      this._entries.delete(lruKey);
    }
  }
}
