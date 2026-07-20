/**
 * Allocation Matrix - Stage 8C Financial OS Visual System
 *
 * Asset allocation visualization.
 */

'use client';

import { useMemo } from 'react';
import { formatINR } from '@/lib/utils/format';
import { cn } from '@/lib/utils';

// ===== Allocation Item =====
export interface AllocationItem {
  id: string;
  label: string;
  valuePaise: number;
  percentage: number;
  color: string;
}

// ===== Props =====
interface AllocationMatrixProps {
  allocations: AllocationItem[];
  totalPaise: number;
  className?: string;
}

// ===== Allocation Matrix Component =====
export function AllocationMatrix({
  allocations,
  totalPaise,
  className,
}: AllocationMatrixProps) {
  const sortedAllocations = useMemo(() => {
    return [...allocations].sort((a, b) => b.valuePaise - a.valuePaise);
  }, [allocations]);

  if (sortedAllocations.length === 0) {
    return (
      <div className={className}>
        <p className="text-gray-500 text-sm">No allocation data available</p>
      </div>
    );
  }

  return (
    <div className={cn('space-y-2', className)}>
      {sortedAllocations.map((item) => (
        <div key={item.id} className="flex items-center gap-3">
          {/* Color indicator */}
          <div
            className="w-4 h-4 rounded"
            style={{ backgroundColor: item.color }}
          />

          {/* Label and value */}
          <div className="flex-1 min-w-0">
            <div className="flex justify-between items-baseline">
              <p className="text-sm font-medium truncate">{item.label}</p>
              <p className="text-sm font-mono">{formatINR(item.valuePaise)}</p>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
              <div
                className="h-2 rounded-full"
                style={{
                  width: `${item.percentage}%`,
                  backgroundColor: item.color,
                }}
              />
            </div>

            {/* Percentage */}
            <p className="text-xs text-gray-500 mt-1">{item.percentage.toFixed(1)}%</p>
          </div>
        </div>
      ))}

      {/* Total */}
      <div className="pt-2 border-t">
        <div className="flex justify-between">
          <p className="text-sm font-semibold">Total</p>
          <p className="text-sm font-mono font-semibold">{formatINR(totalPaise)}</p>
        </div>
      </div>
    </div>
  );
}