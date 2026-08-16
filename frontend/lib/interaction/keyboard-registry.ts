/**
 * Keyboard Registry - Stage 8F Financial OS Interaction Layer
 *
 * Registry for all keyboard shortcuts.
 * Tracks usage, favorites, and aliases.
 */

import type { KeyboardShortcut } from './interaction-types';
import type { WorkspaceName } from '../workspace';
import { commandRuntime } from '../command/command-runtime';

// ===== Shortcut Usage Tracking =====
interface ShortcutUsage {
  shortcut: KeyboardShortcut;
  lastUsed: number;
  useCount: number;
}

// ===== Keyboard Registry =====
class KeyboardRegistry {
  private shortcuts: Map<string, KeyboardShortcut> = new Map();
  private usage: Map<string, ShortcutUsage> = new Map();
  private favorites: Set<string> = new Set();
  private aliases: Map<string, string> = new Map(); // alias -> shortcut key

  // ===== Registration =====
  /**
   * Register a keyboard shortcut
   */
  register(shortcut: KeyboardShortcut): void {
    const key = this.getShortcutKey(shortcut);
    this.shortcuts.set(key, shortcut);
    this.usage.set(key, {
      shortcut,
      lastUsed: 0,
      useCount: 0,
    });
  }

  /**
   * Register multiple shortcuts
   */
  registerAll(shortcuts: KeyboardShortcut[]): void {
    for (const shortcut of shortcuts) {
      this.register(shortcut);
    }
  }

  /**
   * Unregister a keyboard shortcut
   */
  unregister(key: string): boolean {
    return this.shortcuts.delete(key);
  }

  /**
   * Get a shortcut by key
   */
  get(key: string): KeyboardShortcut | undefined {
    return this.shortcuts.get(key);
  }

  /**
   * Get all registered shortcuts
   */
  getAll(): KeyboardShortcut[] {
    return Array.from(this.shortcuts.values());
  }

  /**
   * Get shortcuts by category
   */
  getByCategory(category: KeyboardShortcut['category']): KeyboardShortcut[] {
    return this.getAll().filter(s => s.category === category);
  }

  // ===== Usage Tracking =====
  /**
   * Record shortcut usage
   */
  recordUsage(shortcut: KeyboardShortcut): void {
    const key = this.getShortcutKey(shortcut);
    const usage = this.usage.get(key);
    if (usage) {
      usage.lastUsed = Date.now();
      usage.useCount++;
    }
  }

  /**
   * Get recently used shortcuts
   */
  getRecent(limit = 10): KeyboardShortcut[] {
    return this.getAll()
      .map(s => ({
        shortcut: s,
        lastUsed: this.usage.get(this.getShortcutKey(s))?.lastUsed ?? 0,
      }))
      .sort((a, b) => b.lastUsed - a.lastUsed)
      .slice(0, limit)
      .map(item => item.shortcut);
  }

  /**
   * Get most used shortcuts
   */
  getMostUsed(limit = 10): KeyboardShortcut[] {
    return this.getAll()
      .map(s => ({
        shortcut: s,
        useCount: this.usage.get(this.getShortcutKey(s))?.useCount ?? 0,
      }))
      .sort((a, b) => b.useCount - a.useCount)
      .slice(0, limit)
      .map(item => item.shortcut);
  }

  // ===== Favorites =====
  /**
   * Add a shortcut to favorites
   */
  addToFavorites(shortcut: KeyboardShortcut): void {
    this.favorites.add(this.getShortcutKey(shortcut));
  }

  /**
   * Remove a shortcut from favorites
   */
  removeFromFavorites(shortcut: KeyboardShortcut): void {
    this.favorites.delete(this.getShortcutKey(shortcut));
  }

  /**
   * Get favorite shortcuts
   */
  getFavorites(): KeyboardShortcut[] {
    return this.getAll().filter(s => this.favorites.has(this.getShortcutKey(s)));
  }

  // ===== Aliases =====
  /**
   * Register an alias for a shortcut
   */
  addAlias(alias: string, shortcut: KeyboardShortcut): void {
    this.aliases.set(alias.toLowerCase(), this.getShortcutKey(shortcut));
  }

  /**
   * Resolve an alias to a shortcut
   */
  resolveAlias(alias: string): KeyboardShortcut | undefined {
    const key = this.aliases.get(alias.toLowerCase());
    return key ? this.shortcuts.get(key) : undefined;
  }

  // ===== Workspace Shortcuts =====
  /**
   * Get shortcuts for a specific workspace
   */
  getByWorkspace(workspace: WorkspaceName): KeyboardShortcut[] {
    return this.getAll().filter(s => s.description?.includes(workspace) ?? false);
  }

  // ===== Private Methods =====
  private getShortcutKey(shortcut: KeyboardShortcut): string {
    const parts: string[] = [];
    if (shortcut.ctrl) parts.push('ctrl');
    if (shortcut.cmd) parts.push('cmd');
    if (shortcut.alt) parts.push('alt');
    if (shortcut.shift) parts.push('shift');
    parts.push(shortcut.key.toLowerCase());
    return parts.join('+');
  }

  // ===== Reset =====
  /**
   * Reset the registry
   */
  reset(): void {
    this.shortcuts.clear();
    this.usage.clear();
    this.favorites.clear();
    this.aliases.clear();
  }
}

// ===== Singleton Export =====
export const keyboardRegistry = new KeyboardRegistry();

// ===== Default Shortcuts =====
/**
 * Create default OS-level shortcuts
 */
export function createDefaultShortcuts(
  onWorkspaceSwitch: (workspace: WorkspaceName) => void,
  _onCommandPaletteOpen: () => void,
  onGlobalSearchOpen: () => void,
  onSelectionClear: () => void,
  onGraphFocus: () => void,
  onOverlayToggle: () => void,
  onTimelineToggle: () => void,
  onInspectorToggle: () => void,
): KeyboardShortcut[] {
  return [
    // Command Palette
    {
      key: 'k',
      ctrl: true,
      handler: async () => {
        await commandRuntime.execute('cmd:open-palette');
      },
      description: 'Open command palette',
      category: 'system',
    },
    // Global Search
    {
      key: '/',
      handler: () => onGlobalSearchOpen(),
      description: 'Open global search',
      category: 'search',
    },
    // Clear Selection
    {
      key: 'Escape',
      handler: () => onSelectionClear(),
      description: 'Clear selection',
      category: 'selection',
    },
    // Focus Node
    {
      key: 'f',
      handler: () => onGraphFocus(),
      description: 'Focus selected node',
      category: 'graph',
    },
    // Toggle Overlays
    {
      key: 'g',
      handler: () => onOverlayToggle(),
      description: 'Toggle graph overlays',
      category: 'overlay',
    },
    // Timeline
    {
      key: 't',
      handler: () => onTimelineToggle(),
      description: 'Toggle timeline',
      category: 'workspace',
    },
    // Inspector
    {
      key: 'i',
      handler: () => onInspectorToggle(),
      description: 'Toggle inspector',
      category: 'workspace',
    },
    // Shortcut Overlay
    {
      key: '?',
      handler: () => {
        const event = new CustomEvent('os-show-shortcuts');
        window.dispatchEvent(event);
      },
      description: 'Show shortcut overlay',
      category: 'system',
    },
    // Workspace Switching (1-9)
    ...[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => ({
      key: num.toString(),
      ctrl: true,
      handler: () => {
        const workspaces: WorkspaceName[] = [
          'dashboard',
          'transactions',
          'accounts',
          'net-worth',
          'cashflow',
          'investments',
          'loans',
          'behaviour',
          'forecast',
        ];
        if (workspaces[num - 1]) {
          onWorkspaceSwitch(workspaces[num - 1]);
        }
      },
      description: `Switch to workspace ${num}`,
      category: 'workspace' as const,
    })),
    // Arrow Keys for Selection
    {
      key: 'ArrowUp',
      handler: () => {
        const event = new CustomEvent('os-selection-up');
        window.dispatchEvent(event);
      },
      description: 'Select previous item',
      category: 'selection',
    },
    {
      key: 'ArrowDown',
      handler: () => {
        const event = new CustomEvent('os-selection-down');
        window.dispatchEvent(event);
      },
      description: 'Select next item',
      category: 'selection',
    },
    {
      key: 'ArrowLeft',
      handler: () => {
        const event = new CustomEvent('os-selection-left');
        window.dispatchEvent(event);
      },
      description: 'Select parent item',
      category: 'selection',
    },
    {
      key: 'ArrowRight',
      handler: () => {
        const event = new CustomEvent('os-selection-right');
        window.dispatchEvent(event);
      },
      description: 'Select child item',
      category: 'selection',
    },
    // Enter for Inspect
    {
      key: 'Enter',
      handler: () => {
        const event = new CustomEvent('os-inspect');
        window.dispatchEvent(event);
      },
      description: 'Inspect selected item',
      category: 'selection',
    },
    // Space for Center Graph
    {
      key: ' ',
      handler: () => {
        const event = new CustomEvent('os-center-graph');
        window.dispatchEvent(event);
      },
      description: 'Center graph view',
      category: 'graph',
    },
    // Tab for Focus Cycle
    {
      key: 'Tab',
      handler: () => {
        const event = new CustomEvent('os-focus-next');
        window.dispatchEvent(event);
      },
      description: 'Focus next element',
      category: 'system',
    },
  ];
}