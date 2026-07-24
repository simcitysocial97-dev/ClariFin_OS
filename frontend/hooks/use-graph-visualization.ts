/**
 * Graph Visualization Hook - Stage 8C Integration
 *
 * Connects visualization components to FinancialGraphRuntime.
 * Provides model and selection state for graph rendering.
 */

'use client';

import { useMemo, useCallback, useEffect, useState } from 'react';
import { FinancialGraphModel, type RenderNode } from '@/lib/graph/financial-graph-model';
import { financialGraphRuntime } from '@/lib/graph';
import type { GraphSelection } from '@/lib/graph/types';

// ===== Hook Return Type =====
interface GraphVisualizationState {
  model: FinancialGraphModel;
  selectedNode: RenderNode | null;
  selectedNodeId: string | null;
}

// ===== Graph Visualization Hook =====
export function useGraphVisualization(): GraphVisualizationState {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // Get current graph from runtime
  const currentGraph = financialGraphRuntime.getCurrentResult();

  // Build model from graph result
  const model = useMemo(() => {
    const graphModel = new FinancialGraphModel();
    if (currentGraph) {
      graphModel.build(currentGraph);
    }
    return graphModel;
  }, [currentGraph]);

  // Get selected node
  const selectedNode = useMemo(() => {
    if (!selectedNodeId || !model) return null;
    return model.getNode(selectedNodeId) ?? null;
  }, [model, selectedNodeId]);

  // Subscribe to selection changes
  useEffect(() => {
    const unsubscribe = financialGraphRuntime.onSelectionChanged((selection: GraphSelection) => {
      const nodeId = selection.node_ids.length > 0 ? selection.node_ids[0] : null;
      setSelectedNodeId(nodeId);
    });

    return unsubscribe;
  }, []);

  return {
    model,
    selectedNode,
    selectedNodeId,
  };
}

// ===== Node Selection Handler =====
export function useNodeSelection() {
  const handleNodeSelect = useCallback((nodeId: string) => {
    financialGraphRuntime.select([nodeId]);
  }, []);

  const handleNodeFocus = useCallback((nodeId: string) => {
    financialGraphRuntime.focus(nodeId, 2);
  }, []);

  const clearSelection = useCallback(() => {
    financialGraphRuntime.clearSelection();
  }, []);

  return {
    handleNodeSelect,
    handleNodeFocus,
    clearSelection,
  };
}