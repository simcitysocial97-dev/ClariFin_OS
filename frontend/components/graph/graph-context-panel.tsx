/**
 * Graph Context Panel - Stage 7 Graph Runtime Integration
 *
 * Compact 1-hop relationship view for the Right Context Panel.
 * Shows at most 20 nodes with a static layout — no interactive pan/zoom.
 *
 * Architecture: FinancialGraphRuntime.related() → compact render
 *
 * Invariants:
 * - Maximum 20 nodes (per architecture spec §5.5)
 * - Static arrangement (no interactive layout)
 * - Node click updates SelectionRuntime
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { financialGraphRuntime } from '@/lib/graph';
import { selectionRuntime } from '@/lib/runtime/selection-runtime';
import type { GraphResult } from '@/lib/graph/types';
import { cn } from '@/lib/utils';
import { Loader2, GitBranch } from 'lucide-react';

// ===== Props =====
interface GraphContextPanelProps {
  entityId?: string;
  className?: string;
}

// ===== Node color map by type =====
const NODE_COLOR_MAP: Record<string, string> = {
  transaction: 'bg-blue-500',
  account: 'bg-green-500',
  category: 'bg-purple-500',
  statement: 'bg-cyan-500',
  reconciliation: 'bg-orange-500',
  forecast: 'bg-indigo-500',
  scenario: 'bg-pink-500',
  bank: 'bg-teal-500',
  investment: 'bg-lime-500',
  loan: 'bg-red-500',
  credit_card: 'bg-amber-500',
  net_worth: 'bg-violet-500',
  cashflow: 'bg-sky-500',
  institution: 'bg-teal-500',
  merchant: 'bg-yellow-500',
};

// ===== Component =====
export function GraphContextPanel({ entityId, className }: GraphContextPanelProps) {
  const [nodes, setNodes] = useState<Array<{ id: string; label: string; type: string; value_paise?: number; deep_link?: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load related nodes when entityId changes
  useEffect(() => {
    if (!entityId) {
      setNodes([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result: GraphResult = financialGraphRuntime.related(entityId, 1);
      // Cap at 20 nodes per architecture spec §5.5
      const cappedNodes = result.nodes.slice(0, 20);
      setNodes(cappedNodes.map((n) => ({
        id: n.id,
        label: n.label,
        type: n.type,
        value_paise: n.value_paise,
        deep_link: n.deep_link,
      })));
    } catch {
      setError('Failed to load relationships');
    } finally {
      setLoading(false);
    }
  }, [entityId]);

  // Handle node click — update SelectionRuntime then navigate
  const handleNodeClick = useCallback((nodeId: string, deepLink?: string) => {
    // Select via SelectionRuntime (delegated selection — graph does not own it)
    selectionRuntime.selectEntity({ type: 'event', id: nodeId });

    // Navigate to source if available
    if (deepLink) {
      window.location.href = deepLink;
    }
  }, []);

  if (loading) {
    return (
      <div className={cn('flex items-center justify-center py-4', className)}>
        <Loader2 className="h-4 w-4 animate-spin text-[var(--text-tertiary)]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('py-3 px-2', className)}>
        <p className="fin-caption text-[var(--color-negative-500)]">{error}</p>
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className={cn('py-3 px-2', className)}>
        <p className="fin-caption text-[var(--text-tertiary)] text-center">No relationships found</p>
      </div>
    );
  }

  return (
    <div className={cn('flex flex-col gap-1 p-2', className)}>
      <div className="flex items-center gap-1.5 mb-2">
        <GitBranch className="h-3 w-3 text-[var(--text-tertiary)]" />
        <span className="fin-caption font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
          Relationships ({nodes.length})
        </span>
      </div>

      <div className="flex flex-col gap-0.5">
        {nodes.map((node) => {
          const colorClass = NODE_COLOR_MAP[node.type] ?? 'bg-gray-500';
          return (
            <button
              key={node.id}
              onClick={() => handleNodeClick(node.id, node.deep_link)}
              className="flex items-center gap-2 w-full text-left px-2 py-1.5 rounded hover:bg-[var(--surface-interactive)] transition-colors duration-50"
            >
              <span className={cn('h-2 w-2 rounded-full shrink-0', colorClass)} />
              <span className="fin-body-small text-[var(--text-primary)] truncate flex-1">
                {node.label}
              </span>
              {node.value_paise !== undefined && (
                <span className="fin-caption font-mono text-[var(--text-tertiary)] shrink-0">
                  ₹{(node.value_paise / 100).toFixed(0)}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
