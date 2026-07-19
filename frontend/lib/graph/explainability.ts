/**
 * Explainability Runtime - Stage 4B Financial Graph Runtime
 *
 * Provides explainability and traceability for every graph node.
 * Wraps existing lib/evidence/ types into graph-aware explainability.
 * Every node can be explained with evidence, calculations, sources, and confidence.
 *
 * Architecture: Runtime → Explainability Runtime → Evidence System
 */

import type {
  GraphNode,
  GraphEdge,
  Evidence,
  Calculation,
  Source,
  TracePath,
  ExplainabilityPayload,
} from './types';

// ===== Explainability Provider =====
/**
 * Interface for workspace-specific explainability providers.
 * Each workspace adapter can optionally implement this to provide
 * detailed explainability for its nodes.
 */
export interface ExplainabilityProvider {
  /** Get evidence for a specific node */
  getEvidence(nodeId: string): Evidence[];
  /** Get calculation steps for a specific node */
  getCalculations(nodeId: string): Calculation[];
  /** Get source references for a specific node */
  getSources(nodeId: string): Source[];
  /** Get confidence score for a specific node (0-100) */
  getConfidence(nodeId: string): number;
}

// ===== Explainability Runtime =====
/**
 * Runtime for explaining graph nodes.
 * Combines graph structure with evidence, calculations, and sources.
 */
export class ExplainabilityRuntime {
  private nodes: Map<string, GraphNode> = new Map();
  private edges: GraphEdge[] = [];
  private providers: Map<string, ExplainabilityProvider> = new Map();

  /**
   * Load graph data
   */
  loadGraph(nodes: GraphNode[], edges: GraphEdge[]): void {
    this.nodes.clear();
    this.edges = [];
    for (const node of nodes) {
      this.nodes.set(node.id, node);
    }
    this.edges = [...edges];
  }

  /**
   * Register an explainability provider for a workspace
   */
  registerProvider(workspace: string, provider: ExplainabilityProvider): void {
    this.providers.set(workspace, provider);
  }

  /**
   * Unregister an explainability provider
   */
  unregisterProvider(workspace: string): boolean {
    return this.providers.delete(workspace);
  }

  /**
   * Get the full explainability payload for a node
   */
  explain(nodeId: string): ExplainabilityPayload | null {
    const node = this.nodes.get(nodeId);
    if (!node) return null;

    const provider = this.providers.get(node.workspace);

    const evidence = provider ? provider.getEvidence(nodeId) : this.buildDefaultEvidence(node);
    const calculations = provider ? provider.getCalculations(nodeId) : this.buildDefaultCalculations(node);
    const sources = provider ? provider.getSources(nodeId) : this.buildDefaultSources(node);
    const confidence = provider
      ? provider.getConfidence(nodeId)
      : (node.confidence ?? 100);

    return {
      node_id: nodeId,
      evidence,
      calculations,
      sources,
      confidence,
    };
  }

  /**
   * Trace the provenance of a node through the graph
   */
  trace(nodeId: string): TracePath | null {
    const node = this.nodes.get(nodeId);
    if (!node) return null;

    // Build a trace path by following 'traces_to' and 'derived_from' edges
    const path: string[] = [nodeId];
    const edgeTypes: string[] = [];
    let currentId = nodeId;
    const visited = new Set<string>([nodeId]);

    // Walk backwards through traceable edges
    let found = true;
    while (found) {
      found = false;
      for (const edge of this.edges) {
        if (edge.target === currentId && !visited.has(edge.source)) {
          if (edge.type === 'traces_to' || edge.type === 'derived_from') {
            path.unshift(edge.source);
            edgeTypes.unshift(edge.type);
            visited.add(edge.source);
            currentId = edge.source;
            found = true;
            break;
          }
        }
      }
    }

    return {
      path,
      edge_types: edgeTypes as TracePath['edge_types'],
      steps: path.length - 1,
      complete: path.length > 1,
    };
  }

  /**
   * Get the confidence score for a node
   */
  confidence(nodeId: string): number {
    const node = this.nodes.get(nodeId);
    if (!node) return 0;

    const provider = this.providers.get(node.workspace);
    if (provider) {
      return provider.getConfidence(nodeId);
    }

    return node.confidence ?? 100;
  }

  /**
   * Get the evidence chain for a node
   */
  evidenceChain(nodeId: string): Evidence[] {
    const node = this.nodes.get(nodeId);
    if (!node) return [];

    const provider = this.providers.get(node.workspace);
    if (provider) {
      return provider.getEvidence(nodeId);
    }

    return this.buildDefaultEvidence(node);
  }

  /**
   * Get calculation steps for a node
   */
  calculationSteps(nodeId: string): Calculation[] {
    const node = this.nodes.get(nodeId);
    if (!node) return [];

    const provider = this.providers.get(node.workspace);
    if (provider) {
      return provider.getCalculations(nodeId);
    }

    return this.buildDefaultCalculations(node);
  }

  /**
   * Get source references for a node
   */
  sources(nodeId: string): Source[] {
    const node = this.nodes.get(nodeId);
    if (!node) return [];

    const provider = this.providers.get(node.workspace);
    if (provider) {
      return provider.getSources(nodeId);
    }

    return this.buildDefaultSources(node);
  }

  /**
   * Build default evidence from node metadata
   */
  private buildDefaultEvidence(node: GraphNode): Evidence[] {
    const evidence: Evidence[] = [];

    if (node.confidence !== undefined) {
      evidence.push({
        type: 'graph_node',
        summary: `Node '${node.label}' from ${node.workspace} workspace`,
        source: node.workspace,
        confidence: node.confidence,
      });
    }

    if (node.date) {
      evidence.push({
        type: 'temporal',
        summary: `Node dated ${node.date}`,
        source: node.workspace,
      });
    }

    return evidence;
  }

  /**
   * Build default calculations from node metadata
   */
  private buildDefaultCalculations(node: GraphNode): Calculation[] {
    const calculations: Calculation[] = [];

    if (node.value_paise !== undefined) {
      calculations.push({
        name: 'value_calculation',
        description: `Monetary value for ${node.label}`,
        inputs: { raw_value: node.value_paise },
        outputs: { value_paise: node.value_paise },
      });
    }

    return calculations;
  }

  /**
   * Build default sources from node metadata
   */
  private buildDefaultSources(node: GraphNode): Source[] {
    return [
      {
        id: `${node.workspace}:${node.id}`,
        type: 'graph_node',
        label: `${node.workspace} workspace`,
        timestamp: new Date().toISOString(),
      },
    ];
  }

  /**
   * Get all nodes that have explainability data
   */
  getExplainableNodes(): GraphNode[] {
    return Array.from(this.nodes.values()).filter(
      n => n.confidence !== undefined || this.providers.has(n.workspace),
    );
  }

  /**
   * Get the count of explainable nodes
   */
  get explainableCount(): number {
    return this.getExplainableNodes().length;
  }

  /**
   * Reset the runtime
   */
  reset(): void {
    this.nodes.clear();
    this.edges = [];
    this.providers.clear();
  }
}

// ===== Convenience Export =====
export const explainabilityRuntime = new ExplainabilityRuntime();