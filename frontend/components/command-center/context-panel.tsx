/**
 * Context Panel - Stage 5 Command Center Platform
 *
 * Displays summary, evidence, calculation, confidence, sources,
 * related nodes, and navigation for a selected graph node.
 * No hidden calculations - all data comes from FinancialGraphRuntime.
 */

'use client';

import { useMemo } from 'react';
import { commandCenterRuntime } from '@/lib/command-center';
import { formatINR } from '@/lib/utils/format';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

// ===== Props =====
interface ContextPanelProps {
  nodeId: string | null;
  onNavigateToNode?: (nodeId: string) => void;
  className?: string;
}

// ===== Component =====
export function ContextPanel({
  nodeId,
  onNavigateToNode,
  className = '',
}: ContextPanelProps) {
  const runtime = commandCenterRuntime;
  // Get explainability data from runtime
  const explainability = useMemo(() => {
    if (!nodeId) return null;
    return runtime.explainNode(nodeId);
  }, [runtime, nodeId]);

  // Get related nodes
  const relatedNodes = useMemo(() => {
    if (!nodeId) return null;
    return runtime.getRelated(nodeId, 2);
  }, [runtime, nodeId]);

  if (!nodeId || !explainability) {
    return (
      <div className={`p-4 ${className}`}>
        <p className="text-gray-500 text-sm">Select a node to view details</p>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full overflow-y-auto ${className}`}>
      {/* Summary */}
      <Card className="m-2 mb-0">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600">
            Node: {nodeId}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Workspace: {explainability.node_id.split(':')[0]}
          </p>
        </CardContent>
      </Card>

      {/* Confidence */}
      <Card className="m-2 mb-0">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Confidence</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${explainability.confidence}%` }}
              />
            </div>
            <span className="text-sm font-medium">{explainability.confidence}%</span>
          </div>
        </CardContent>
      </Card>

      {/* Evidence */}
      {explainability.evidence.length > 0 && (
        <Card className="m-2 mb-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Evidence</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {explainability.evidence.map((ev, idx) => (
                <li key={idx} className="text-xs">
                  <Badge variant="outline" className="mr-1 text-xs">
                    {ev.type}
                  </Badge>
                  <span className="text-gray-600">{ev.summary}</span>
                  {ev.confidence !== undefined && (
                    <span className="text-gray-400 ml-1">({ev.confidence}%)</span>
                  )}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Calculations */}
      {explainability.calculations.length > 0 && (
        <Card className="m-2 mb-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Calculations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {explainability.calculations.map((calc, idx) => (
                <li key={idx} className="text-xs">
                  <p className="font-medium text-gray-700">{calc.name}</p>
                  <p className="text-gray-500">{calc.description}</p>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Sources */}
      {explainability.sources.length > 0 && (
        <Card className="m-2 mb-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1">
              {explainability.sources.map((source, idx) => (
                <li key={idx} className="text-xs">
                  <Badge variant="secondary" className="mr-1 text-xs">
                    {source.type}
                  </Badge>
                  <span className="text-gray-600">{source.label}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Related Nodes */}
      {relatedNodes && relatedNodes.nodes.length > 0 && (
        <Card className="m-2 mb-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Related Nodes</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1">
              {relatedNodes.nodes.slice(0, 10).map(node => (
                <li key={node.id}>
                  <button
                    onClick={() => onNavigateToNode?.(node.id)}
                    className="text-xs text-blue-600 hover:underline text-left"
                  >
                    {node.label}
                    {node.value_paise !== undefined && (
                      <span className="text-gray-500 ml-1">
                        ({formatINR(node.value_paise)})
                      </span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}