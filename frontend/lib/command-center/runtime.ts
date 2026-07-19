/**
 * Command Center Runtime - Stage 5 Command Center Platform
 *
 * Composition layer built on top of the Financial Graph Runtime.
 * Manages workspace registration, panel routing, graph synchronization,
 * node focus, workspace preview, and layout persistence.
 *
 * Architecture: FinancialGraphRuntime → CommandCenterRuntime → UI
 */

import {
  FinancialGraphRuntime,
  type GraphResult,
  type GraphSelection,
  type GraphMetrics,
  type ExplainabilityPayload,
  type TracePath,
} from '../graph';
import {
  IntelligenceRuntime,
  type IntelligenceResult,
  type IntelligenceContext,
  type IntelligenceConfig,
} from '../intelligence';

// ===== Panel Types =====
export type PanelId = 'graph' | 'timeline' | 'insights' | 'search' | 'preview' | 'context';

export interface PanelState {
  id: PanelId;
  visible: boolean;
  width?: number;
  height?: number;
}

// ===== Layout Configuration =====
export interface LayoutConfig {
  panels: Record<PanelId, PanelState>;
  favorites: string[];
  savedLayouts: Record<string, Record<PanelId, PanelState>>;
}

// ===== Workspace Registration =====
export interface WorkspaceRegistration {
  name: string;
  label: string;
  icon?: string;
  deepLink: string;
  viewModelKey: string;
}

// ===== Command Center Runtime =====
/**
 * Main runtime for the Command Center Platform.
 * Composes the Financial Graph Runtime and provides UI-oriented APIs.
 */
export class CommandCenterRuntime {
  private graphRuntime: FinancialGraphRuntime;
  private layout: LayoutConfig;
  private workspaces: Map<string, WorkspaceRegistration> = new Map();
  private currentGraph: GraphResult | null = null;

  constructor(graphRuntime?: FinancialGraphRuntime) {
    this.graphRuntime = graphRuntime ?? new FinancialGraphRuntime();
    this.layout = this.loadLayout();
  }

  // ===== Workspace Registration =====
  /**
   * Register a workspace with the command center
   */
  registerWorkspace(registration: WorkspaceRegistration): void {
    this.workspaces.set(registration.name, registration);
  }

  /**
   * Get all registered workspaces
   */
  getWorkspaces(): WorkspaceRegistration[] {
    return Array.from(this.workspaces.values());
  }

  /**
   * Get a specific workspace registration
   */
  getWorkspace(name: string): WorkspaceRegistration | undefined {
    return this.workspaces.get(name);
  }

  // ===== Graph Operations =====
  /**
   * Build the financial graph from all workspace ViewModels
   */
  build(viewModels: Record<string, unknown>): GraphResult {
    this.currentGraph = this.graphRuntime.build(viewModels);
    return this.currentGraph;
  }

  /**
   * Get the current graph
   */
  getCurrentGraph(): GraphResult | null {
    return this.currentGraph;
  }

  /**
   * Focus on a specific node
   */
  focusNode(nodeId: string, depth?: number): GraphResult {
    return this.graphRuntime.focus(nodeId, depth);
  }

  /**
   * Get related nodes
   */
  getRelated(nodeId: string, depth?: number): GraphResult {
    return this.graphRuntime.related(nodeId, depth);
  }

  /**
   * Trace money flow
   */
  traceMoney(from: string, to: string): TracePath | null {
    return this.graphRuntime.traceMoney(from, to);
  }

  /**
   * Get graph metrics
   */
  getMetrics(): GraphMetrics {
    return this.graphRuntime.metrics();
  }

  /**
   * Get explainability for a node
   */
  explainNode(nodeId: string): ExplainabilityPayload | null {
    return this.graphRuntime.explain(nodeId);
  }

  // ===== Intelligence Integration =====
  private intelligenceRuntime: IntelligenceRuntime = new IntelligenceRuntime();

  /**
   * Compute financial intelligence from the current graph
   */
  computeIntelligence(config?: Partial<IntelligenceConfig>): IntelligenceResult | null {
    if (!this.currentGraph) return null;

    const context: IntelligenceContext = {
      nodes: this.currentGraph.nodes.map(n => ({
        id: n.id,
        type: n.type,
        label: n.label,
        value_paise: n.value_paise,
        date: n.date,
        metadata: n.metadata,
        confidence: n.confidence,
      })),
      edges: this.currentGraph.edges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        type: e.type,
        label: e.label,
        metadata: e.metadata,
      })),
      config: config ? { ...this.intelligenceRuntime.getConfig(), ...config } : this.intelligenceRuntime.getConfig(),
    };

    return this.intelligenceRuntime.compute(context);
  }

  /**
   * Get the intelligence runtime for advanced operations
   */
  getIntelligenceRuntime(): IntelligenceRuntime {
    return this.intelligenceRuntime;
  }

  // ===== Selection Management =====
  /**
   * Get current selection
   */
  getSelection(): GraphSelection {
    return this.graphRuntime.selection();
  }

  /**
   * Select nodes
   */
  selectNodes(nodeIds: string[]): void {
    this.graphRuntime.select(nodeIds);
  }

  /**
   * Deselect nodes
   */
  deselectNodes(nodeIds: string[]): void {
    this.graphRuntime.deselect(nodeIds);
  }

  /**
   * Toggle node selection
   */
  toggleNode(nodeId: string): void {
    this.graphRuntime.toggleSelection(nodeId);
  }

  /**
   * Clear selection
   */
  clearSelection(): void {
    this.graphRuntime.clearSelection();
  }

  // ===== Layout Management =====
  /**
   * Get current layout
   */
  getLayout(): LayoutConfig {
    return this.layout;
  }

  /**
   * Update panel state
   */
  updatePanel(panelId: PanelId, state: Partial<PanelState>): void {
    this.layout.panels[panelId] = {
      ...this.layout.panels[panelId],
      ...state,
    };
    this.saveLayout();
  }

  /**
   * Toggle panel visibility
   */
  togglePanel(panelId: PanelId): void {
    const current = this.layout.panels[panelId]?.visible ?? true;
    this.updatePanel(panelId, { visible: !current });
  }

  /**
   * Save current layout as a named layout
   */
  saveLayoutAs(name: string): void {
    this.layout.savedLayouts[name] = { ...this.layout.panels };
    this.saveLayout();
  }

  /**
   * Load a saved layout
   */
  loadLayoutByName(name: string): void {
    const saved = this.layout.savedLayouts[name];
    if (saved) {
      this.layout.panels = saved;
      this.saveLayout();
    }
  }

  /**
   * Add to favorites
   */
  addToFavorites(nodeId: string): void {
    if (!this.layout.favorites.includes(nodeId)) {
      this.layout.favorites.push(nodeId);
      this.saveLayout();
    }
  }

  /**
   * Remove from favorites
   */
  removeFromFavorites(nodeId: string): void {
    this.layout.favorites = this.layout.favorites.filter(id => id !== nodeId);
    this.saveLayout();
  }

  /**
   * Get favorites
   */
  getFavorites(): string[] {
    return this.layout.favorites;
  }

  // ===== Persistence =====
  private loadLayout(): LayoutConfig {
    if (typeof window === 'undefined') {
      return this.defaultLayout();
    }

    try {
      const stored = localStorage.getItem('command-center-layout');
      if (stored) {
        return JSON.parse(stored);
      }
    } catch {
      // Ignore parse errors
    }

    return this.defaultLayout();
  }

  private saveLayout(): void {
    if (typeof window === 'undefined') return;

    try {
      localStorage.setItem('command-center-layout', JSON.stringify(this.layout));
    } catch {
      // Ignore storage errors
    }
  }

  private defaultLayout(): LayoutConfig {
    return {
      panels: {
        graph: { id: 'graph', visible: true, width: 800, height: 600 },
        timeline: { id: 'timeline', visible: true, width: 400, height: 300 },
        insights: { id: 'insights', visible: true, width: 300, height: 400 },
        search: { id: 'search', visible: true, width: 300, height: 200 },
        preview: { id: 'preview', visible: true, width: 350, height: 350 },
        context: { id: 'context', visible: true, width: 350, height: 400 },
      },
      favorites: [],
      savedLayouts: {},
    };
  }

  // ===== Reset =====
  /**
   * Reset the runtime
   */
  reset(): void {
    this.graphRuntime.reset();
    this.currentGraph = null;
    this.workspaces.clear();
    this.layout = this.defaultLayout();
    this.saveLayout();
  }
}

// ===== Convenience Export =====
export const commandCenterRuntime = new CommandCenterRuntime();