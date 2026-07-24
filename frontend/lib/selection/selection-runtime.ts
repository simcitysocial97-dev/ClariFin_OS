/**
 * Selection Runtime - Stage 7.5 Runtime Consolidation
 *
 * Single selection engine for all workspaces.
 * Promotes GraphSelectionEngine as the canonical selection runtime.
 *
 * Architecture: SelectionRuntime → GraphSelectionEngine → Workspace Context
 */

import { graphSelection, type GraphSelectionEngine } from '../graph/selection';
import type { GraphNode, GraphEdge, GraphSelection } from '../graph';

// ===== Selection Runtime =====
/**
 * Main runtime for selection management across all workspaces.
 * This is the public API - GraphSelectionEngine is the internal implementation.
 */
export class SelectionRuntime {
  private engine: GraphSelectionEngine;

  constructor(engine?: GraphSelectionEngine) {
    this.engine = engine ?? graphSelection;
  }

  /**
   * Get the underlying engine (for advanced operations)
   */
  getEngine(): GraphSelectionEngine {
    return this.engine;
  }

  // ===== Selection Operations =====
  /**
   * Get current selection
   */
  getSelection(): GraphSelection {
    return this.engine.getSelection();
  }

  /**
   * Select nodes by ID
   */
  select(nodeIds: string[]): void {
    this.engine.select(nodeIds);
  }

  /**
   * Deselect nodes by ID
   */
  deselect(nodeIds: string[]): void {
    this.engine.deselect(nodeIds);
  }

  /**
   * Toggle node selection
   */
  toggle(nodeId: string): void {
    this.engine.toggle(nodeId);
  }

  /**
   * Select all nodes
   */
  selectAll(): void {
    this.engine.selectAll();
  }

  /**
   * Clear all selections
   */
  clear(): void {
    this.engine.clear();
  }

  // ===== Edge Selection =====
  /**
   * Select edges by ID
   */
  selectEdges(edgeIds: string[]): void {
    this.engine.selectEdges(edgeIds);
  }

  /**
   * Deselect edges by ID
   */
  deselectEdges(edgeIds: string[]): void {
    this.engine.deselectEdges(edgeIds);
  }

  // ===== Focus Operations =====
  /**
   * Set focus to a specific node
   */
  focus(nodeId: string, depth = 3): void {
    this.engine.focus(nodeId, depth);
  }

  /**
   * Clear focus
   */
  clearFocus(): void {
    this.engine.clearFocus();
  }

  // ===== Query Operations =====
  /**
   * Check if a node is selected
   */
  isSelected(nodeId: string): boolean {
    return this.engine.isSelected(nodeId);
  }

  /**
   * Check if an edge is selected
   */
  isEdgeSelected(edgeId: string): boolean {
    return this.engine.isEdgeSelected(edgeId);
  }

  /**
   * Get selected nodes
   */
  getSelectedNodes(): GraphNode[] {
    return this.engine.getSelectedNodes();
  }

  /**
   * Get selected edges
   */
  getSelectedEdges(): GraphEdge[] {
    return this.engine.getSelectedEdges();
  }

  /**
   * Get selected count
   */
  get selectedCount(): number {
    return this.engine.selectedCount;
  }

  /**
   * Get selected edge count
   */
  get selectedEdgeCount(): number {
    return this.engine.selectedEdgeCount;
  }

  /**
   * Check if anything is selected
   */
  get hasSelection(): boolean {
    return this.engine.hasSelection;
  }

  /**
   * Check if there is an active focus
   */
  get hasFocus(): boolean {
    return this.engine.hasFocus;
  }

  // ===== Subscription =====
  /**
   * Subscribe to selection changes
   */
  onSelectionChanged(handler: (selection: GraphSelection) => void): () => void {
    return this.engine.onSelectionChanged(handler);
  }

  /**
   * Subscribe to focus changes
   */
  onFocusChanged(handler: (focus: { node_id: string; depth: number } | null) => void): () => void {
    return this.engine.onFocusChanged(handler);
  }

  // ===== Graph Loading =====
  /**
   * Load graph data into the selection engine
   */
  loadGraph(nodes: GraphNode[], edges: GraphEdge[]): void {
    this.engine.loadGraph(nodes, edges);
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
export const selectionRuntime = new SelectionRuntime();