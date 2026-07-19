/**
 * Graph Selection Engine - Stage 4B Financial Graph Runtime
 *
 * Manages node/edge selection and focus state for the Financial Graph Runtime.
 * Enables interactive graph exploration without UI coupling.
 *
 * Architecture: Runtime → Selection Engine → State
 */

import type { GraphNode, GraphEdge, GraphSelection, GraphFocus } from './types';

// ===== Selection Change Handler =====
export type SelectionChangeHandler = (selection: GraphSelection) => void;
export type FocusChangeHandler = (focus: GraphFocus | null) => void;

// ===== Graph Selection Engine =====
/**
 * Engine for managing graph selection and focus state.
 * Tracks selected nodes/edges and the currently focused node.
 */
export class GraphSelectionEngine {
  private selectedNodeIds: Set<string> = new Set();
  private selectedEdgeIds: Set<string> = new Set();
  private focusNodeId: string | null = null;
  private focusDepth = 3;
  private nodes: Map<string, GraphNode> = new Map();
  private edges: Map<string, GraphEdge> = new Map();

  private selectionListeners: Set<SelectionChangeHandler> = new Set();
  private focusListeners: Set<FocusChangeHandler> = new Set();

  /**
   * Load nodes and edges for reference
   */
  loadGraph(nodes: GraphNode[], edges: GraphEdge[]): void {
    this.nodes.clear();
    this.edges.clear();
    for (const node of nodes) {
      this.nodes.set(node.id, node);
    }
    for (const edge of edges) {
      this.edges.set(edge.id, edge);
    }
  }

  /**
   * Select specific nodes by ID
   */
  select(nodeIds: string[]): void {
    for (const id of nodeIds) {
      if (this.nodes.has(id)) {
        this.selectedNodeIds.add(id);
      }
    }
    this.notifySelectionChanged();
  }

  /**
   * Deselect specific nodes by ID
   */
  deselect(nodeIds: string[]): void {
    for (const id of nodeIds) {
      this.selectedNodeIds.delete(id);
    }
    this.notifySelectionChanged();
  }

  /**
   * Toggle selection of a node
   */
  toggle(nodeId: string): void {
    if (this.selectedNodeIds.has(nodeId)) {
      this.selectedNodeIds.delete(nodeId);
    } else if (this.nodes.has(nodeId)) {
      this.selectedNodeIds.add(nodeId);
    }
    this.notifySelectionChanged();
  }

  /**
   * Select all loaded nodes
   */
  selectAll(): void {
    for (const id of this.nodes.keys()) {
      this.selectedNodeIds.add(id);
    }
    this.notifySelectionChanged();
  }

  /**
   * Clear all selections
   */
  clear(): void {
    this.selectedNodeIds.clear();
    this.selectedEdgeIds.clear();
    this.notifySelectionChanged();
  }

  /**
   * Select edges by ID
   */
  selectEdges(edgeIds: string[]): void {
    for (const id of edgeIds) {
      if (this.edges.has(id)) {
        this.selectedEdgeIds.add(id);
      }
    }
    this.notifySelectionChanged();
  }

  /**
   * Deselect edges by ID
   */
  deselectEdges(edgeIds: string[]): void {
    for (const id of edgeIds) {
      this.selectedEdgeIds.delete(id);
    }
    this.notifySelectionChanged();
  }

  /**
   * Set the focus to a specific node
   */
  focus(nodeId: string, depth = 3): void {
    if (this.nodes.has(nodeId)) {
      this.focusNodeId = nodeId;
      this.focusDepth = depth;
      this.notifyFocusChanged();
    }
  }

  /**
   * Clear the current focus
   */
  clearFocus(): void {
    this.focusNodeId = null;
    this.focusDepth = 3;
    this.notifyFocusChanged();
  }

  /**
   * Get the current selection state
   */
  getSelection(): GraphSelection {
    return {
      node_ids: Array.from(this.selectedNodeIds),
      edge_ids: Array.from(this.selectedEdgeIds),
      all_selected: this.selectedNodeIds.size === this.nodes.size,
      selected_at: new Date().toISOString(),
    };
  }

  /**
   * Get the current focus state
   */
  getFocus(): GraphFocus | null {
    if (!this.focusNodeId) return null;
    return {
      node_id: this.focusNodeId,
      depth: this.focusDepth,
    };
  }

  /**
   * Check if a node is selected
   */
  isSelected(nodeId: string): boolean {
    return this.selectedNodeIds.has(nodeId);
  }

  /**
   * Check if an edge is selected
   */
  isEdgeSelected(edgeId: string): boolean {
    return this.selectedEdgeIds.has(edgeId);
  }

  /**
   * Get selected nodes
   */
  getSelectedNodes(): GraphNode[] {
    return Array.from(this.selectedNodeIds)
      .map(id => this.nodes.get(id))
      .filter((n): n is GraphNode => n !== undefined);
  }

  /**
   * Get selected edges
   */
  getSelectedEdges(): GraphEdge[] {
    return Array.from(this.selectedEdgeIds)
      .map(id => this.edges.get(id))
      .filter((e): e is GraphEdge => e !== undefined);
  }

  /**
   * Get the count of selected nodes
   */
  get selectedCount(): number {
    return this.selectedNodeIds.size;
  }

  /**
   * Get the count of selected edges
   */
  get selectedEdgeCount(): number {
    return this.selectedEdgeIds.size;
  }

  /**
   * Check if anything is selected
   */
  get hasSelection(): boolean {
    return this.selectedNodeIds.size > 0 || this.selectedEdgeIds.size > 0;
  }

  /**
   * Check if there is an active focus
   */
  get hasFocus(): boolean {
    return this.focusNodeId !== null;
  }

  /**
   * Subscribe to selection changes
   */
  onSelectionChanged(handler: SelectionChangeHandler): () => void {
    this.selectionListeners.add(handler);
    return () => {
      this.selectionListeners.delete(handler);
    };
  }

  /**
   * Subscribe to focus changes
   */
  onFocusChanged(handler: FocusChangeHandler): () => void {
    this.focusListeners.add(handler);
    return () => {
      this.focusListeners.delete(handler);
    };
  }

  /**
   * Notify all selection listeners
   */
  private notifySelectionChanged(): void {
    const selection = this.getSelection();
    for (const handler of this.selectionListeners) {
      try {
        handler(selection);
      } catch (error) {
        console.error('[GraphSelectionEngine] Error in selection listener:', error);
      }
    }
  }

  /**
   * Notify all focus listeners
   */
  private notifyFocusChanged(): void {
    const focus = this.getFocus();
    for (const handler of this.focusListeners) {
      try {
        handler(focus);
      } catch (error) {
        console.error('[GraphSelectionEngine] Error in focus listener:', error);
      }
    }
  }

  /**
   * Reset the engine state
   */
  reset(): void {
    this.selectedNodeIds.clear();
    this.selectedEdgeIds.clear();
    this.focusNodeId = null;
    this.focusDepth = 3;
    this.nodes.clear();
    this.edges.clear();
    this.selectionListeners.clear();
    this.focusListeners.clear();
  }
}

// ===== Convenience Export =====
export const graphSelection = new GraphSelectionEngine();