/**
 * Command Center Page - Stage 5 Command Center Platform
 *
 * Main entry point for the Command Center.
 * Composes all command center components.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  commandCenterRuntime,
  type PanelId,
} from '@/lib/command-center';
import type { GraphNode } from '@/lib/graph';
import { MoneyGraph } from '@/components/command-center/money-graph';
import { ContextPanel } from '@/components/command-center/context-panel';
import { Timeline } from '@/components/command-center/timeline';
import { InsightFeed } from '@/components/command-center/insight-feed';
import { GlobalSearch } from '@/components/command-center/global-search';
import { WorkspacePreview } from '@/components/command-center/workspace-preview';
import { Button } from '@/components/ui/button';
import { useDashboardMetrics } from '@/lib/hooks/use-dashboard-metrics';
import { useManagedAccounts } from '@/lib/hooks/use-accounts';
import { useLoans } from '@/lib/hooks/use-loans';
import { useCards } from '@/lib/hooks/use-cards';
import { useInvestments } from '@/lib/hooks/use-investments';
import { useCashflow } from '@/lib/hooks/use-cashflow';
import { useBehaviorScore } from '@/lib/hooks/use-behavior-score';
import { useReconciliations } from '@/lib/hooks/use-reconciliation';

// ===== Page Component =====
export default function CommandCenterPage() {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [activePanel, setActivePanel] = useState<PanelId>('graph');

  // Load all workspace data
  const { data: dashboardData } = useDashboardMetrics();
  const { data: accountsData } = useManagedAccounts();
  const { data: loansData } = useLoans();
  const { data: cardsData } = useCards();
  const { data: investmentsData } = useInvestments();
  const { data: cashflowData } = useCashflow();
  const { data: behaviourData } = useBehaviorScore();
  const { data: forecastData } = useCashflow(); // Use cashflow as forecast placeholder
  const { data: reconciliationData } = useReconciliations();

  // Build graph when data is available
  useEffect(() => {
    const viewModels: Record<string, unknown> = {
      transactions: { transactions: dashboardData?.recent_transactions ?? [] },
      accounts: accountsData,
      loans: loansData,
      cards: cardsData,
      investments: investmentsData,
      cashflow: cashflowData,
      behaviour: behaviourData,
      forecast: forecastData,
      reconciliation: reconciliationData,
    };

    // Only build if we have at least some data
    if (Object.values(viewModels).some(v => v !== undefined)) {
      commandCenterRuntime.build(viewModels);
    }
  }, [
    dashboardData,
    accountsData,
    loansData,
    cardsData,
    investmentsData,
    cashflowData,
    behaviourData,
    forecastData,
    reconciliationData,
  ]);

  // Handle node selection
  const handleNodeSelect = useCallback((node: GraphNode) => {
    setSelectedNodeId(node.id);
  }, []);

  // Handle node focus
  const handleNodeFocus = useCallback((node: GraphNode) => {
    setSelectedNodeId(node.id);
    // Could also navigate to workspace
  }, []);

  // Panel tabs
  const panels: PanelId[] = ['graph', 'timeline', 'insights', 'search', 'preview', 'context'];

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="border-b p-4 bg-white">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Command Center</h1>
          <div className="flex items-center gap-2">
            {panels.map(panel => (
              <Button
                key={panel}
                variant={activePanel === panel ? 'default' : 'outline'}
                size="sm"
                onClick={() => setActivePanel(panel)}
              >
                {panel.charAt(0).toUpperCase() + panel.slice(1)}
              </Button>
            ))}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Graph or Timeline */}
        <div className="flex-1 border-r">
          {activePanel === 'graph' && (
            <MoneyGraph
              onNodeSelect={handleNodeSelect}
              onNodeFocus={handleNodeFocus}
            />
          )}
          {activePanel === 'timeline' && (
            <Timeline onNodeSelect={handleNodeSelect} />
          )}
          {activePanel === 'insights' && (
            <InsightFeed onNodeSelect={handleNodeSelect} />
          )}
          {activePanel === 'search' && (
            <div className="p-4">
              <GlobalSearch onNodeSelect={handleNodeSelect} />
            </div>
          )}
          {activePanel === 'preview' && (
            <div className="p-2 grid grid-cols-2 gap-2 overflow-y-auto">
              <WorkspacePreview workspace="accounts" />
              <WorkspacePreview workspace="transactions" />
              <WorkspacePreview workspace="loans" />
              <WorkspacePreview workspace="cards" />
              <WorkspacePreview workspace="investments" />
              <WorkspacePreview workspace="behaviour" />
              <WorkspacePreview workspace="forecast" />
              <WorkspacePreview workspace="reconciliation" />
            </div>
          )}
          {activePanel === 'context' && (
            <ContextPanel nodeId={selectedNodeId} onNavigateToNode={setSelectedNodeId} />
          )}
        </div>

        {/* Right Panel - Context (when not in context mode) */}
        {activePanel !== 'context' && (
          <div className="w-80 border-l">
            <ContextPanel nodeId={selectedNodeId} onNavigateToNode={setSelectedNodeId} />
          </div>
        )}
      </div>
    </div>
  );
}