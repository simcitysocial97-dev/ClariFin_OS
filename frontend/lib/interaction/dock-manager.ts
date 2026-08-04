/**
 * Dock Manager - Milestone 9 Interaction Polish
 *
 * Manages dockable panel state across the OS shell.
 * Supports dock (attach to edge), undock (float), and pinned state.
 * Persistence is handled by StateRuntime per architecture §2.4.
 */

export type DockPosition = 'left' | 'right' | 'bottom' | 'top' | 'center';
export type DockState = 'docked' | 'floating' | 'collapsed' | 'hidden';

export interface DockItem {
  id: string;
  label: string;
  position: DockPosition;
  state: DockState;
  size: { width: number; height: number };
  zIndex: number;
  pinned: boolean;
  visible: boolean;
}

export interface DockLayout {
  items: DockItem[];
  activeId: string | null;
}

const DEFAULT_LAYOUT: DockLayout = {
  items: [],
  activeId: null,
};

class DockManager {
  private layout: DockLayout = { ...DEFAULT_LAYOUT, items: [] };
  private listeners: Set<(layout: DockLayout) => void> = new Set();

  register(item: Omit<DockItem, 'zIndex'>): DockItem {
    const existing = this.layout.items.find(i => i.id === item.id);
    if (existing) {
      return existing;
    }

    const maxZ = this.layout.items.reduce((max, i) => Math.max(max, i.zIndex), 0);
    const dockItem: DockItem = {
      ...item,
      zIndex: maxZ + 1,
    };

    this.layout = {
      ...this.layout,
      items: [...this.layout.items, dockItem],
    };
    this.notify();
    return dockItem;
  }

  unregister(id: string): boolean {
    const existed = this.layout.items.some(i => i.id === id);
    this.layout = {
      ...this.layout,
      items: this.layout.items.filter(i => i.id !== id),
      activeId: this.layout.activeId === id ? null : this.layout.activeId,
    };
    this.notify();
    return existed;
  }

  get(id: string): DockItem | undefined {
    return this.layout.items.find(i => i.id === id);
  }

  getAll(): DockItem[] {
    return [...this.layout.items];
  }

  getDocked(): DockItem[] {
    return this.layout.items.filter(i => i.state === 'docked' && i.visible);
  }

  getFloating(): DockItem[] {
    return this.layout.items.filter(i => i.state === 'floating');
  }

  getVisible(): DockItem[] {
    return this.layout.items.filter(i => i.visible);
  }

  getActive(): DockItem | undefined {
    return this.layout.activeId
      ? this.layout.items.find(i => i.id === this.layout.activeId)
      : undefined;
  }

  setActive(id: string | null): void {
    this.layout = { ...this.layout, activeId: id };
    this.notify();
  }

  dock(id: string, position: DockPosition): void {
    this.layout = {
      ...this.layout,
      items: this.layout.items.map(item =>
        item.id === id ? { ...item, state: 'docked', position, visible: true } : item,
      ),
    };
    this.notify();
  }

  float(id: string): void {
    this.layout = {
      ...this.layout,
      items: this.layout.items.map(item =>
        item.id === id ? { ...item, state: 'floating', visible: true } : item,
      ),
    };
    this.notify();
  }

  collapse(id: string): void {
    this.layout = {
      ...this.layout,
      items: this.layout.items.map(item =>
        item.id === id ? { ...item, state: 'collapsed', visible: false } : item,
      ),
    };
    if (this.layout.activeId === id) {
      this.layout = { ...this.layout, activeId: null };
    }
    this.notify();
  }

  hide(id: string): void {
    this.layout = {
      ...this.layout,
      items: this.layout.items.map(item =>
        item.id === id ? { ...item, state: 'hidden', visible: false } : item,
      ),
    };
    this.notify();
  }

  show(id: string): void {
    this.layout = {
      ...this.layout,
      items: this.layout.items.map(item =>
        item.id === id ? { ...item, visible: true, state: 'docked', position: 'right' } : item,
      ),
    };
    this.notify();
  }

  setSize(id: string, size: { width: number; height: number }): void {
    this.layout = {
      ...this.layout,
      items: this.layout.items.map(item =>
        item.id === id ? { ...item, size } : item,
      ),
    };
    this.notify();
  }

  setPosition(id: string, position: DockPosition): void {
    this.layout = {
      ...this.layout,
      items: this.layout.items.map(item =>
        item.id === id ? { ...item, position } : item,
      ),
    };
    this.notify();
  }

  pin(id: string): void {
    this.layout = {
      ...this.layout,
      items: this.layout.items.map(item =>
        item.id === id ? { ...item, pinned: true } : item,
      ),
    };
    this.notify();
  }

  unpin(id: string): void {
    this.layout = {
      ...this.layout,
      items: this.layout.items.map(item =>
        item.id === id ? { ...item, pinned: false } : item,
      ),
    };
    this.notify();
  }

  isPinned(id: string): boolean {
    return this.layout.items.find(i => i.id === id)?.pinned ?? false;
  }

  getLayout(): DockLayout {
    return {
      ...this.layout,
      items: [...this.layout.items],
    };
  }

  saveLayout(): DockLayout {
    return this.getLayout();
  }

restoreLayout(layout: DockLayout): void {
     this.layout = { ...layout, items: [...layout.items] };
     this.notify();
   }

   reorder(itemIds: string[]): void {
     const itemMap = new Map(this.layout.items.map(item => [item.id, item]));
     const reordered = itemIds
       .map(id => itemMap.get(id))
       .filter((item): item is DockItem => item !== undefined);
     const remaining = this.layout.items.filter(item => !itemIds.includes(item.id));
     this.layout = {
       ...this.layout,
       items: [...reordered, ...remaining],
     };
     this.notify();
   }

   subscribe(listener: (layout: DockLayout) => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notify(): void {
    for (const listener of this.listeners) {
      try {
        listener(this.getLayout());
      } catch (err) {
        console.error('[DockManager] Listener error:', err);
      }
    }
  }

  reset(): void {
    this.layout = { ...DEFAULT_LAYOUT, items: [] };
    this.notify();
  }
}

const dockManager = new DockManager();

export { dockManager, DockManager };
