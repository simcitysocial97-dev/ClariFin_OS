/**
 * Evidence Tree - Stage 8C Financial OS Visual System
 *
 * Evidence chain visualization for explainability.
 * Connects to ExplainabilityRuntime for evidence data.
 */

'use client';

import { useMemo } from 'react';
import { financialGraphRuntime } from '@/lib/graph';
import { cn } from '@/lib/utils';

// ===== Evidence Item =====
export interface EvidenceItem {
  id: string;
  type: string;
  summary: string;
  source: string;
  confidence?: number;
  children?: EvidenceItem[];
}

// ===== Props =====
interface EvidenceTreeProps {
  nodeId: string | null;
  className?: string;
}

// ===== Evidence Tree Component =====
export function EvidenceTree({
  nodeId,
  className,
}: EvidenceTreeProps) {

  // Get evidence from runtime
  const evidenceData = useMemo(() => {
    if (!nodeId) return [];
    const payload = financialGraphRuntime.explain(nodeId);
    if (!payload) return [];
    return payload.evidence;
  }, [nodeId]);

  // Get trace path
  const tracePath = useMemo(() => {
    if (!nodeId) return null;
    return financialGraphRuntime.trace(nodeId);
  }, [nodeId]);

  // Build evidence tree with trace path
  const evidenceTree = useMemo(() => {
    if (!nodeId) return [];

    const payload = financialGraphRuntime.explain(nodeId);
    if (!payload) return [];

    // Build tree structure from evidence and trace
    const items: EvidenceItem[] = payload.evidence.map((ev, idx) => ({
      id: `evidence-${idx}`,
      type: ev.type,
      summary: ev.summary,
      source: ev.source,
      confidence: ev.confidence,
    }));

    // Add trace path as parent items if available
    if (tracePath && tracePath.path.length > 1) {
      const traceItems: EvidenceItem[] = tracePath.path.map((pathNodeId, idx) => ({
        id: `trace-${idx}`,
        type: 'trace',
        summary: `Node: ${pathNodeId}`,
        source: 'graph',
        children: idx === 0 ? items : undefined,
      }));
      return traceItems;
    }

    return items;
  }, [nodeId, evidenceData, tracePath]);

  if (evidenceTree.length === 0) {
    return (
      <div className={className}>
        <p className="text-gray-500 text-sm">No evidence available</p>
      </div>
    );
  }

  return (
    <div className={cn('space-y-2', className)}>
      {evidenceTree.map((item) => (
        <EvidenceNode key={item.id} item={item} level={0} />
      ))}
    </div>
  );
}

// ===== Evidence Node Component =====
function EvidenceNode({ item, level }: { item: EvidenceItem; level: number }) {
  const indent = level * 16;

  return (
    <div>
      <div
        className="p-2 border-l-2 border-gray-200"
        style={{ marginLeft: indent }}
      >
        <div className="flex items-start justify-between">
          <p className="text-sm font-medium">{item.summary}</p>
          {item.confidence !== undefined && (
            <span className="text-xs text-gray-500 ml-2">
              {item.confidence}%
            </span>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-1">{item.source}</p>
      </div>

      {item.children && item.children.length > 0 && (
        <div className="mt-1">
          {item.children.map((child) => (
            <EvidenceNode key={child.id} item={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
}