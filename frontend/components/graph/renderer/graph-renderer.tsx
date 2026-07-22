/**
 * Graph Renderer - Stage 8C Financial OS Visual System
 *
 * Renders the FinancialGraphModel using XYFlow.
 * Abstraction layer for graph visualization.
 *
 * Architecture: FinancialGraphRuntime → GraphAdapter → FinancialGraphModel → GraphRenderer → XYFlow
 */

'use client';

import { useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from '@xyflow/react';
import type { FinancialGraphModel, RenderNode } from '@/lib/graph/financial-graph-model';
import { cn } from '@/lib/utils';

// ===== Props =====
interface GraphRendererProps {
  model: FinancialGraphModel;
  layout?: 'force' | 'tree' | 'radial' | 'timeline' | 'grid';
  onNodeSelect?: (node: RenderNode) => void;
  onNodeFocus?: (node: RenderNode) => void;
  className?: string;
}

// ===== Node Types =====
const nodeTypes = {
  financialNode: FinancialNode,
};

// ===== Financial Node Component =====
function FinancialNode({ data }: { data: RenderNode }) {
  const { label, color, size, valuePaise, confidenceColor, animation } = data;
  const nodeSize = size * 2;
  const isPulse = animation === 'pulse';
  const isMoneyFlow = animation === 'flow';

  return (
    <div className="relative group">
      {/* Selection halo */}
      <div
        className={cn(
          'absolute inset-0 rounded-full opacity-0 group-data-[selected=true]:opacity-100',
          'fin-selection-halo',
        )}
        style={{ backgroundColor: color, filter: 'blur(8px)', opacity: 0.2 }}
      />
      <div
        className={cn(
          'flex items-center justify-center rounded-full border-2 relative',
          'transition-all duration-150 ease-out',
          'group-hover:shadow-[var(--shadow-interactive)]',
          isPulse && 'fin-risk-pulse',
          isMoneyFlow && 'fin-money-flow',
          'fin-node-enter',
        )}
        style={{
          width: nodeSize,
          height: nodeSize,
          backgroundColor: color,
          borderColor: confidenceColor ?? color,
        }}
        title={label}
      >
        {valuePaise !== undefined && (
          <span className="text-[10px] font-mono text-white truncate max-w-full px-1 leading-none">
            ₹{(valuePaise / 100).toFixed(0)}
          </span>
        )}
      </div>
      {/* Node label */}
      <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 whitespace-nowrap">
        <span className="text-[9px] font-sans text-[var(--text-tertiary)] leading-none" style={{ fontSize: '9px' }}>
          {label?.length > 14 ? label.slice(0, 12) + '…' : label}
        </span>
      </div>
    </div>
  );
}

// ===== Graph Renderer Component =====
export function GraphRenderer({
  model,
  layout = 'force',
  onNodeSelect,
  onNodeFocus,
  className,
}: GraphRendererProps) {
  const renderGraph = useMemo(() => model.applyLayout(layout), [model, layout]);

  // Convert render nodes to XYFlow nodes
  const initialNodes: Node[] = useMemo(() => {
    return renderGraph.nodes.map((node) => ({
      id: node.id,
      type: 'financialNode',
      position: { x: node.x, y: node.y },
      data: node as unknown as Record<string, unknown>,
    }));
  }, [renderGraph]);

  // Convert render edges to XYFlow edges
  const initialEdges: Edge[] = useMemo(() => {
    return renderGraph.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: 'default',
      animated: edge.animation === 'flow',
      style: {
        strokeWidth: edge.strokeWidth,
        stroke: edge.color,
        strokeDasharray: edge.strokeDasharray,
      },
    }));
  }, [renderGraph]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  // Handle node click
  const handleNodeClick = useCallback((_event: unknown, node: Node) => {
    const renderNode = model.getNode(node.id);
    if (renderNode) {
      onNodeSelect?.(renderNode);
    }
  }, [model, onNodeSelect]);

  // Handle node double click (focus)
  const handleNodeDoubleClick = useCallback((_event: unknown, node: Node) => {
    const renderNode = model.getNode(node.id);
    if (renderNode) {
      onNodeFocus?.(renderNode);
    }
  }, [model, onNodeFocus]);

  return (
    <div className={cn('w-full h-full', className)}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onNodeDoubleClick={handleNodeDoubleClick}
        fitView
        attributionPosition="bottom-right"
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}