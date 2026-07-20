/**
 * Workspace Preview - Stage 5 Command Center Platform
 *
 * Displays summary, key metrics, evidence, navigation, and actions
 * for a workspace without opening it.
 * No workspace logic duplication - consumes only FinancialGraphRuntime.
 */

'use client';

import { useMemo } from 'react';
import { commandCenterRuntime } from '@/lib/command-center';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatINR } from '@/lib/utils/format';

// ===== Props =====
interface WorkspacePreviewProps {
  workspace: string;
  onNavigate?: (url: string) => void;
  className?: string;
}

// ===== Component =====
export function WorkspacePreview({
  workspace,
  onNavigate,
  className = '',
}: WorkspacePreviewProps) {
  // Get current graph
  const graph = commandCenterRuntime.getCurrentGraph();

  // Filter nodes by workspace
  const workspaceNodes = useMemo(() => {
    if (!graph) return [];
    return graph.nodes.filter(n => n.workspace === workspace);
  }, [graph, workspace]);

  // Calculate summary
  const summary = useMemo(() => {
    const totalValue = workspaceNodes.reduce(
      (sum, n) => sum + (n.value_paise ?? 0),
      0,
    );
    const nodeCount = workspaceNodes.length;
    const nodeTypes = workspaceNodes.reduce(
      (acc, n) => {
        acc[n.type] = (acc[n.type] ?? 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );

    return {
      totalValue,
      nodeCount,
      nodeTypes,
    };
  }, [workspaceNodes]);

  // Get workspace label
  const workspaceLabel = workspace.charAt(0).toUpperCase() + workspace.slice(1);

  if (workspaceNodes.length === 0) {
    return (
      <div className={`p-4 ${className}`}>
        <p className="text-gray-500 text-sm">No data for {workspaceLabel} workspace</p>
      </div>
    );
  }

  return (
    <div className={`p-2 ${className}`}>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center justify-between">
            <span>{workspaceLabel} Preview</span>
            <Badge variant="outline">{summary.nodeCount} nodes</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Total Value */}
          {summary.totalValue !== 0 && (
            <div>
              <p className="text-xs text-gray-500">Total Value</p>
              <p className="text-lg font-semibold">{formatINR(summary.totalValue)}</p>
            </div>
          )}

          {/* Node Types */}
          <div>
            <p className="text-xs text-gray-500 mb-1">Node Types</p>
            <div className="flex flex-wrap gap-1">
              {Object.entries(summary.nodeTypes).map(([type, count]) => (
                <Badge key={type} variant="secondary" className="text-xs">
                  {type}: {count}
                </Badge>
              ))}
            </div>
          </div>

          {/* Sample Nodes */}
          <div>
            <p className="text-xs text-gray-500 mb-1">Recent Items</p>
            <ul className="space-y-1 max-h-32 overflow-y-auto">
              {workspaceNodes.slice(0, 5).map(node => (
                <li key={node.id} className="text-xs">
                  <span className="text-gray-700">{node.label}</span>
                  {node.value_paise !== undefined && (
                    <span className="text-gray-500 ml-1">
                      ({formatINR(node.value_paise)})
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Navigation */}
          <button
            onClick={() => onNavigate?.(`/${workspace}`)}
            className="w-full text-xs text-center text-blue-600 hover:underline mt-2"
          >
            Open {workspaceLabel} Workspace →
          </button>
        </CardContent>
      </Card>
    </div>
  );
}