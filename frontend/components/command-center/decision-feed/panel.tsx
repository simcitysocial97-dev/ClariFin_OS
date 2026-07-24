/**
 * Decision Feed Panel - Stage 8E-B Command Center
 *
 * Vertical investigation stream.
 * AI-generated insights that require user attention.
 */

'use client';

import { useMemo, useCallback } from 'react';
import { commandCenterRuntime } from '@/lib/command-center';
import { DecisionFeedItem, type FeedItemData, type FeedItemType } from './item';
import { Panel, PanelHeader, PanelBody } from '@/components/primitives/panel/panel';
import { FinancialBadge } from '@/components/primitives/badge-semantic/financial-badge';
import { Stack } from '@/components/primitives/layout/stack';
import type { GraphNode } from '@/lib/graph';
import { formatINR } from '@/lib/utils/format';

// ===== Props =====
interface DecisionFeedPanelProps {
  onNodeSelect?: (node: GraphNode) => void;
  className?: string;
}

// ===== Decision Feed Panel Component =====
export function DecisionFeedPanel({
  onNodeSelect,
  className,
}: DecisionFeedPanelProps) {
  // Get current graph
  const graph = commandCenterRuntime.getCurrentGraph();

  // Generate feed items from graph
  const feedItems = useMemo((): FeedItemData[] => {
    if (!graph) return [];

    const items: FeedItemData[] = [];

    for (const node of graph.nodes) {
      // High Priority: Large transactions
      if (node.type === 'transaction' && node.value_paise !== undefined) {
        if (Math.abs(node.value_paise) > 5000000) { // > ₹50,000
          items.push({
            id: `high-priority-${node.id}`,
            type: 'high-priority',
            title: 'Large Transaction',
            description: `${node.label} - ${formatINR(node.value_paise)}`,
            nodeId: node.id,
            valuePaise: node.value_paise,
            confidence: node.confidence ?? 85,
            evidenceCount: 1,
            nextAction: 'Review transaction',
            timestamp: node.date,
            node,
          });
        }
      }

      // Cashflow Risk: Negative cashflow months
      if (node.type === 'cashflow_month' && node.value_paise !== undefined) {
        if (node.value_paise < 0) {
          items.push({
            id: `cashflow-risk-${node.id}`,
            type: 'cashflow-risk',
            title: 'Negative Cashflow',
            description: `${node.label} - ${formatINR(node.value_paise)}`,
            nodeId: node.id,
            valuePaise: node.value_paise,
            confidence: node.confidence ?? 90,
            evidenceCount: 3,
            nextAction: 'Investigate categories',
            timestamp: node.date,
            node,
          });
        }
      }

      // Forecast Alerts: Projections
      if (node.type === 'forecast_projection' && node.value_paise !== undefined) {
        items.push({
          id: `forecast-${node.id}`,
          type: 'forecast-alert',
          title: 'Forecast Projection',
          description: `${node.label} - ${formatINR(node.value_paise)}`,
          nodeId: node.id,
          valuePaise: node.value_paise,
          confidence: 75,
          evidenceCount: 2,
          nextAction: 'Review assumptions',
          timestamp: node.date,
          node,
        });
      }

      // Behaviour Changes: Pattern changes
      if (node.type === 'spending_pattern' && node.confidence !== undefined) {
        if (node.confidence < 50) {
          items.push({
            id: `behaviour-${node.id}`,
            type: 'behaviour-change',
            title: 'Pattern Change',
            description: node.label,
            nodeId: node.id,
            confidence: node.confidence,
            evidenceCount: 5,
            nextAction: 'Review pattern',
            timestamp: node.date,
            node,
          });
        }
      }

      // Investment Drift: Holdings with significant changes
      if (node.type === 'holding' && node.metadata?.change_percent !== undefined) {
        const change = node.metadata.change_percent as number;
        if (Math.abs(change) > 10) {
          items.push({
            id: `investment-${node.id}`,
            type: 'investment-drift',
            title: 'Significant Drift',
            description: `${node.label} - ${change > 0 ? '+' : ''}${change.toFixed(1)}%`,
            nodeId: node.id,
            valuePaise: node.value_paise,
            confidence: node.confidence ?? 80,
            evidenceCount: 2,
            nextAction: 'Rebalance portfolio',
            timestamp: node.date,
            node,
          });
        }
      }
    }

    // Sort by confidence (high to low)
    return items.sort((a, b) => b.confidence - a.confidence).slice(0, 20);
  }, [graph]);

  // Handle item selection
  const handleItemSelect = useCallback((nodeId: string) => {
    const node = graph?.nodes.find(n => n.id === nodeId);
    if (node) {
      onNodeSelect?.(node);
    }
  }, [graph, onNodeSelect]);

  // Get count by type
  const getCountByType = useCallback((type: FeedItemType) => {
    return feedItems.filter(item => item.type === type).length;
  }, [feedItems]);

  return (
    <Panel variant="raised" density="compact" className={className}>
      <PanelHeader
        title="Decision Feed"
        actions={
          <div className="flex items-center gap-1">
            {getCountByType('high-priority') > 0 && (
              <FinancialBadge semantic="warning" variant="outline" className="text-[9px] px-1">
                {getCountByType('high-priority')} priority
              </FinancialBadge>
            )}
            {getCountByType('cashflow-risk') > 0 && (
              <FinancialBadge semantic="negative" variant="outline" className="text-[9px] px-1">
                {getCountByType('cashflow-risk')} risk
              </FinancialBadge>
            )}
          </div>
        }
      />
      <PanelBody scrollable={true} empty={feedItems.length === 0} emptyMessage="No insights available">
        <Stack gap={0}>
          {feedItems.map(item => (
            <DecisionFeedItem
              key={item.id}
              item={item}
              onSelect={handleItemSelect}
            />
          ))}
        </Stack>
      </PanelBody>
    </Panel>
  );
}