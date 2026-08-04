/**
 * Risk Badge - Stage 8C Financial OS Visual System
 *
 * Displays risk level for financial data.
 */

'use client';

import { useMemo } from 'react';
import { getRiskColor } from '@/lib/design-system/financial-semantics';
import { cn } from '@/lib/utils';

// ===== Props =====
interface RiskBadgeProps {
  risk: 'low' | 'medium' | 'high' | 'critical';
  className?: string;
  showLabel?: boolean;
}

// ===== Risk Badge Component =====
export function RiskBadge({
  risk,
  className,
  showLabel = true,
}: RiskBadgeProps) {
  const color = useMemo(() => getRiskColor(risk), [risk]);

  return (
    <div className={cn('flex items-center gap-1', className)}>
      <div
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: color }}
        title={`Risk: ${risk}`}
      />
      {showLabel && (
        <span className="fin-caption text-[var(--text-secondary)] capitalize">{risk}</span>
      )}
    </div>
  );
}