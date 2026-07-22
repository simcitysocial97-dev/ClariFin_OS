/**
 * Command Center Layout - Stage 8E-B Command Center
 *
 * Three-layer analytical surface layout.
 *
 * Architecture:
 *   Top Command Bar (global)
 *   ┌──────────────────────────────────────────────────────────┬───────────────┐
 *   │                                                          │               │
 *   │                 Financial Graph                          │ Decision Feed │
 *   │                                                          │               │
 *   ├──────────────────────────────────────────────────────────┴───────────────┤
 *   │ Metrics Strip                                                           │
 *   └──────────────────────────────────────────────────────────────────────────┘
 *   Right Inspector (global)
 *   Bottom Timeline (global)
 */

'use client';

import { useCallback } from 'react';
import { WorkspaceContainer } from '@/components/os-shell/workspace-container';
import { MoneyGraphSurface } from '../graph/money-graph-surface';
import { DecisionFeedPanel } from '../decision-feed/panel';
import { MetricsStrip } from '../metrics/metrics-strip';
import { useCommandCenterKeyboard } from '../hooks/use-command-center-keyboard';
import type { GraphNode } from '@/lib/graph';

// ===== Props =====
interface CommandCenterLayoutProps {
  viewModels?: Record<string, unknown>;
  className?: string;
}

// ===== Command Center Layout Component =====
export function CommandCenterLayout({
  viewModels,
  className,
}: CommandCenterLayoutProps) {
  // Handle node selection from graph
  const handleNodeSelect = useCallback(() => {
    // Selection is handled by SelectionRuntime via MoneyGraphSurface
    // This callback is for any additional workspace-level handling
  }, []);

  // Handle node focus (double click)
  const handleNodeFocus = useCallback(() => {
    // Navigation is handled by NavigationRuntime via MoneyGraphSurface
  }, []);

  // Handle metric selection
  const handleMetricSelect = useCallback((nodeId: string) => {
    // Focus the graph on this node
    const event = new CustomEvent('command-center-focus-node', {
      detail: { nodeId },
    });
    window.dispatchEvent(event);
  }, []);

  // Handle feed item selection
  const handleFeedItemSelect = useCallback((node: GraphNode) => {
    // Focus the graph on this node
    const event = new CustomEvent('command-center-focus-node', {
      detail: { nodeId: node.id },
    });
    window.dispatchEvent(event);
  }, []);

  // Setup keyboard shortcuts
  useCommandCenterKeyboard(handleNodeSelect, handleNodeFocus);

  return (
    <WorkspaceContainer className={className}>
      <div className="h-full flex flex-col">
        {/* Main Content: Graph + Feed */}
        <div className="flex-1 flex overflow-hidden">
          {/* Graph Area (70-75% width) - dominates the workspace */}
          <div className="flex-[3] min-w-0">
            <MoneyGraphSurface
              viewModels={viewModels}
              onNodeSelect={handleNodeSelect}
              onNodeFocus={handleNodeFocus}
            />
          </div>

          {/* Decision Feed (25-30% width) - supports graph */}
          <div className="w-72 flex-shrink-0 border-l border-[var(--border-default)]">
            <DecisionFeedPanel onNodeSelect={handleFeedItemSelect} />
          </div>
        </div>

        {/* Metrics Strip - compact initiation bar */}
        <div className="h-12 border-t border-[var(--border-default)]">
          <MetricsStrip onMetricSelect={handleMetricSelect} />
        </div>
      </div>
    </WorkspaceContainer>
  );
}