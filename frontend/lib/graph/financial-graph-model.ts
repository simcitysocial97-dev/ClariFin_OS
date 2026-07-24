/**
 * Financial Graph Model - Stage 8C Financial OS Visual System
 *
 * Canonical rendering model independent of visualization library.
 * This is the single source of truth for graph rendering.
 *
 * Architecture: FinancialGraphRuntime → GraphAdapter → FinancialGraphModel → GraphRenderer
 */

import type { GraphResult } from './types';
import { getNodeGrammar, getEdgeGrammar, getConfidenceColor } from '../design-system/financial-semantics';

// ===== Render Node =====
export interface RenderNode {
  id: string;
  type: string;
  label: string;
  workspace: string;
  x: number;
  y: number;
  width: number;
  height: number;
  // Visual properties from grammar
  shape: string;
  color: string;
  size: number;
  animation: string;
  badge: string;
  // Data properties
  valuePaise?: number;
  date?: string;
  status?: string;
  confidence?: number;
  confidenceColor?: string;
  // Metadata
  metadata: Record<string, unknown>;
  deepLink?: string;
  // Accessibility
  accessibilityLabel: string;
}

// ===== Render Edge =====
export interface RenderEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  label: string;
  // Visual properties from grammar
  color: string;
  strokeWidth: number;
  strokeDasharray?: string;
  animation: string;
  // Metadata
  weight: number;
  metadata: Record<string, unknown>;
}

// ===== Render Graph =====
export interface RenderGraph {
  nodes: RenderNode[];
  edges: RenderEdge[];
  width: number;
  height: number;
}

// ===== Layout Options =====
export interface LayoutOptions {
  width: number;
  height: number;
  padding: number;
  nodeSpacing: number;
  rankSpacing: number;
}

// ===== Financial Graph Model =====
export class FinancialGraphModel {
  private nodes: Map<string, RenderNode> = new Map();
  private edges: Map<string, RenderEdge> = new Map();
  private layoutOptions: LayoutOptions;

  constructor(options?: Partial<LayoutOptions>) {
    this.layoutOptions = {
      width: 1200,
      height: 800,
      padding: 40,
      nodeSpacing: 80,
      rankSpacing: 120,
      ...options,
    };
  }

  /**
   * Build render model from graph result
   */
  build(graphResult: GraphResult): RenderGraph {
    this.nodes.clear();
    this.edges.clear();

    // Convert nodes
    for (const node of graphResult.nodes) {
      const grammar = getNodeGrammar(node.type);
      const renderNode: RenderNode = {
        id: node.id,
        type: node.type,
        label: node.label,
        workspace: node.workspace,
        x: 0,
        y: 0,
        width: grammar.size * 2,
        height: grammar.size * 2,
        shape: grammar.shape,
        color: grammar.color,
        size: grammar.size,
        animation: grammar.animation ?? 'none',
        badge: grammar.badge ?? 'none',
        valuePaise: node.value_paise,
        date: node.date,
        status: node.status,
        confidence: node.confidence,
        confidenceColor: node.confidence !== undefined ? getConfidenceColor(node.confidence) : undefined,
        metadata: node.metadata,
        deepLink: node.deep_link,
        accessibilityLabel: grammar.accessibilityLabel,
      };
      this.nodes.set(node.id, renderNode);
    }

    // Convert edges
    for (const edge of graphResult.edges) {
      const grammar = getEdgeGrammar(edge.type);
      const renderEdge: RenderEdge = {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type,
        label: edge.label,
        color: grammar.color,
        strokeWidth: grammar.strokeWidth,
        strokeDasharray: grammar.strokeDasharray,
        animation: grammar.animation ?? 'none',
        weight: edge.weight,
        metadata: edge.metadata,
      };
      this.edges.set(edge.id, renderEdge);
    }

    return this.getRenderGraph();
  }

  /**
   * Apply layout to the graph
   */
  applyLayout(layout: 'force' | 'tree' | 'radial' | 'timeline' | 'grid'): RenderGraph {
    const graph = this.getRenderGraph();

    switch (layout) {
      case 'force':
        this.applyForceLayout(graph);
        break;
      case 'tree':
        this.applyTreeLayout(graph);
        break;
      case 'radial':
        this.applyRadialLayout(graph);
        break;
      case 'timeline':
        this.applyTimelineLayout(graph);
        break;
      case 'grid':
        this.applyGridLayout(graph);
        break;
    }

    return graph;
  }

  /**
   * Get render graph
   */
  getRenderGraph(): RenderGraph {
    return {
      nodes: Array.from(this.nodes.values()),
      edges: Array.from(this.edges.values()),
      width: this.layoutOptions.width,
      height: this.layoutOptions.height,
    };
  }

  /**
   * Get node by ID
   */
  getNode(id: string): RenderNode | undefined {
    return this.nodes.get(id);
  }

  /**
   * Get edge by ID
   */
  getEdge(id: string): RenderEdge | undefined {
    return this.edges.get(id);
  }

  /**
   * Get nodes by type
   */
  getNodesByType(type: string): RenderNode[] {
    return Array.from(this.nodes.values()).filter(n => n.type === type);
  }

  /**
   * Get edges by type
   */
  getEdgesByType(type: string): RenderEdge[] {
    return Array.from(this.edges.values()).filter(e => e.type === type);
  }

  // ===== Layout Implementations =====

  private applyForceLayout(graph: RenderGraph): void {
    // Simple force-directed layout
    const centerX = this.layoutOptions.width / 2;
    const centerY = this.layoutOptions.height / 2;
    const radius = Math.min(centerX, centerY) - this.layoutOptions.padding;

    graph.nodes.forEach((node, index) => {
      const angle = (index / graph.nodes.length) * 2 * Math.PI;
      node.x = centerX + Math.cos(angle) * radius;
      node.y = centerY + Math.sin(angle) * radius;
    });
  }

  private applyTreeLayout(graph: RenderGraph): void {
    // Group nodes by workspace
    const workspaceGroups = new Map<string, RenderNode[]>();
    for (const node of graph.nodes) {
      const workspace = node.workspace;
      if (!workspaceGroups.has(workspace)) {
        workspaceGroups.set(workspace, []);
      }
      workspaceGroups.get(workspace)!.push(node);
    }

    // Layout each workspace group
    let yOffset = this.layoutOptions.padding;
    const workspaces = Array.from(workspaceGroups.keys());

    workspaces.forEach((workspace, workspaceIndex) => {
      const nodes = workspaceGroups.get(workspace)!;
      const xSpacing = (this.layoutOptions.width - 2 * this.layoutOptions.padding) / (nodes.length + 1);

      nodes.forEach((node, index) => {
        node.x = this.layoutOptions.padding + (index + 1) * xSpacing;
        node.y = yOffset + workspaceIndex * 150;
      });
    });
  }

  private applyRadialLayout(graph: RenderGraph): void {
    // Same as force for now
    this.applyForceLayout(graph);
  }

  private applyTimelineLayout(graph: RenderGraph): void {
    // Sort by date
    const sortedNodes = [...graph.nodes].sort((a, b) => {
      if (!a.date || !b.date) return 0;
      return a.date.localeCompare(b.date);
    });

    const xSpacing = (this.layoutOptions.width - 2 * this.layoutOptions.padding) / (sortedNodes.length + 1);
    const centerY = this.layoutOptions.height / 2;

    sortedNodes.forEach((node, index) => {
      node.x = this.layoutOptions.padding + (index + 1) * xSpacing;
      node.y = centerY;
    });
  }

  private applyGridLayout(graph: RenderGraph): void {
    const cols = Math.ceil(Math.sqrt(graph.nodes.length));
    const xSpacing = (this.layoutOptions.width - 2 * this.layoutOptions.padding) / (cols + 1);
    const ySpacing = (this.layoutOptions.height - 2 * this.layoutOptions.padding) / (cols + 1);

    graph.nodes.forEach((node, index) => {
      const col = index % cols;
      const row = Math.floor(index / cols);
      node.x = this.layoutOptions.padding + (col + 1) * xSpacing;
      node.y = this.layoutOptions.padding + (row + 1) * ySpacing;
    });
  }

  /**
   * Reset the model
   */
  reset(): void {
    this.nodes.clear();
    this.edges.clear();
  }
}