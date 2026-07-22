/**
 * Money Graph Surface - Stage 8E-B Command Center
 *
 * Abstraction layer for graph rendering.
 * Consumes GraphRenderer, not XYFlow directly.
 *
 * Architecture: MoneyGraphSurface → GraphRenderer → FinancialGraphRuntime
 */

'use client';

import { useMemo, useCallback, useState, useEffect } from 'react';
import { commandCenterRuntime } from '@/lib/command-center';
import { GraphRenderer } from '@/components/graph/renderer/graph-renderer';
import { FinancialGraphModel, type RenderNode } from '@/lib/graph/financial-graph-model';
import { overlayRegistry, type OverlayType } from './overlay-registry';
import { Surface } from '@/components/primitives/surface/surface';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';
import { ToolbarButton, ToolbarSeparator, ToolbarLabel } from '@/components/primitives/toolbar-primitive/compact-toolbar';
import { Kbd } from '@/components/primitives/kbd/kbd';
import { navigationRuntime } from '@/lib/command-center/navigation';
import type { GraphNode } from '@/lib/graph';
import { cn } from '@/lib/utils';

// ===== Props =====
interface MoneyGraphSurfaceProps {
  viewModels?: Record<string, unknown>;
  onNodeSelect?: (node: GraphNode) => void;
  onNodeFocus?: (node: GraphNode) => void;
  className?: string;
}

// ===== Layout Options (optimized for investigative density) =====
const LAYOUT_OPTIONS = {
  width: 1200,
  height: 800,
  padding: 40,
  nodeSpacing: 80,
  rankSpacing: 120,
};

// ===== Money Graph Surface Component =====
export function MoneyGraphSurface({
  viewModels,
  onNodeSelect,
  onNodeFocus,
  className,
}: MoneyGraphSurfaceProps) {
  const [layout, setLayout] = useState<'force' | 'tree' | 'radial' | 'timeline' | 'grid'>('force');
  const [overlaysVisible, setOverlaysVisible] = useState(true);

  // Build graph on mount or when viewModels change
  const graphResult = useMemo(() => {
    if (viewModels) {
      return commandCenterRuntime.build(viewModels);
    }
    return commandCenterRuntime.getCurrentGraph();
  }, [viewModels]);

  // Build render model - pass the model instance, not the result
  const graphModel = useMemo(() => {
    if (!graphResult) return null;
    return new FinancialGraphModel(LAYOUT_OPTIONS);
  }, [graphResult]);

  // Build the graph in the model
  useEffect(() => {
    if (graphModel && graphResult) {
      graphModel.build(graphResult);
    }
  }, [graphModel, graphResult]);

  // Handle node selection - convert RenderNode to GraphNode
  const handleNodeSelect = useCallback((node: RenderNode) => {
    // Find the original GraphNode from the graph result
    const graphNode = graphResult?.nodes.find(n => n.id === node.id);
    if (graphNode) {
      onNodeSelect?.(graphNode);
    }
  }, [onNodeSelect, graphResult]);

  // Handle node focus (double click) - convert RenderNode to GraphNode
  const handleNodeFocus = useCallback((node: RenderNode) => {
    const graphNode = graphResult?.nodes.find(n => n.id === node.id);
    if (graphNode) {
      onNodeFocus?.(graphNode);
      // Navigate to workspace via NavigationRuntime
      navigationRuntime.navigateToNode(graphNode);
    }
  }, [onNodeFocus, graphResult]);

  // Handle overlay toggle
  const handleOverlayToggle = useCallback((overlayId: OverlayType) => {
    overlayRegistry.toggle(overlayId);
  }, []);

  // Get available overlays
  const availableOverlays = overlayRegistry.getAll();

  if (!graphModel) {
    return (
      <Surface variant="graph" density="none" className={cn('flex items-center justify-center', className)}>
        <p className="fin-caption">No graph data available</p>
      </Surface>
    );
  }

  return (
    <Surface variant="graph" density="none" className={cn('flex flex-col h-full', className)}>
      {/* Graph Toolbar */}
      <div className="flex items-center gap-1 px-2 py-1 border-b border-[var(--border-subtle)] shrink-0">
        <ToolbarLabel label="Graph" />
        <ToolbarSeparator />

        {/* Layout Controls */}
        <ToolbarButton
          icon={() => <FinancialIcon name="graph" size={12} />}
          label="Force"
          active={layout === 'force'}
          onClick={() => setLayout('force')}
        />
        <ToolbarButton
          icon={() => <FinancialIcon name="graph" size={12} />}
          label="Tree"
          active={layout === 'tree'}
          onClick={() => setLayout('tree')}
        />
        <ToolbarButton
          icon={() => <FinancialIcon name="graph" size={12} />}
          label="Radial"
          active={layout === 'radial'}
          onClick={() => setLayout('radial')}
        />

        <ToolbarSeparator />

        {/* Overlay Toggle */}
        <ToolbarButton
          icon={() => <FinancialIcon name="graph" size={12} />}
          label="Overlays"
          active={overlaysVisible}
          onClick={() => setOverlaysVisible(!overlaysVisible)}
        />

        <div className="flex-1" />

        {/* Keyboard hint */}
        <div className="flex items-center gap-1 px-1.5 text-[10px] text-[var(--text-tertiary)]">
          <Kbd keys={['G']} size="sm" />
        </div>
      </div>

      {/* Graph Renderer */}
      <div className="flex-1 relative">
        <GraphRenderer
          model={graphModel}
          layout={layout}
          onNodeSelect={handleNodeSelect}
          onNodeFocus={handleNodeFocus}
        />

        {/* Overlay Indicators */}
        {overlaysVisible && (
          <div className="absolute top-2 right-2 flex flex-col gap-1 p-2 bg-[var(--surface-floating)] border border-[var(--border-default)] rounded-[var(--radius-sm)]">
            {availableOverlays.map(overlay => (
              <button
                key={overlay.id}
                onClick={() => handleOverlayToggle(overlay.id)}
                className={cn(
                  'flex items-center gap-1.5 text-xs px-1.5 py-0.5 rounded',
                  overlayRegistry.isVisible(overlay.id)
                    ? 'bg-[var(--surface-selected)] text-[var(--text-primary)]'
                    : 'text-[var(--text-tertiary)] hover:bg-[var(--surface-interactive)]'
                )}
                title={overlay.description}
              >
                <span className="w-2 h-2 rounded-full bg-[var(--color-selection)]" />
                <span className="fin-caption">{overlay.label}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Graph Status */}
      <div className="px-2 py-1 border-t border-[var(--border-subtle)] shrink-0">
        <div className="flex items-center justify-between">
          <span className="fin-caption">
            Nodes: {graphResult?.nodes.length ?? 0} | Edges: {graphResult?.edges.length ?? 0}
          </span>
          <span className="fin-caption">
            Layout: {layout}
          </span>
        </div>
      </div>
    </Surface>
  );
}