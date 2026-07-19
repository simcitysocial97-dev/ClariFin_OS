/**
 * Adapter Infrastructure - Stage 4B Financial Graph Runtime
 *
 * Base adapter class and utilities for workspace graph adapters.
 * Each workspace adapter extends BaseAdapter to convert ViewModels
 * into GraphResult objects without modifying workspace code.
 *
 * Architecture: ViewModel → Adapter → GraphResult
 */

import type {
  GraphAdapter,
  GraphNode,
  GraphEdge,
  GraphResult,
  GraphMetadata,
  NodeType,
  EdgeType,
} from './types';
import { GRAPH_RUNTIME_VERSION } from './types';

// ===== ID Generation =====
/**
 * Generate a scoped node ID with workspace prefix
 */
export function scopedId(workspace: string, localId: string | number): string {
  return `${workspace}:${localId}`;
}

/**
 * Generate a scoped edge ID
 */
export function edgeId(source: string, target: string, type: EdgeType): string {
  return `${source}->${target}:${type}`;
}

// ===== Metadata Builder =====
/**
 * Build GraphMetadata from nodes and edges
 */
export function buildMetadata(
  nodes: GraphNode[],
  edges: GraphEdge[],
  workspace?: string,
): GraphMetadata {
  const nodes_by_type = {} as Record<NodeType, number>;
  const edges_by_type = {} as Record<EdgeType, number>;
  const workspacesSet = new Set<string>();

  for (const node of nodes) {
    nodes_by_type[node.type] = (nodes_by_type[node.type] || 0) + 1;
    workspacesSet.add(node.workspace);
  }

  for (const edge of edges) {
    edges_by_type[edge.type] = (edges_by_type[edge.type] || 0) + 1;
  }

  return {
    node_count: nodes.length,
    edge_count: edges.length,
    nodes_by_type,
    edges_by_type,
    workspaces: workspace ? [workspace] : Array.from(workspacesSet),
    built_at: new Date().toISOString(),
    version: GRAPH_RUNTIME_VERSION,
  };
}

// ===== Base Adapter =====
/**
 * Abstract base class for all workspace graph adapters.
 *
 * Extend this class to create a new workspace adapter.
 * Implement buildNodes() and buildEdges() for the specific ViewModel.
 */
export abstract class BaseAdapter<TViewModel> implements GraphAdapter<TViewModel> {
  abstract readonly name: string;

  /**
   * Export the ViewModel as a complete GraphResult
   */
  export(viewModel: TViewModel): GraphResult {
    const nodes = this.buildNodes(viewModel);
    const edges = this.buildEdges(viewModel, nodes);
    const metadata = this.buildMetadata(nodes, edges);
    return { nodes, edges, metadata };
  }

  /**
   * Build graph nodes from the ViewModel
   */
  abstract buildNodes(viewModel: TViewModel): GraphNode[];

  /**
   * Build graph edges from the ViewModel and nodes
   */
  abstract buildEdges(viewModel: TViewModel, nodes: GraphNode[]): GraphEdge[];

  /**
   * Build metadata for the result
   */
  buildMetadata(nodes: GraphNode[], edges: GraphEdge[]): GraphMetadata {
    return buildMetadata(nodes, edges, this.name);
  }
}

// ===== Empty Adapter =====
/**
 * Empty adapter for workspaces that are not yet implemented.
 * Returns an empty GraphResult with workspace metadata.
 */
export class EmptyAdapter extends BaseAdapter<Record<string, never>> {
  readonly name: string;

  constructor(name: string) {
    super();
    this.name = name;
  }

  buildNodes(): GraphNode[] {
    return [];
  }

  buildEdges(): GraphEdge[] {
    return [];
  }
}

// ===== Graph Result Merger =====
/**
 * Merge multiple GraphResults into a single GraphResult.
 * Deduplicates nodes and edges by ID.
 */
export function mergeGraphResults(results: GraphResult[]): GraphResult {
  const nodeMap = new Map<string, GraphNode>();
  const edgeMap = new Map<string, GraphEdge>();
  const workspacesSet = new Set<string>();
  const nodes_by_type = {} as Record<NodeType, number>;
  const edges_by_type = {} as Record<EdgeType, number>;

  for (const result of results) {
    for (const node of result.nodes) {
      if (!nodeMap.has(node.id)) {
        nodeMap.set(node.id, node);
        nodes_by_type[node.type] = (nodes_by_type[node.type] || 0) + 1;
        workspacesSet.add(node.workspace);
      }
    }
    for (const edge of result.edges) {
      if (!edgeMap.has(edge.id)) {
        edgeMap.set(edge.id, edge);
        edges_by_type[edge.type] = (edges_by_type[edge.type] || 0) + 1;
      }
    }
  }

  const nodes = Array.from(nodeMap.values());
  const edges = Array.from(edgeMap.values());

  return {
    nodes,
    edges,
    metadata: {
      node_count: nodes.length,
      edge_count: edges.length,
      nodes_by_type,
      edges_by_type,
      workspaces: Array.from(workspacesSet),
      built_at: new Date().toISOString(),
      version: GRAPH_RUNTIME_VERSION,
    },
  };
}