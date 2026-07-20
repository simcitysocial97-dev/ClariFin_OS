/**
 * Evidence Tree - Stage 8C Financial OS Visual System
 *
 * Evidence chain visualization for explainability.
 */

'use client';

import { useMemo } from 'react';
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
  evidence: EvidenceItem[];
  className?: string;
}

// ===== Evidence Tree Component =====
export function EvidenceTree({
  evidence,
  className,
}: EvidenceTreeProps) {
  const sortedEvidence = useMemo(() => {
    return [...evidence].sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0));
  }, [evidence]);

  if (sortedEvidence.length === 0) {
    return (
      <div className={className}>
        <p className="text-gray-500 text-sm">No evidence available</p>
      </div>
    );
  }

  return (
    <div className={cn('space-y-2', className)}>
      {sortedEvidence.map((item) => (
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