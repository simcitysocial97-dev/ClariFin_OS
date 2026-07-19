/**
 * Layout Runtime - Stage 5 Command Center Platform
 *
 * Manages panel docking, resizing, collapsing, favorites, and saved layouts.
 * No business logic - pure UI state management.
 */

import type { PanelId } from './runtime';

// ===== Panel Position =====
export interface PanelPosition {
  x: number;
  y: number;
  width: number;
  height: number;
  zIndex: number;
}

// ===== Layout Snapshot =====
export interface LayoutSnapshot {
  positions: Record<PanelId, PanelPosition>;
  collapsed: Record<PanelId, boolean>;
  favorites: string[];
}

// ===== Layout Runtime =====
/**
 * Runtime for managing Command Center layout state.
 * Handles docking, resize, collapse, favorites, and saved layouts.
 */
export class LayoutRuntime {
  private positions: Map<PanelId, PanelPosition> = new Map();
  private collapsed: Map<PanelId, boolean> = new Map();
  private favorites: string[] = [];
  private savedLayouts: Map<string, LayoutSnapshot> = new Map();
  private nextZIndex = 100;

  constructor() {
    this.loadFromStorage();
  }

  // ===== Position Management =====
  /**
   * Get panel position
   */
  getPosition(panelId: PanelId): PanelPosition | undefined {
    return this.positions.get(panelId);
  }

  /**
   * Set panel position
   */
  setPosition(panelId: PanelId, position: Partial<PanelPosition>): void {
    const current = this.positions.get(panelId) ?? this.defaultPosition(panelId);
    this.positions.set(panelId, { ...current, ...position });
    this.saveToStorage();
  }

  /**
   * Bring panel to front
   */
  bringToFront(panelId: PanelId): void {
    const pos = this.positions.get(panelId);
    if (pos) {
      pos.zIndex = ++this.nextZIndex;
      this.positions.set(panelId, { ...pos });
      this.saveToStorage();
    }
  }

  // ===== Collapse Management =====
  /**
   * Check if panel is collapsed
   */
  isCollapsed(panelId: PanelId): boolean {
    return this.collapsed.get(panelId) ?? false;
  }

  /**
   * Set panel collapsed state
   */
  setCollapsed(panelId: PanelId, collapsed: boolean): void {
    this.collapsed.set(panelId, collapsed);
    this.saveToStorage();
  }

  /**
   * Toggle panel collapsed state
   */
  toggleCollapsed(panelId: PanelId): void {
    this.setCollapsed(panelId, !this.isCollapsed(panelId));
  }

  // ===== Favorites =====
  /**
   * Get all favorites
   */
  getFavorites(): string[] {
    return [...this.favorites];
  }

  /**
   * Add to favorites
   */
  addFavorite(nodeId: string): void {
    if (!this.favorites.includes(nodeId)) {
      this.favorites.push(nodeId);
      this.saveToStorage();
    }
  }

  /**
   * Remove from favorites
   */
  removeFavorite(nodeId: string): void {
    this.favorites = this.favorites.filter(id => id !== nodeId);
    this.saveToStorage();
  }

  /**
   * Check if node is favorited
   */
  isFavorited(nodeId: string): boolean {
    return this.favorites.includes(nodeId);
  }

  // ===== Saved Layouts =====
  /**
   * Save current layout
   */
  saveLayout(name: string): void {
    const snapshot: LayoutSnapshot = {
      positions: Object.fromEntries(this.positions.entries()) as Record<PanelId, PanelPosition>,
      collapsed: Object.fromEntries(this.collapsed.entries()) as Record<PanelId, boolean>,
      favorites: [...this.favorites],
    };
    this.savedLayouts.set(name, snapshot);
    this.saveToStorage();
  }

  /**
   * Load saved layout
   */
  loadLayout(name: string): boolean {
    const snapshot = this.savedLayouts.get(name);
    if (snapshot) {
      this.positions = new Map(Object.entries(snapshot.positions) as [PanelId, PanelPosition][]);
      this.collapsed = new Map(Object.entries(snapshot.collapsed) as [PanelId, boolean][]);
      this.favorites = [...snapshot.favorites];
      this.saveToStorage();
      return true;
    }
    return false;
  }

  /**
   * Get all saved layout names
   */
  getSavedLayoutNames(): string[] {
    return Array.from(this.savedLayouts.keys());
  }

  /**
   * Delete saved layout
   */
  deleteLayout(name: string): boolean {
    return this.savedLayouts.delete(name);
  }

  // ===== Reset =====
  /**
   * Reset to default layout
   */
  reset(): void {
    this.positions.clear();
    this.collapsed.clear();
    this.favorites = [];
    this.savedLayouts.clear();
    this.nextZIndex = 100;
    this.saveToStorage();
  }

  // ===== Storage =====
  private loadFromStorage(): void {
    if (typeof window === 'undefined') return;

    try {
      const stored = localStorage.getItem('command-center-layout-state');
      if (stored) {
        const data = JSON.parse(stored);
        if (data.positions) {
          this.positions = new Map(Object.entries(data.positions) as [PanelId, PanelPosition][]);
        }
        if (data.collapsed) {
          this.collapsed = new Map(Object.entries(data.collapsed) as [PanelId, boolean][]);
        }
        if (data.favorites) {
          this.favorites = data.favorites;
        }
        if (data.savedLayouts) {
          this.savedLayouts = new Map(Object.entries(data.savedLayouts));
        }
      }
    } catch {
      // Ignore parse errors
    }
  }

  private saveToStorage(): void {
    if (typeof window === 'undefined') return;

    try {
      const data = {
        positions: Object.fromEntries(this.positions.entries()),
        collapsed: Object.fromEntries(this.collapsed.entries()),
        favorites: this.favorites,
        savedLayouts: Object.fromEntries(this.savedLayouts.entries()),
      };
      localStorage.setItem('command-center-layout-state', JSON.stringify(data));
    } catch {
      // Ignore storage errors
    }
  }

  // ===== Defaults =====
  private defaultPosition(panelId: PanelId): PanelPosition {
    const defaults: Record<PanelId, PanelPosition> = {
      graph: { x: 0, y: 0, width: 800, height: 600, zIndex: 100 },
      timeline: { x: 800, y: 0, width: 400, height: 300, zIndex: 101 },
      insights: { x: 0, y: 600, width: 300, height: 400, zIndex: 102 },
      search: { x: 300, y: 600, width: 300, height: 200, zIndex: 103 },
      preview: { x: 600, y: 600, width: 350, height: 350, zIndex: 104 },
      context: { x: 0, y: 500, width: 350, height: 400, zIndex: 105 },
    };
    return defaults[panelId] ?? { x: 0, y: 0, width: 300, height: 300, zIndex: 100 };
  }
}

// ===== Convenience Export =====
export const layoutRuntime = new LayoutRuntime();