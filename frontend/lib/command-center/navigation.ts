/**
 * Navigation Runtime - Stage 5 Command Center Platform
 *
 * Manages panel routing, workspace navigation, and deep link handling.
 * All navigation flows through graph nodes.
 */

import type { GraphNode } from '../graph';

// ===== Navigation Target =====
export interface NavigationTarget {
  /** Target type */
  type: 'workspace' | 'node' | 'panel' | 'external';
  /** Target identifier */
  id: string;
  /** Deep link URL */
  url: string;
  /** Workspace name (if applicable) */
  workspace?: string;
  /** Node ID (if applicable) */
  nodeId?: string;
}

// ===== Navigation History =====
export interface NavigationHistory {
  /** History entries */
  entries: NavigationTarget[];
  /** Current index */
  currentIndex: number;
}

// ===== Navigation Runtime =====
/**
 * Runtime for managing Command Center navigation.
 * Handles panel routing, workspace navigation, and deep link handling.
 */
export class NavigationRuntime {
  private history: NavigationTarget[] = [];
  private currentIndex = -1;
  private maxHistory = 100;

  constructor() {
    this.loadFromStorage();
  }

  // ===== Navigation =====
  /**
   * Navigate to a target
   */
  navigate(target: NavigationTarget): void {
    // Truncate forward history
    this.history = this.history.slice(0, this.currentIndex + 1);
    
    // Add new entry
    this.history.push(target);
    this.currentIndex++;
    
    // Limit history size
    if (this.history.length > this.maxHistory) {
      this.history.shift();
      this.currentIndex--;
    }
    
    this.saveToStorage();
  }

  /**
   * Navigate to a workspace
   */
  navigateToWorkspace(workspace: string, nodeId?: string): void {
    this.navigate({
      type: 'workspace',
      id: workspace,
      url: nodeId ? `/${workspace}?id=${nodeId}` : `/${workspace}`,
      workspace,
      nodeId,
    });
  }

  /**
   * Navigate to a graph node
   */
  navigateToNode(node: GraphNode): void {
    this.navigate({
      type: 'node',
      id: node.id,
      url: node.deep_link ?? `/${node.workspace}`,
      workspace: node.workspace,
      nodeId: node.id,
    });
  }

  /**
   * Navigate to a panel
   */
  navigateToPanel(panelId: string): void {
    this.navigate({
      type: 'panel',
      id: panelId,
      url: `/command-center?panel=${panelId}`,
    });
  }

  // ===== History =====
  /**
   * Go back in history
   */
  goBack(): NavigationTarget | null {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.saveToStorage();
      return this.history[this.currentIndex];
    }
    return null;
  }

  /**
   * Go forward in history
   */
  goForward(): NavigationTarget | null {
    if (this.currentIndex < this.history.length - 1) {
      this.currentIndex++;
      this.saveToStorage();
      return this.history[this.currentIndex];
    }
    return null;
  }

  /**
   * Get current target
   */
  getCurrent(): NavigationTarget | null {
    if (this.currentIndex >= 0 && this.currentIndex < this.history.length) {
      return this.history[this.currentIndex];
    }
    return null;
  }

  /**
   * Get full history
   */
  getHistory(): NavigationHistory {
    return {
      entries: [...this.history],
      currentIndex: this.currentIndex,
    };
  }

  /**
   * Check if can go back
   */
  canGoBack(): boolean {
    return this.currentIndex > 0;
  }

  /**
   * Check if can go forward
   */
  canGoForward(): boolean {
    return this.currentIndex < this.history.length - 1;
  }

  // ===== Deep Link Parsing =====
  /**
   * Parse a deep link URL to extract navigation target
   */
  parseDeepLink(url: string): NavigationTarget | null {
    try {
      const urlObj = new URL(url, 'http://localhost');
      const path = urlObj.pathname;
      const search = urlObj.searchParams;

      // Workspace links: /workspace?id=xyz
      const workspaceMatch = path.match(/^\/([a-z-]+)(\?.*)?$/);
      if (workspaceMatch) {
        const workspace = workspaceMatch[1];
        const nodeId = search.get('id') ?? undefined;
        return {
          type: 'workspace',
          id: nodeId ?? workspace,
          url,
          workspace,
          nodeId,
        };
      }

      // Command center links: /command-center?panel=xyz
      if (path === '/command-center') {
        const panelId = search.get('panel') ?? 'graph';
        return {
          type: 'panel',
          id: panelId,
          url,
        };
      }

      return null;
    } catch {
      return null;
    }
  }

  // ===== Storage =====
  private saveToStorage(): void {
    if (typeof window === 'undefined') return;

    try {
      const data = {
        history: this.history,
        currentIndex: this.currentIndex,
      };
      sessionStorage.setItem('command-center-navigation', JSON.stringify(data));
    } catch {
      // Ignore storage errors
    }
  }

  private loadFromStorage(): void {
    if (typeof window === 'undefined') return;

    try {
      const stored = sessionStorage.getItem('command-center-navigation');
      if (stored) {
        const data = JSON.parse(stored);
        this.history = data.history ?? [];
        this.currentIndex = data.currentIndex ?? -1;
      }
    } catch {
      // Ignore parse errors
    }
  }

  // ===== Reset =====
  /**
   * Reset navigation state
   */
  reset(): void {
    this.history = [];
    this.currentIndex = -1;
    this.saveToStorage();
  }
}

// ===== Convenience Export =====
export const navigationRuntime = new NavigationRuntime();