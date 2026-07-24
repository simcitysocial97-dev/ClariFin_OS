/**
 * Graph Traversal Engine - Stage 4B Financial Graph Runtime
 *
 * Graph traversal algorithms for the Financial Graph Runtime.
 * Supports BFS/DFS traversal, money tracing, related node discovery,
 * subgraph extraction, path finding, and cycle detection.
 *
 * Architecture: Runtime → Traversal Engine → Graph
 */

import type {
  GraphNode,
  GraphEdge,
  GraphResult,
  GraphFilter,
  TracePath,
  EdgeType,
} from './types';

// ===== Traversal Options =====
export interface TraversalOptions {
  /** Maximum traversal depth */
  maxDepth: number;
  /** Algorithm: 'bfs' | 'dfs' */
  algorithm: 'bfs' | 'dfs';
  /** Include only these edge types */
  edgeTypes?: EdgeType[];
  /** Node filter function */
  nodeFilter?: (node: GraphNode) => boolean;
}

// ===== Traversal Result =====
export interface TraversalResult {
  /** Nodes visited during traversal */
  visited: GraphNode[];
  /** Edges traversed */
  traversed: GraphEdge[];
  /** Paths discovered (ordered by discovery) */
  paths: string[][];
}

// ===== Default Options =====
const DEFAULT_OPTIONS: TraversalOptions = {
  maxDepth: 5,
  algorithm: 'bfs',
};

// ===== Graph Traversal Engine =====
/**
 * Engine for traversing the financial graph.
 * Provides BFS/DFS traversal, money tracing, and related node discovery.
 */
export class GraphTraversalEngine {
  private nodes: Map<string, GraphNode> = new Map();
  private edges: GraphEdge[] = [];
  private adjacencyList: Map<string, Map<string, GraphEdge[]>> = new Map();

  /**
   * Load a graph into the traversal engine
   */
  loadGraph(result: GraphResult): void {
    this.nodes.clear();
    this.edges = [];
    this.adjacencyList.clear();

    for (const node of result.nodes) {
      this.nodes.set(node.id, node);
    }

    this.edges = [...result.edges];

    // Build adjacency list
    for (const edge of this.edges) {
      if (!this.adjacencyList.has(edge.source)) {
        this.adjacencyList.set(edge.source, new Map());
      }
      const sourceEdges = this.adjacencyList.get(edge.source)!;
      if (!sourceEdges.has(edge.target)) {
        sourceEdges.set(edge.target, []);
      }
      sourceEdges.get(edge.target)!.push(edge);

      // Also index reverse direction for undirected traversal
      if (!this.adjacencyList.has(edge.target)) {
        this.adjacencyList.set(edge.target, new Map());
      }
      const targetEdges = this.adjacencyList.get(edge.target)!;
      if (!targetEdges.has(edge.source)) {
        targetEdges.set(edge.source, []);
      }
      targetEdges.get(edge.source)!.push(edge);
    }
  }

  /**
   * Traverse the graph starting from a given node
   */
  traverse(
    startNodeId: string,
    options: Partial<TraversalOptions> = {},
  ): TraversalResult {
    const opts = { ...DEFAULT_OPTIONS, ...options };
    const visited = new Set<string>();
    const visitedNodes: GraphNode[] = [];
    const traversedEdges: GraphEdge[] = [];
    const paths: string[][] = [];

    const startNode = this.nodes.get(startNodeId);
    if (!startNode) {
      return { visited: [], traversed: [], paths: [] };
    }

    if (opts.algorithm === 'bfs') {
      this.bfs(startNodeId, opts, visited, visitedNodes, traversedEdges, paths);
    } else {
      this.dfs(startNodeId, opts, visited, visitedNodes, traversedEdges, paths, []);
    }

    return {
      visited: visitedNodes,
      traversed: traversedEdges,
      paths,
    };
  }

  /**
   * Breadth-First Search
   */
  private bfs(
    startId: string,
    opts: TraversalOptions,
    visited: Set<string>,
    visitedNodes: GraphNode[],
    traversedEdges: GraphEdge[],
    paths: string[][],
  ): void {
    const queue: Array<{ nodeId: string; depth: number; path: string[] }> = [
      { nodeId: startId, depth: 0, path: [startId] },
    ];
    visited.add(startId);

    while (queue.length > 0) {
      const { nodeId, depth, path } = queue.shift()!;
      const node = this.nodes.get(nodeId);

      if (node && (!opts.nodeFilter || opts.nodeFilter(node))) {
        visitedNodes.push(node);
        paths.push(path);
      }

      if (depth >= opts.maxDepth) continue;

      const neighbors = this.adjacencyList.get(nodeId);
      if (!neighbors) continue;

      for (const [targetId, connectingEdges] of neighbors) {
        if (visited.has(targetId)) continue;

        // Check edge type filter
        if (opts.edgeTypes) {
          const validEdge = connectingEdges.some(e =>
            opts.edgeTypes!.includes(e.type),
          );
          if (!validEdge) continue;
        }

        visited.add(targetId);
        traversedEdges.push(connectingEdges[0]);
        queue.push({
          nodeId: targetId,
          depth: depth + 1,
          path: [...path, targetId],
        });
      }
    }
  }

  /**
   * Depth-First Search
   */
  private dfs(
    nodeId: string,
    opts: TraversalOptions,
    visited: Set<string>,
    visitedNodes: GraphNode[],
    traversedEdges: GraphEdge[],
    paths: string[][],
    currentPath: string[],
  ): void {
    if (visited.has(nodeId)) return;
    visited.add(nodeId);

    const newPath = [...currentPath, nodeId];
    const node = this.nodes.get(nodeId);

    if (node && (!opts.nodeFilter || opts.nodeFilter(node))) {
      visitedNodes.push(node);
      paths.push(newPath);
    }

    if (newPath.length - 1 >= opts.maxDepth) return;

    const neighbors = this.adjacencyList.get(nodeId);
    if (!neighbors) return;

    for (const [targetId, connectingEdges] of neighbors) {
      if (visited.has(targetId)) continue;

      // Check edge type filter
      if (opts.edgeTypes) {
        const validEdge = connectingEdges.some(e =>
          opts.edgeTypes!.includes(e.type),
        );
        if (!validEdge) continue;
      }

      traversedEdges.push(connectingEdges[0]);
      this.dfs(
        targetId,
        opts,
        visited,
        visitedNodes,
        traversedEdges,
        paths,
        newPath,
      );
    }
  }

  /**
   * Trace money flow between two nodes
   * Returns the path of nodes money flows through
   */
  traceMoney(from: string, to: string): TracePath | null {
    const startNode = this.nodes.get(from);
    const endNode = this.nodes.get(to);
    if (!startNode || !endNode) return null;

    // Use BFS to find shortest path
    const visited = new Set<string>();
    const queue: Array<{ nodeId: string; path: string[]; edges: EdgeType[] }> = [
      { nodeId: from, path: [from], edges: [] },
    ];
    visited.add(from);

    while (queue.length > 0) {
      const { nodeId, path, edges } = queue.shift()!;

      if (nodeId === to) {
        return {
          path,
          edge_types: edges,
          steps: path.length - 1,
          complete: true,
        };
      }

      const neighbors = this.adjacencyList.get(nodeId);
      if (!neighbors) continue;

      for (const [targetId, connectingEdges] of neighbors) {
        if (visited.has(targetId)) continue;
        visited.add(targetId);

        // Use the first valid edge type
        const edgeType = connectingEdges[0]?.type;
        queue.push({
          nodeId: targetId,
          path: [...path, targetId],
          edges: edgeType ? [...edges, edgeType] : edges,
        });
      }
    }

    return null;
  }

  /**
   * Find related nodes to a given node within a certain depth
   */
  related(nodeId: string, depth = 3): GraphResult {
    const result = this.traverse(nodeId, {
      maxDepth: depth,
      algorithm: 'bfs',
    });

    return {
      nodes: result.visited,
      edges: result.traversed,
      metadata: {
        node_count: result.visited.length,
        edge_count: result.traversed.length,
        nodes_by_type: {} as Record<string, number>,
        edges_by_type: {} as Record<string, number>,
        workspaces: [],
        built_at: new Date().toISOString(),
        version: '1.0.0',
      },
    };
  }

  /**
   * Extract a subgraph based on a filter
   */
  subgraph(filter: GraphFilter): GraphResult {
    let filteredNodes: GraphNode[] = [];
    let filteredEdges: GraphEdge[] = [];

    // Apply node filters
    if (filter.include_nodes) {
      const includeSet = new Set(filter.include_nodes);
      filteredNodes = Array.from(this.nodes.values()).filter(n =>
        includeSet.has(n.id),
      );
    } else {
      filteredNodes = Array.from(this.nodes.values());
    }

    // Apply exclude filter
    if (filter.exclude_nodes) {
      const excludeSet = new Set(filter.exclude_nodes);
      filteredNodes = filteredNodes.filter(n => !excludeSet.has(n.id));
    }

    // Apply confidence filter
    if (filter.min_confidence !== undefined) {
      filteredNodes = filteredNodes.filter(
        n => (n.confidence ?? 100) >= filter.min_confidence!,
      );
    }

    const nodeIds = new Set(filteredNodes.map(n => n.id));

    // Filter edges
    filteredEdges = this.edges.filter(e => {
      if (!nodeIds.has(e.source) || !nodeIds.has(e.target)) return false;
      if (
        filter.include_edge_types &&
        !filter.include_edge_types.includes(e.type)
      ) {
        return false;
      }
      return true;
    });

    return {
      nodes: filteredNodes,
      edges: filteredEdges,
      metadata: {
        node_count: filteredNodes.length,
        edge_count: filteredEdges.length,
        nodes_by_type: {} as Record<string, number>,
        edges_by_type: {} as Record<string, number>,
        workspaces: [],
        built_at: new Date().toISOString(),
        version: '1.0.0',
      },
    };
  }

  /**
   * Detect cycles in the graph
   */
  detectCycles(): string[][] {
    const cycles: string[][] = [];
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    const dfs = (nodeId: string, path: string[]): void => {
      visited.add(nodeId);
      recursionStack.add(nodeId);

      const neighbors = this.adjacencyList.get(nodeId);
      if (neighbors) {
        for (const targetId of neighbors.keys()) {
          if (!visited.has(targetId)) {
            dfs(targetId, [...path, targetId]);
          } else if (recursionStack.has(targetId)) {
            // Found a cycle
            const cycleStart = path.indexOf(targetId);
            if (cycleStart !== -1) {
              cycles.push(path.slice(cycleStart));
            }
          }
        }
      }

      recursionStack.delete(nodeId);
    };

    for (const nodeId of this.nodes.keys()) {
      if (!visited.has(nodeId)) {
        dfs(nodeId, [nodeId]);
      }
    }

    return cycles;
  }

  /**
   * Find all paths between two nodes (DFS, limited to maxDepth)
   */
  findAllPaths(from: string, to: string, maxDepth = 10): string[][] {
    const paths: string[][] = [];
    const visited = new Set<string>();

    const dfs = (current: string, path: string[]): void => {
      if (path.length > maxDepth) return;
      if (current === to) {
        paths.push([...path]);
        return;
      }

      visited.add(current);
      const neighbors = this.adjacencyList.get(current);
      if (neighbors) {
        for (const targetId of neighbors.keys()) {
          if (!visited.has(targetId)) {
            dfs(targetId, [...path, targetId]);
          }
        }
      }
      visited.delete(current);
    };

    dfs(from, [from]);
    return paths;
  }

  /**
   * Get a node by ID
   */
  getNode(nodeId: string): GraphNode | undefined {
    return this.nodes.get(nodeId);
  }

  /**
   * Check if a node exists
   */
  hasNode(nodeId: string): boolean {
    return this.nodes.has(nodeId);
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
}

// ===== Convenience Export =====
export const graphTraversal = new GraphTraversalEngine();