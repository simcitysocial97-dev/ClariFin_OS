/**
 * Evidence Runtime - Stage 7.5 Runtime Consolidation
 *
 * Single explainability runtime for all workspaces.
 * Promotes ExplainabilityRuntime as the canonical evidence runtime.
 *
 * Architecture: EvidenceRuntime → ExplainabilityRuntime → Workspace Context
 */

import {
  explainabilityRuntime,
  type ExplainabilityRuntime,
  type ExplainabilityProvider,
} from '../graph/explainability';
import type { GraphNode, GraphEdge, Evidence, Calculation, Source, TracePath, ExplainabilityPayload } from '../graph';

// ===== Evidence Runtime =====
/**
 * Main runtime for evidence management across all workspaces.
 * This is the public API - ExplainabilityRuntime is the internal implementation.
 */
export class EvidenceRuntime {
  private engine: ExplainabilityRuntime;

  constructor(engine?: ExplainabilityRuntime) {
    this.engine = engine ?? explainabilityRuntime;
  }

  /**
   * Get the underlying engine (for advanced operations)
   */
  getEngine(): ExplainabilityRuntime {
    return this.engine;
  }

  // ===== Evidence Operations =====
  /**
   * Explain a node
   */
  explain(nodeId: string): ExplainabilityPayload | null {
    return this.engine.explain(nodeId);
  }

  /**
   * Trace provenance of a node
   */
  trace(nodeId: string): TracePath | null {
    return this.engine.trace(nodeId);
  }

  /**
   * Get evidence for a node
   */
  evidence(nodeId: string): Evidence[] {
    return this.engine.evidenceChain(nodeId);
  }

  /**
   * Get calculation steps for a node
   */
  calculations(nodeId: string): Calculation[] {
    return this.engine.calculationSteps(nodeId);
  }

  /**
   * Get sources for a node
   */
  sources(nodeId: string): Source[] {
    return this.engine.sources(nodeId);
  }

  /**
   * Get confidence for a node
   */
  confidence(nodeId: string): number {
    return this.engine.confidence(nodeId);
  }

  // ===== Provider Management =====
  /**
   * Register an explainability provider
   */
  registerProvider(workspace: string, provider: ExplainabilityProvider): void {
    this.engine.registerProvider(workspace, provider);
  }

  /**
   * Unregister an explainability provider
   */
  unregisterProvider(workspace: string): boolean {
    return this.engine.unregisterProvider(workspace);
  }

  // ===== Graph Loading =====
  /**
   * Load graph data into the evidence engine
   */
  loadGraph(nodes: GraphNode[], edges: GraphEdge[]): void {
    this.engine.loadGraph(nodes, edges);
  }

  // ===== Query Operations =====
  /**
   * Get all explainable nodes
   */
  getExplainableNodes(): GraphNode[] {
    return this.engine.getExplainableNodes();
  }

  /**
   * Get explainable count
   */
  get explainableCount(): number {
    return this.engine.explainableCount;
  }

  // ===== Reset =====
  /**
   * Reset the runtime
   */
  reset(): void {
    this.engine.reset();
  }
}

// ===== Convenience Export =====
export const evidenceRuntime = new EvidenceRuntime();