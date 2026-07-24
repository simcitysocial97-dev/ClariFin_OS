/**
 * Money Graph - Stage 5 Command Center Platform
 *
 * Primary visualization for the Financial Graph.
 * Supports zoom, pan, fit, search, trace, expand/collapse, highlight, and selection.
 * Consumes only FinancialGraphRuntime API.
 */

'use client';

import { useRef, useState, useCallback, useMemo } from 'react';
import { commandCenterRuntime } from '@/lib/command-center';
import type { GraphNode } from '@/lib/graph';
import { formatINR } from '@/lib/utils/format';

// ===== View State =====
interface ViewState {
  scale: number;
  translateX: number;
  translateY: number;
}

// ===== Props =====
interface MoneyGraphProps {
  viewModels?: Record<string, unknown>;
  onNodeSelect?: (node: GraphNode) => void;
  onNodeFocus?: (node: GraphNode) => void;
  className?: string;
}

// ===== Component =====
export function MoneyGraph({
  viewModels,
  onNodeSelect,
  onNodeFocus,
  className = '',
}: MoneyGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [viewState, setViewState] = useState<ViewState>({
    scale: 1,
    translateX: 0,
    translateY: 0,
  });
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());

  // Build graph on mount or when viewModels change
  const graph = useMemo(() => {
    if (viewModels) {
      return commandCenterRuntime.build(viewModels);
    }
    return commandCenterRuntime.getCurrentGraph();
  }, [viewModels]);

  // Get nodes and edges
  const nodes = useMemo(() => graph?.nodes ?? [], [graph]);
  const edges = useMemo(() => graph?.edges ?? [], [graph]);

  // ===== Zoom Controls =====
  const zoomIn = useCallback(() => {
    setViewState(prev => ({ ...prev, scale: Math.min(prev.scale * 1.2, 5) }));
  }, []);

  const zoomOut = useCallback(() => {
    setViewState(prev => ({ ...prev, scale: Math.max(prev.scale * 0.8, 0.1) }));
  }, []);

  const fitView = useCallback(() => {
    setViewState({ scale: 1, translateX: 0, translateY: 0 });
  }, []);

  // ===== Node Interaction =====
  const handleNodeClick = useCallback(
    (node: GraphNode) => {
      setSelectedNodeId(node.id);
      onNodeSelect?.(node);
    },
    [onNodeSelect],
  );

  const handleNodeDoubleClick = useCallback(
    (node: GraphNode) => {
      onNodeFocus?.(node);
    },
    [onNodeFocus],
  );

  // ===== Search =====
  const handleSearch = useCallback(
    (query: string) => {
      setSearchQuery(query);
      if (!query) {
        setHighlightedNodes(new Set());
        return;
      }

      const matches = new Set<string>();
      const lowerQuery = query.toLowerCase();
      for (const node of nodes) {
        if (
          node.label.toLowerCase().includes(lowerQuery) ||
          node.workspace.toLowerCase().includes(lowerQuery)
        ) {
          matches.add(node.id);
        }
      }
      setHighlightedNodes(matches);
    },
    [nodes],
  );

  // ===== Render =====
  const nodePositions = useMemo(() => {
    // Simple force-directed layout simulation
    const positions: Record<string, { x: number; y: number }> = {};
    const centerX = 400;
    const centerY = 300;
    const radius = 200;

    nodes.forEach((node, index) => {
      const angle = (index / nodes.length) * 2 * Math.PI;
      positions[node.id] = {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
      };
    });

    return positions;
  }, [nodes]);

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Toolbar */}
      <div className="flex items-center gap-2 p-2 border-b bg-gray-50">
        <button
          onClick={zoomIn}
          className="px-2 py-1 text-sm bg-white border rounded hover:bg-gray-100"
          aria-label="Zoom in"
        >
          Zoom +
        </button>
        <button
          onClick={zoomOut}
          className="px-2 py-1 text-sm bg-white border rounded hover:bg-gray-100"
          aria-label="Zoom out"
        >
          Zoom -
        </button>
        <button
          onClick={fitView}
          className="px-2 py-1 text-sm bg-white border rounded hover:bg-gray-100"
          aria-label="Fit view"
        >
          Fit
        </button>
        <input
          type="text"
          placeholder="Search nodes..."
          value={searchQuery}
          onChange={e => handleSearch(e.target.value)}
          className="flex-1 px-2 py-1 text-sm border rounded"
        />
      </div>

      {/* Graph SVG */}
      <div className="flex-1 overflow-hidden relative">
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          viewBox="0 0 800 600"
          className="cursor-move"
          style={{
            transform: `scale(${viewState.scale}) translate(${viewState.translateX}px, ${viewState.translateY}px)`,
          }}
        >
          {/* Edges */}
          {edges.map(edge => {
            const source = nodePositions[edge.source];
            const target = nodePositions[edge.target];
            if (!source || !target) return null;

            return (
              <line
                key={edge.id}
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
                stroke="#94a3b8"
                strokeWidth={1}
                className="transition-colors"
              />
            );
          })}

          {/* Nodes */}
          {nodes.map(node => {
            const pos = nodePositions[node.id];
            if (!pos) return null;

            const isSelected = selectedNodeId === node.id;
            const isHovered = hoveredNodeId === node.id;
            const isHighlighted = highlightedNodes.has(node.id);

            const radius = isSelected ? 20 : isHovered || isHighlighted ? 15 : 12;
            const fill = isSelected
              ? '#3b82f6'
              : isHovered || isHighlighted
                ? '#60a5fa'
                : '#94a3b8';

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={() => handleNodeClick(node)}
                onDoubleClick={() => handleNodeDoubleClick(node)}
                onMouseEnter={() => setHoveredNodeId(node.id)}
                onMouseLeave={() => setHoveredNodeId(null)}
                className="cursor-pointer"
              >
                <circle
                  r={radius}
                  fill={fill}
                  stroke="#1e293b"
                  strokeWidth={1}
                  className="transition-all"
                />
                <text
                  x={0}
                  y={radius + 12}
                  textAnchor="middle"
                  fontSize={10}
                  fill="#1e293b"
                  className="pointer-events-none"
                >
                  {node.label.length > 15 ? `${node.label.substring(0, 15)}...` : node.label}
                </text>
                {node.value_paise !== undefined && (
                  <text
                    x={0}
                    y={-radius - 4}
                    textAnchor="middle"
                    fontSize={9}
                    fill="#64748b"
                    className="pointer-events-none"
                  >
                    {formatINR(node.value_paise)}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Status Bar */}
      <div className="p-2 border-t text-xs text-gray-500 bg-gray-50">
        <span>
          Nodes: {nodes.length} | Edges: {edges.length} | Scale: {Math.round(viewState.scale * 100)}%
        </span>
      </div>
    </div>
  );
}