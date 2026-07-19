/**
 * Insight Feed - Stage 5 Command Center Platform
 *
 * Runtime-generated insights from the Financial Graph.
 * Examples: spending anomalies, large transfers, loan milestones, investment changes, forecast alerts.
 * Every insight links back to graph nodes.
 */

import { useMemo } from 'react';
import { commandCenterRuntime } from '@/lib/command-center';
import type { GraphNode } from '@/lib/graph';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatINR } from '@/lib/utils/format';

// ===== Insight Types =====
type InsightType = 'anomaly' | 'milestone' | 'alert' | 'trend' | 'opportunity';

interface Insight {
  id: string;
  type: InsightType;
  title: string;
  description: string;
  nodeId?: string;
  value_paise?: number;
  confidence: number;
}

// ===== Props =====
interface InsightFeedProps {
  onNodeSelect?: (node: GraphNode) => void;
  className?: string;
}

// ===== Component =====
export function InsightFeed({
  onNodeSelect,
  className = '',
}: InsightFeedProps) {
  // Get current graph
  const graph = commandCenterRuntime.getCurrentGraph();

  // Generate insights from graph
  const insights = useMemo((): Insight[] => {
    if (!graph) return [];

    const insights: Insight[] = [];

    // Spending anomalies: large transactions
    for (const node of graph.nodes) {
      if (node.type === 'transaction' && node.value_paise !== undefined) {
        if (Math.abs(node.value_paise) > 5000000) { // > ₹50,000
          insights.push({
            id: `anomaly-${node.id}`,
            type: 'anomaly',
            title: 'Large Transaction',
            description: `${node.label} - ${formatINR(node.value_paise)}`,
            nodeId: node.id,
            value_paise: node.value_paise,
            confidence: node.confidence ?? 85,
          });
        }
      }

      // Loan milestones: high confidence scores
      if (node.type === 'behaviour_score' && node.confidence !== undefined) {
        if (node.confidence > 80) {
          insights.push({
            id: `milestone-${node.id}`,
            type: 'milestone',
            title: 'High Confidence Score',
            description: node.label,
            nodeId: node.id,
            confidence: node.confidence,
          });
        }
      }

      // Forecast alerts: projections
      if (node.type === 'forecast_projection' && node.value_paise !== undefined) {
        insights.push({
          id: `forecast-${node.id}`,
          type: 'alert',
          title: 'Forecast Projection',
          description: `${node.label} - ${formatINR(node.value_paise)}`,
          nodeId: node.id,
          value_paise: node.value_paise,
          confidence: 75,
        });
      }
    }

    // Sort by confidence
    return insights.sort((a, b) => b.confidence - a.confidence).slice(0, 10);
  }, [graph]);

  // Get type color
  const getTypeColor = (type: InsightType): string => {
    switch (type) {
      case 'anomaly': return 'bg-amber-100 text-amber-800';
      case 'milestone': return 'bg-green-100 text-green-800';
      case 'alert': return 'bg-blue-100 text-blue-800';
      case 'trend': return 'bg-purple-100 text-purple-800';
      case 'opportunity': return 'bg-emerald-100 text-emerald-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (insights.length === 0) {
    return (
      <div className={`p-4 ${className}`}>
        <p className="text-gray-500 text-sm">No insights available</p>
      </div>
    );
  }

  return (
    <div className={`p-2 overflow-y-auto ${className}`}>
      <div className="space-y-2">
        {insights.map(insight => (
          <Card
            key={insight.id}
            className="cursor-pointer hover:bg-gray-50"
            onClick={() => {
              if (insight.nodeId) {
                const node = graph?.nodes.find(n => n.id === insight.nodeId);
                if (node) onNodeSelect?.(node);
              }
            }}
          >
            <CardHeader className="pb-1">
              <CardTitle className="text-sm font-medium flex items-center justify-between">
                <span>{insight.title}</span>
                <Badge className={`text-xs ${getTypeColor(insight.type)}`}>
                  {insight.type}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-gray-600">{insight.description}</p>
              <div className="flex items-center justify-between mt-1">
                <span className="text-xs text-gray-400">
                  Confidence: {insight.confidence}%
                </span>
                {insight.value_paise !== undefined && (
                  <span className="text-xs font-medium">
                    {formatINR(insight.value_paise)}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}