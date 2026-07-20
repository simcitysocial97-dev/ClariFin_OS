/**
 * Timeline Engine - Stage 8C Financial OS Visual System
 *
 * Financial timeline visualization.
 */

'use client';

import { useMemo } from 'react';
import { formatINR } from '@/lib/utils/format';
import { cn } from '@/lib/utils';

// ===== Timeline Item =====
export interface TimelineItem {
  id: string;
  date: string;
  label: string;
  valuePaise?: number;
  type: string;
}

// ===== Props =====
interface TimelineEngineProps {
  items: TimelineItem[];
  className?: string;
}

// ===== Timeline Engine Component =====
export function TimelineEngine({
  items,
  className,
}: TimelineEngineProps) {
  const sortedItems = useMemo(() => {
    return [...items].sort((a, b) => a.date.localeCompare(b.date));
  }, [items]);

  if (sortedItems.length === 0) {
    return (
      <div className={className}>
        <p className="text-gray-500 text-sm">No timeline data available</p>
      </div>
    );
  }

  return (
    <div className={cn('relative', className)}>
      {/* Vertical line */}
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

      {/* Items */}
      <div className="space-y-4">
        {sortedItems.map((item) => (
          <div key={item.id} className="relative flex items-start gap-4">
            {/* Dot */}
            <div className="absolute left-2 w-4 h-4 bg-blue-500 rounded-full border-2 border-white shadow" />

            {/* Content */}
            <div className="ml-12">
              <p className="text-sm font-medium">{item.label}</p>
              <p className="text-xs text-gray-500">{item.date}</p>
              {item.valuePaise !== undefined && (
                <p className="text-sm font-mono text-gray-700 mt-1">
                  {formatINR(item.valuePaise)}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}