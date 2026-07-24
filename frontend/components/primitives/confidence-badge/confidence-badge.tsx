/**
 * Confidence Badge - Stage 8C Financial OS Visual System
 *
 * Displays confidence score for financial data.
 */

'use client';

import { useMemo } from 'react';
import { getConfidenceColor } from '@/lib/design-system/financial-semantics';
import { cn } from '@/lib/utils';

// ===== Props =====
interface ConfidenceBadgeProps {
  confidence: number; // 0-100
  className?: string;
  showLabel?: boolean;
}

// ===== Confidence Badge Component =====
export function ConfidenceBadge({
  confidence,
  className,
  showLabel = true,
}: ConfidenceBadgeProps) {
  const color = useMemo(() => getConfidenceColor(confidence), [confidence]);

  const label = useMemo(() => {
    if (confidence >= 80) return 'High';
    if (confidence >= 50) return 'Medium';
    return 'Low';
  }, [confidence]);

  return (
    <div className={cn('flex items-center gap-1', className)}>
      <div
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: color }}
        title={`Confidence: ${confidence}%`}
      />
      {showLabel && (
        <span className="text-xs text-gray-600">{label}</span>
      )}
    </div>
  );
}