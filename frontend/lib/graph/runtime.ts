/**
 * Financial Graph Runtime - Stage 4B Financial Graph Runtime
 *
 * Main runtime that orchestrates the registry, event bus, traversal,
 * selection, metrics, and explainability engines.
 *
 * This is the primary entry point for all graph operations.
 *
 * Architecture: Runtime → Registry + EventBus + Traversal + Selection + Metrics + Explainability
 */

import type {
  GraphResult,
  GraphFilter,
  GraphSelection,
  GraphFocus,
  GraphMetrics,
  GraphMetadata,
  TracePath,
  RuntimeAPI,
} from './types';

import { graphRegistry } from './registry';
import { graphEventBus } from './event-bus';
import { graphTraversal } from './traversal';
import { graphSelection } from './selection';
import { graphMetrics } from './metrics';
import { explainabilityRuntime } from './explainability';
import { workspaceRegistry } from '../workspace';
import type { GraphRegistry } from './registry';
import type { GraphEventBus } from './event-bus';
import type { GraphTraversalEngine } from './traversal';
import type { GraphSelectionEngine } from './selection';
import type { GraphMetricsEngine } from './metrics';
import type { ExplainabilityRuntime, ExplainabilityProvider } from './explainability';
import type { WorkspaceName } from '../workspace';

// ===== Runtime Configuration =====
export interface RuntimeConfig {
  /** Maximum traversal depth */
  maxTraversalDepth: number;
  /** Default focus depth */
  defaultFocusDepth: number;
  /** Event log size */
  eventLogSize: number;
  /** Auto-build on adapter registration */
  autoBuild: boolean;
}

const DEFAULT_CONFIG: RuntimeConfig = {
  maxTraversalDepth: 5,
  defaultFocusDepth: 3,
  eventLogSize: 1000,
  autoBuild: false,
};

// ===== Financial Graph Runtime =====
/**
 * Main runtime for the Financial Graph.
 * Orchestrates all graph engines and exposes the public API.
 */
export class FinancialGraphRuntime implements RuntimeAPI {
  private config: RuntimeConfig;
  private registry: GraphRegistry;
  private eventBus: GraphEventBus;
  private traversalEngine: GraphTraversalEngine;
  private selectionEngine: GraphSelectionEngine;
  private metricsEngine: GraphMetricsEngine;
  private explainabilityEngine: ExplainabilityRuntime;
  private currentResult: GraphResult | null = null;

  constructor(
    config: Partial<RuntimeConfig> = {},
    registry?: GraphRegistry,
    eventBus?: GraphEventBus,
    traversal?: GraphTraversalEngine,
    selection?: GraphSelectionEngine,
    metrics?: GraphMetricsEngine,
    explainability?: ExplainabilityRuntime,
  ) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.registry = registry ?? graphRegistry;
    this.eventBus = eventBus ?? graphEventBus;
    this.traversalEngine = traversal ?? graphTraversal;
    this.selectionEngine = selection ?? graphSelection;
    this.metricsEngine = metrics ?? graphMetrics;
    this.explainabilityEngine = explainability ?? explainabilityRuntime;
  }

  /**
   * Build the full financial graph from all registered adapters
   */
  build(viewModels?: Record<string, unknown>): GraphResult {
    const result = this.registry.buildAll(viewModels ?? {});
    this.currentResult = result;

    // Load into all engines
    this.traversalEngine.loadGraph(result);
    this.selectionEngine.loadGraph(result.nodes, result.edges);
    this.metricsEngine.loadGraph(result.nodes, result.edges);
    this.explainabilityEngine.loadGraph(result.nodes, result.edges);

    // Emit event
    this.eventBus.emit('graph:built', {
      node_count: result.metadata.node_count,
      edge_count: result.metadata.edge_count,
    }, 'runtime');

    return result;
  }

  /**
   * Build graph for a single adapter
   */
  buildOne<T>(name: string, viewModel: T): GraphResult {
    const result = this.registry.buildOne(name, viewModel);
    return result;
  }

  /**
   * Trace money flow between two nodes
   */
  traceMoney(from: string, to: string): TracePath | null {
    return this.traversalEngine.traceMoney(from, to);
  }

  /**
   * Find related nodes to a given node
   */
  related(nodeId: string, depth?: number): GraphResult {
    return this.traversalEngine.related(nodeId, depth ?? this.config.defaultFocusDepth);
  }

  /**
   * Extract a subgraph based on a filter
   */
  subgraph(filter: GraphFilter): GraphResult {
    return this.traversalEngine.subgraph(filter);
  }

  /**
   * Get graph metrics
   */
  metrics(): GraphMetrics {
    return this.metricsEngine.compute();
  }

  /**
   * Focus on a specific node with surrounding context
   */
  focus(nodeId: string, depth?: number): GraphResult {
    const focusDepth = depth ?? this.config.defaultFocusDepth;
    this.selectionEngine.focus(nodeId, focusDepth);
    return this.traversalEngine.related(nodeId, focusDepth);
  }

  /**
   * Get current selection
   */
  selection(): GraphSelection {
    return this.selectionEngine.getSelection();
  }

  /**
   * Select nodes
   */
  select(nodeIds: string[]): void {
    this.selectionEngine.select(nodeIds);
  }

  /**
   * Deselect nodes
   */
  deselect(nodeIds: string[]): void {
    this.selectionEngine.deselect(nodeIds);
  }

  /**
   * Toggle node selection
   */
  toggleSelection(nodeId: string): void {
    this.selectionEngine.toggle(nodeId);
  }

  /**
   * Clear all selections
   */
  clearSelection(): void {
    this.selectionEngine.clear();
  }

  /**
   * Get explainability for a node
   */
  explain(nodeId: string) {
    return this.explainabilityEngine.explain(nodeId);
  }

  /**
   * Trace provenance of a node
   */
  trace(nodeId: string): TracePath | null {
    return this.explainabilityEngine.trace(nodeId);
  }

  /**
   * Get the current full graph result
   */
  getCurrentResult(): GraphResult | null {
    return this.currentResult;
  }

  /**
   * Get the registry
   */
  getRegistry(): GraphRegistry {
    return this.registry;
  }

  /**
   * Get the event bus
   */
  getEventBus(): GraphEventBus {
    return this.eventBus;
  }

  /**
   * Get the traversal engine
   */
  getTraversal(): GraphTraversalEngine {
    return this.traversalEngine;
  }

  /**
   * Get the selection engine
   */
  getSelection(): GraphSelectionEngine {
    return this.selectionEngine;
  }

  /**
   * Get the metrics engine
   */
  getMetrics(): GraphMetricsEngine {
    return this.metricsEngine;
  }

  /**
   * Get the explainability runtime
   */
  getExplainability(): ExplainabilityRuntime {
    return this.explainabilityEngine;
  }

  /**
   * Subscribe to selection changes
   */
  onSelectionChanged(handler: (selection: GraphSelection) => void): () => void {
    return this.selectionEngine.onSelectionChanged(handler);
  }

  /**
   * Subscribe to focus changes
   */
  onFocusChanged(handler: (focus: GraphFocus | null) => void): () => void {
    return this.selectionEngine.onFocusChanged(handler);
  }

  /**
   * Register an explainability provider
   */
  registerExplainabilityProvider(
    workspace: string,
    provider: ExplainabilityProvider,
  ): void {
    this.explainabilityEngine.registerProvider(workspace, provider);
  }

  // ===== Workspace Integration =====
  /**
   * Get all registered workspace names
   */
  getWorkspaceNames(): WorkspaceName[] {
    return workspaceRegistry.getNames();
  }

  /**
   * Check if a workspace is registered
   */
  hasWorkspace(name: WorkspaceName): boolean {
    return workspaceRegistry.has(name);
  }

  /**
   * Get workspace registration
   */
  getWorkspaceRegistration(name: WorkspaceName) {
    return workspaceRegistry.get(name);
  }

  /**
   * Reset the runtime
   */
  reset(): void {
    this.currentResult = null;
    this.registry.clear();
    this.eventBus.clearAll();
    this.eventBus.clearEventLog();
    this.traversalEngine.loadGraph({ nodes: [], edges: [], metadata: {} as GraphMetadata });
    this.selectionEngine.reset();
    this.metricsEngine.reset();
    this.explainabilityEngine.reset();
  }
}

// ===== Convenience Export =====
/** Default runtime instance */
export const financialGraphRuntime = new FinancialGraphRuntime();