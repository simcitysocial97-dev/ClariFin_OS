/**
 * Graph Overlay - Stage 7 Graph Runtime Integration
 *
 * Full workspace area graph exploration surface.
 * Renders as an overlay (never replaces the workspace).
 *
 * Architecture: FinancialGraphRuntime → FinancialGraphModel → GraphRenderer → ReactFlow
 * Invocation: CommandRuntime / Insight action / Cmd+G → graphInvocation.invoke()
 *
 * Invariants:
 * - Investigative only — never the primary surface
 * - State is ephemeral — not persisted across sessions
 * - Selection delegated to SelectionRuntime, not managed here
 */

'use client';

import { useMemo, useCallback, useState, useEffect } from 'react';
import { FinancialGraphModel, type RenderNode } from '@/lib/graph/financial-graph-model';
import { GraphRenderer } from '@/components/graph/renderer/graph-renderer';
import { financialGraphRuntime } from '@/lib/graph';
import { graphInvocation, type GraphScope } from '@/lib/graph/graph-invocation';
import type { GraphResult } from '@/lib/graph/types';
import { runtimeEventBus, GRAPH_NODE_SELECTED } from '@/lib/event-bus';
import { GraphEvidencePanel } from './graph-evidence-panel';
import { cn } from '@/lib/utils';
import { Search, X, LayoutGrid, GitBranch } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

// ===== Props =====
interface GraphOverlayProps {
  scope: GraphScope;
  initialResult?: GraphResult | null;
  onDismiss?: () => void;
  className?: string;
}

// ===== Component =====
export function GraphOverlay({ scope, initialResult, onDismiss, className }: GraphOverlayProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [layout, setLayout] = useState<'force' | 'tree' | 'radial' | 'timeline' | 'grid'>('force');
  const [showEvidence, setShowEvidence] = useState(false);
  const [result, setResult] = useState<GraphResult | null>(initialResult ?? null);
  // Initialise counts during render from the initial result (no setState-in-effect).
  const [nodeCount, setNodeCount] = useState(() => initialResult?.nodes.length ?? 0);
  const [edgeCount, setEdgeCount] = useState(() => initialResult?.edges.length ?? 0);

  // Build graph model
  const model = useMemo(() => {
    const graphModel = new FinancialGraphModel();
    if (result) {
      graphModel.build(result);
    }
    return graphModel;
  }, [result]);

  // Subscribe to graph invocation state changes
  useEffect(() => {
    const unsubscribe = graphInvocation.subscribe((invScope, invResult) => {
      if (invScope?.mode === 'overlay' && invScope.trigger === scope.trigger) {
        setResult(invResult);
        setNodeCount(invResult?.nodes.length ?? 0);
        setEdgeCount(invResult?.edges.length ?? 0);
      }
    });
    return unsubscribe;
  }, [scope.trigger]);

  // Handle node selection
  const handleNodeSelect = useCallback((node: RenderNode) => {
    setSelectedNodeId(node.id);
    financialGraphRuntime.select([node.id]);
    setShowEvidence(true);
    runtimeEventBus.publish({
      type: GRAPH_NODE_SELECTED,
      timestamp: Date.now(),
      source: 'GraphRuntime',
      payload: { nodeId: node.id, nodeType: node.type, relationships: [] },
    });
  }, []);

  // Handle node focus (double click)
  const handleNodeFocus = useCallback((node: RenderNode) => {
    financialGraphRuntime.focus(node.id, scope.focusDepth ?? 2);
  }, [scope.focusDepth]);

  // Handle evidence panel close
  const handleEvidenceClose = useCallback(() => {
    setShowEvidence(false);
    setSelectedNodeId(null);
  }, []);

  // Handle navigation to source workspace
  const handleNavigateToSource = useCallback((deepLink: string) => {
    if (deepLink) {
      window.location.href = deepLink;
    }
  }, []);

  // Handle dismiss
  const handleDismiss = useCallback(() => {
    graphInvocation.close('overlay-dismissed');
    onDismiss?.();
  }, [onDismiss]);

  // Keyboard shortcut: Escape closes overlay
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleDismiss();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleDismiss]);

  const hasSelection = selectedNodeId !== null;

  return (
    <div className={cn('fixed inset-0 z-[1001] flex flex-col bg-[var(--surface-graph)]', className)}>
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border-default)] bg-[var(--surface-raised)] shrink-0">
        <div className="flex items-center gap-2 flex-1">
          <GitBranch className="h-4 w-4 text-[var(--text-tertiary)]" />
          <span className="fin-label font-medium text-[var(--text-primary)]">
            Graph Exploration
          </span>
          {scope.entityId && (
            <span className="fin-caption text-[var(--text-secondary)]">
              — Entity: {scope.entityId.slice(0, 12)}…
            </span>
          )}
        </div>

        {/* Layout controls */}
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={() => setLayout('force')}>
            <LayoutGrid className="h-3 w-3 mr-1" />Force
          </Button>
          <Button variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={() => setLayout('tree')}>
            <GitBranch className="h-3 w-3 mr-1" />Tree
          </Button>
          <Button variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={() => setLayout('timeline')}>
            <LayoutGrid className="h-3 w-3 mr-1" />Timeline
          </Button>
        </div>

        <div className="flex-1" />

        {/* Search */}
        <div className="relative w-48">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-[var(--text-tertiary)]" />
          <Input
            type="text"
            placeholder="Search nodes…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-7 pl-7 pr-2 text-xs"
          />
        </div>

        {/* Dismiss */}
        <Button
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0"
          onClick={handleDismiss}
          aria-label="Close graph overlay"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Main area: graph + evidence panel */}
      <div className="flex-1 flex overflow-hidden">
        {/* Graph canvas */}
        <div className="flex-1 relative min-w-0">
          {model ? (
            <GraphRenderer
              model={model}
              layout={layout}
              onNodeSelect={handleNodeSelect}
              onNodeFocus={handleNodeFocus}
              className="w-full h-full"
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <p className="fin-caption text-[var(--text-tertiary)]">Building graph…</p>
            </div>
          )}

          {/* Selection indicator */}
          {hasSelection && (
            <div className="absolute bottom-3 left-3 flex items-center gap-2 px-2 py-1 bg-[var(--surface-floating)] border border-[var(--border-default)] rounded-[var(--radius-sm)]">
              <span className="h-2 w-2 rounded-full bg-[var(--color-selection)]" />
              <span className="fin-caption text-[var(--text-secondary)]">
                Selected: {selectedNodeId?.slice(0, 12)}…
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="h-5 w-5 p-0 ml-1"
                onClick={handleEvidenceClose}
                aria-label="Deselect"
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          )}

          {/* Search highlights */}
          {searchQuery && model && (
            <div className="absolute top-3 left-3 px-2 py-1 bg-[var(--surface-floating)] border border-[var(--border-default)] rounded-[var(--radius-sm)]">
              <span className="fin-caption text-[var(--text-secondary)]">
                {model.getNodesByType('').filter(n =>
                  n.label.toLowerCase().includes(searchQuery.toLowerCase())
                ).length} matches
              </span>
            </div>
          )}
        </div>

        {/* Evidence panel (slides in on selection) */}
        {showEvidence && selectedNodeId && model && (
          <GraphEvidencePanel
            nodeId={selectedNodeId}
            onClose={handleEvidenceClose}
            onNavigate={handleNavigateToSource}
          />
        )}
      </div>

      {/* Status bar */}
      <div className="flex items-center gap-4 px-4 py-1.5 border-t border-[var(--border-default)] bg-[var(--surface-raised)] shrink-0">
        <span className="fin-caption text-[var(--text-tertiary)]">
          Nodes: {nodeCount} | Edges: {edgeCount}
        </span>
        <span className="fin-caption text-[var(--text-tertiary)]">
          Layout: {layout}
        </span>
        {scope.entityId && (
          <span className="fin-caption text-[var(--text-tertiary)]">
            Trigger: {scope.trigger}
          </span>
        )}
        <div className="flex-1" />
        <span className="fin-caption text-[var(--text-tertiary)]">
          Esc to close
        </span>
      </div>
    </div>
  );
}
