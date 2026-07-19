/**
 * Graph Metrics Engine - Stage 4B Financial Graph Runtime
 *
 * Computes graph-level metrics for the Financial Graph Runtime.
 * Provides insights into graph structure, connectivity, and composition.
 *
 * Architecture: Runtime → Metrics Engine → GraphMetrics
 */

import type {
  GraphNode,
  GraphEdge,
  GraphMetrics,
  NodeType,
  EdgeType,
} from './types';

// ===== Graph Metrics Engine =====
/**
 * Engine for computing graph metrics.
 * Analyzes graph structure, connectivity, and composition.
 */
export class GraphMetricsEngine {
  private nodes: Map<string, GraphNode> = new Map();
  private edges: GraphEdge[] = [];
  private adjacencyList: Map<string, Set<string>> = new Map();

  /**
   * Load a graph for metric computation
   */
  loadGraph(nodes: GraphNode[], edges: GraphEdge[]): void {
    this.nodes.clear();
    this.edges = [];
    this.adjacencyList.clear();

    for (const node of nodes) {
      this.nodes.set(node.id, node);
    }

    this.edges = [...edges];

    // Build adjacency list for degree computation
    for (const edge of this.edges) {
      if (!this.adjacencyList.has(edge.source)) {
        this.adjacencyList.set(edge.source, new Set());
      }
      this.adjacencyList.get(edge.source)!.add(edge.target);

      if (!this.adjacencyList.has(edge.target)) {
        this.adjacencyList.set(edge.target, new Set());
      }
      this.adjacencyList.get(edge.target)!.add(edge.source);
    }
  }

  /**
   * Compute all graph metrics
   */
  compute(): GraphMetrics {
    const nodeCount = this.nodes.size;
    const edgeCount = this.edges.length;

    // Density: 2|E| / (|V|(|V|-1))
    const density = nodeCount > 1
      ? (2 * edgeCount) / (nodeCount * (nodeCount - 1))
      : 0;

    // Average degree: 2|E| / |V|
    const averageDegree = nodeCount > 0
      ? (2 * edgeCount) / nodeCount
      : 0;

    // Connected components
    const componentCount = this.countConnectedComponents();

    // Nodes by workspace
    const nodesByWorkspace: Record<string, number> = {};
    for (const node of this.nodes.values()) {
      nodesByWorkspace[node.workspace] = (nodesByWorkspace[node.workspace] || 0) + 1;
    }

    // Edges by type
    const edgesByType = {} as Record<EdgeType, number>;
    for (const edge of this.edges) {
      edgesByType[edge.type] = (edgesByType[edge.type] || 0) + 1;
    }

    // Total monetary value
    let totalValuePaise = 0;
    for (const node of this.nodes.values()) {
      if (node.value_paise !== undefined) {
        totalValuePaise += node.value_paise;
      }
    }

    // Nodes by type
    const nodesByType = {} as Record<NodeType, number>;
    for (const node of this.nodes.values()) {
      nodesByType[node.type] = (nodesByType[node.type] || 0) + 1;
    }

    return {
      node_count: nodeCount,
      edge_count: edgeCount,
      density: Math.round(density * 10000) / 10000,
      average_degree: Math.round(averageDegree * 100) / 100,
      component_count: componentCount,
      nodes_by_workspace: nodesByWorkspace,
      edges_by_type: edgesByType,
      total_value_paise: totalValuePaise,
      nodes_by_type: nodesByType,
    };
  }

  /**
   * Count connected components using BFS
   */
  private countConnectedComponents(): number {
    const visited = new Set<string>();
    let components = 0;

    for (const nodeId of this.nodes.keys()) {
      if (!visited.has(nodeId)) {
        components++;
        // BFS to mark all nodes in this component
        const queue = [nodeId];
        visited.add(nodeId);
        while (queue.length > 0) {
          const current = queue.shift()!;
          const neighbors = this.adjacencyList.get(current);
          if (neighbors) {
            for (const neighbor of neighbors) {
              if (!visited.has(neighbor)) {
                visited.add(neighbor);
                queue.push(neighbor);
              }
            }
          }
        }
      }
    }

    return components;
  }

  /**
   * Compute degree centrality for a specific node
   */
  degreeCentrality(nodeId: string): number {
    const neighbors = this.adjacencyList.get(nodeId);
    if (!neighbors || this.nodes.size <= 1) return 0;
    return neighbors.size / (this.nodes.size - 1);
  }

  /**
   * Compute the distribution of node types
   */
  nodeTypeDistribution(): Array<{ type: NodeType; count: number; percentage: number }> {
    const total = this.nodes.size;
    const byType = {} as Record<NodeType, number>;

    for (const node of this.nodes.values()) {
      byType[node.type] = (byType[node.type] || 0) + 1;
    }

    return Object.entries(byType).map(([type, count]) => ({
      type: type as NodeType,
      count,
      percentage: total > 0 ? Math.round((count / total) * 10000) / 100 : 0,
    }));
  }

  /**
   * Compute the distribution of edge types
   */
  edgeTypeDistribution(): Array<{ type: EdgeType; count: number; percentage: number }> {
    const total = this.edges.length;
    const byType = {} as Record<EdgeType, number>;

    for (const edge of this.edges) {
      byType[edge.type] = (byType[edge.type] || 0) + 1;
    }

    return Object.entries(byType).map(([type, count]) => ({
      type: type as EdgeType,
      count,
      percentage: total > 0 ? Math.round((count / total) * 10000) / 100 : 0,
    }));
  }

  /**
   * Get the top N nodes by degree
   */
  topNodesByDegree(limit = 10): Array<{ node: GraphNode; degree: number }> {
    const degrees: Array<{ nodeId: string; degree: number }> = [];

    for (const nodeId of this.nodes.keys()) {
      const neighbors = this.adjacencyList.get(nodeId);
      degrees.push({
        nodeId,
        degree: neighbors ? neighbors.size : 0,
      });
    }

    degrees.sort((a, b) => b.degree - a.degree);

    return degrees.slice(0, limit).map(d => ({
      node: this.nodes.get(d.nodeId)!,
      degree: d.degree,
    }));
  }

  /**
   * Get the total monetary value by workspace
   */
  valueByWorkspace(): Record<string, number> {
    const values: Record<string, number> = {};

    for (const node of this.nodes.values()) {
      if (node.value_paise !== undefined) {
        values[node.workspace] = (values[node.workspace] || 0) + node.value_paise;
      }
    }

    return values;
  }

  /**
   * Get node count
   */
  get nodeCount(): number {
    return this.nodes.size;
  }

  /**
   * Get edge count
   */
  get edgeCount(): number {
    return this.edges.length;
  }

  /**
   * Reset the engine
   */
  reset(): void {
    this.nodes.clear();
    this.edges = [];
    this.adjacencyList.clear();
  }
}

// ===== Convenience Export =====
export const graphMetrics = new GraphMetricsEngine();