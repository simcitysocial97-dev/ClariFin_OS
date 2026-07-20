/**
 * Money Graph - Stage 8C Financial OS Visual System
 *
 * Primary visualization for the Financial Graph.
 * Uses GraphRenderer with FinancialGraphModel.
 *
 * Features:
 * - Node clustering by workspace
 * - Edge highlighting on selection
 * - Money flow traversal
 * - Search integration
 * - Zoom and pan
 * - Focus mode
 */

'use client';

import { useMemo, useCallback, useState, useEffect } from 'react';
import { FinancialGraphModel, type RenderNode } from '@/lib/graph/financial-graph-model';
import { GraphRenderer } from '@/components/graph/renderer/graph-renderer';
import { financialGraphRuntime } from '@/lib/graph';
import { Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

// ===== Props =====
interface MoneyGraphProps {
  className?: string;
  onNodeSelect?: (node: RenderNode) => void;
  onNodeFocus?: (node: RenderNode) => void;
}

// ===== Money Graph Component =====
export function MoneyGraph({
  className,
  onNodeSelect,
  onNodeFocus,
}: MoneyGraphProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [layout, setLayout] = useState<'force' | 'tree' | 'radial' | 'timeline' | 'grid'>('force');

  // Build graph model from runtime
  const model = useMemo(() => {
    const currentGraph = financialGraphRuntime.getCurrentResult();
    const graphModel = new FinancialGraphModel();
    if (currentGraph) {
      graphModel.build(currentGraph);
    }
    return graphModel;
  }, []);

  // Subscribe to selection changes
  useEffect(() => {
    const unsubscribe = financialGraphRuntime.onSelectionChanged((selection) => {
      const nodeId = selection.node_ids.length > 0 ? selection.node_ids[0] : null;
      setSelectedNodeId(nodeId);
    });
    return unsubscribe;
  }, []);

  // Handle node selection
  const handleNodeSelect = useCallback((node: RenderNode) => {
    setSelectedNodeId(node.id);
    financialGraphRuntime.select([node.id]);
    onNodeSelect?.(node);
  }, [onNodeSelect]);

  // Handle node focus
  const handleNodeFocus = useCallback((node: RenderNode) => {
    financialGraphRuntime.focus(node.id, 2);
    onNodeFocus?.(node);
  }, [onNodeFocus]);

  // Search handler
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Toolbar */}
      <div className="flex items-center gap-2 p-2 border-b bg-gray-50">
        <div className="relative flex-1">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            type="text"
            placeholder="Search nodes..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-8 text-sm"
          />
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setLayout('force')}
          className="text-xs"
        >
          Force
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setLayout('tree')}
          className="text-xs"
        >
          Tree
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setLayout('timeline')}
          className="text-xs"
        >
          Timeline
        </Button>
      </div>

      {/* Graph */}
      <div className="flex-1 relative">
        <GraphRenderer
          model={model}
          layout={layout}
          onNodeSelect={handleNodeSelect}
          onNodeFocus={handleNodeFocus}
        />
      </div>

      {/* Status Bar */}
      <div className="p-2 border-t text-xs text-gray-500 bg-gray-50">
        <span>
          Layout: {layout} | Selected: {selectedNodeId ?? 'none'}
        </span>
      </div>
    </div>
  );
}