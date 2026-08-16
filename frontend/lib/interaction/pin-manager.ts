/**
 * Pin Manager - Milestone 9 Interaction Polish
 *
 * Manages pinned workspaces, entities, and shortcuts.
 * Pinned items provide quick access and are persisted via StateRuntime.
 *
 * Persistence scope: per-session cross-session via StateRuntime (architecture §2.4).
 */

export type PinType = 'workspace' | 'entity' | 'command' | 'shortcut';

export interface PinnedItem {
  id: string;
  type: PinType;
  label: string;
  icon?: string;
  order: number;
  pinnedAt: number;
  metadata?: Record<string, unknown>;
}

const STORAGE_KEY = 'os-pinned-items';

class PinManager {
  private items: PinnedItem[] = [];
  private listeners: Set<(items: PinnedItem[]) => void> = new Set();

  load(): void {
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored) as PinnedItem[];
          this.items = parsed;
          this.notify();
        }
      } catch {
        // Ignore storage errors
      }
    }
  }

  pin(item: Omit<PinnedItem, 'order' | 'pinnedAt'>): PinnedItem {
    const existing = this.items.find(i => i.id === item.id && i.type === item.type);
    if (existing) {
      return existing;
    }

    const maxOrder = this.items.reduce((max, i) => Math.max(max, i.order), -1);
    const pinnedItem: PinnedItem = {
      ...item,
      order: maxOrder + 1,
      pinnedAt: Date.now(),
    };

    this.items = [...this.items, pinnedItem];
    this.save();
    this.notify();
    return pinnedItem;
  }

  unpin(id: string, type?: PinType): boolean {
    const existed = type
      ? this.items.some(i => i.id === id && i.type === type)
      : this.items.some(i => i.id === id);

    this.items = this.items.filter(i => {
      if (type) return !(i.id === id && i.type === type);
      return i.id !== id;
    });

    if (existed) {
      this.save();
      this.notify();
    }
    return existed;
  }

  get(id: string, type?: PinType): PinnedItem | undefined {
    if (type) {
      return this.items.find(i => i.id === id && i.type === type);
    }
    return this.items.find(i => i.id === id);
  }

  getAll(): PinnedItem[] {
    return [...this.items];
  }

  getByType(type: PinType): PinnedItem[] {
    return this.items.filter(i => i.type === type);
  }

  getWorkspaces(): PinnedItem[] {
    return this.getByType('workspace');
  }

  getEntities(): PinnedItem[] {
    return this.getByType('entity');
  }

  getCommands(): PinnedItem[] {
    return this.getByType('command');
  }

  getShortcuts(): PinnedItem[] {
    return this.getByType('shortcut');
  }

  isPinned(id: string, type?: PinType): boolean {
    if (type) {
      return this.items.some(i => i.id === id && i.type === type);
    }
    return this.items.some(i => i.id === id);
  }

  reorder(ids: string[]): void {
    const idToItem = new Map(this.items.map(i => [i.id, i]));
    const reordered: PinnedItem[] = [];

    for (let i = 0; i < ids.length; i++) {
      const item = idToItem.get(ids[i]);
      if (item) {
        reordered.push({ ...item, order: i });
      }
    }

    for (const item of this.items) {
      if (!ids.includes(item.id)) {
        reordered.push({ ...item, order: reordered.length });
      }
    }

    this.items = reordered.sort((a, b) => a.order - b.order);
    this.save();
    this.notify();
  }

  clear(): void {
    this.items = [];
    this.save();
    this.notify();
  }

  private save(): void {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(this.items));
      } catch {
        // Ignore storage errors
      }
    }
  }

  subscribe(listener: (items: PinnedItem[]) => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notify(): void {
    for (const listener of this.listeners) {
      try {
        listener(this.getAll());
      } catch (err) {
        console.error('[PinManager] Listener error:', err);
      }
    }
  }

  reset(): void {
    this.items = [];
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch {
        // Ignore
      }
    }
    this.notify();
  }
}

const pinManager = new PinManager();

export { pinManager, PinManager };
