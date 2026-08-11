/**
 * Waterfall Engine - Stage 8C Financial OS Visual System
 *
 * Financial waterfall chart for variance analysis.
 */

'use client';

import { useMemo } from 'react';
import { formatINR } from '@/lib/utils/format';
import { cn } from '@/lib/utils';

// ===== Waterfall Item =====
export interface WaterfallItem {
  id: string;
  label: string;
  valuePaise: number;
  type: 'positive' | 'negative' | 'total';
}

// ===== Props =====
interface WaterfallEngineProps {
  items: WaterfallItem[];
  className?: string;
}

// ===== Waterfall Engine Component =====
export function WaterfallEngine({
  items,
  className,
}: WaterfallEngineProps) {
  const cumulativeValues = useMemo(() => {
    return items.reduce<Array<typeof items[number] & { start: number; end: number }>>(
      (acc, item) => {
        const start = acc.length === 0 ? 0 : acc[acc.length - 1].end;
        acc.push({ ...item, start, end: start + item.valuePaise });
        return acc;
      },
      [],
    );
  }, [items]);

  if (cumulativeValues.length === 0) {
    return (
      <div className={className}>
        <p className="text-gray-500 text-sm">No waterfall data available</p>
      </div>
    );
  }

  return (
    <div className={cn('space-y-1', className)}>
      {cumulativeValues.map((item) => {
        const isPositive = item.valuePaise >= 0;
        const barColor = item.type === 'total'
          ? 'bg-blue-500'
          : isPositive
            ? 'bg-green-500'
            : 'bg-red-500';

        return (
          <div key={item.id} className="flex items-center gap-3">
            <p className="w-24 text-sm text-right">{item.label}</p>
            <div className="flex-1 h-8 bg-gray-100 rounded relative overflow-hidden">
              <div
                className={cn('h-full absolute bottom-0', barColor)}
                style={{
                  left: '50%',
                  width: `${Math.abs(item.valuePaise) / 10000}%`,
                  transform: `translateX(${isPositive ? '-100%' : '0'})`,
                }}
              />
            </div>
            <p className="w-24 text-sm font-mono text-right">
              {formatINR(item.valuePaise)}
            </p>
          </div>
        );
      })}
    </div>
  );
}