/**
 * Metric Tile - Stage 8C Financial OS Visual System
 *
 * Displays key financial metrics.
 */

'use client';

import { formatINR } from '@/lib/utils/format';
import { cn } from '@/lib/utils';

// ===== Props =====
interface MetricTileProps {
  label: string;
  value: number;
  valuePaise?: number;
  change?: number;
  changePercent?: number;
  className?: string;
}

// ===== Metric Tile Component =====
export function MetricTile({
  label,
  value,
  valuePaise,
  change,
  changePercent,
  className,
}: MetricTileProps) {
  const displayValue = valuePaise !== undefined ? formatINR(valuePaise) : formatINR(value);
  const isPositive = (change ?? 0) >= 0;

  return (
    <div className={cn('p-4', className)}>
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-lg font-semibold font-mono">{displayValue}</p>
      {change !== undefined && (
        <p className={cn(
          'text-xs mt-1',
          isPositive ? 'text-green-600' : 'text-red-600'
        )}>
          {isPositive ? '+' : ''}{formatINR(change)}
          {changePercent !== undefined && ` (${isPositive ? '+' : ''}${changePercent.toFixed(1)}%)`}
        </p>
      )}
    </div>
  );
}