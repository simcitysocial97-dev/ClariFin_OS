/**
 * MetricTile - Stage 8E-C2 Financial OS Visual System
 *
 * Displays key financial metrics using MoneyValue primitive.
 * Uses design system typography tokens for unified visual language.
 */

import { MoneyValue } from '@/components/primitives/data-display/money-value';
import { cn } from '@/lib/utils';

interface MetricTileProps {
  label: string;
  value: number;
  valuePaise?: number;
  change?: number;
  changePercent?: number;
  /**
   * How to render `value`. Defaults to `'money'`, which is the only correct
   * treatment for a paise amount and preserves every existing caller.
   *
   * M10-A3: the Command Center metrics strip routes percentage metrics
   * (Debt Ratio, Investment Return, Forecast Confidence) through this tile, so
   * they were rendered by `MoneyValue` as rupees — a debt ratio of 42% was
   * displayed as "₹4,20,000.00". Money representation must not be applied to a
   * dimensionless quantity.
   */
  format?: 'money' | 'percent' | 'number';
  /** Decimal places for the non-money formats. */
  precision?: number;
  className?: string;
}

function formatChange(paise: number): string {
  const abs = Math.abs(paise);
  const rupees = Math.floor(abs / 100);
  const paisePart = abs % 100;
  return `₹${rupees.toLocaleString('en-IN')}.${paisePart.toString().padStart(2, '0')}`;
}

export function MetricTile({
  label,
  value,
  valuePaise,
  change,
  changePercent,
  format = 'money',
  precision = 1,
  className,
}: MetricTileProps) {
  const displayValue = valuePaise ?? value;
  const isPositive = (change ?? 0) >= 0;

  return (
    <div className={cn('p-4', className)}>
      <p className="fin-caption text-[var(--text-tertiary)] mb-1">{label}</p>
      {format === 'money' ? (
        <MoneyValue paise={displayValue} variant="default" className="text-[var(--text-primary)]" />
      ) : (
        <p className="fin-amount tabular-nums text-[var(--text-primary)]">
          {format === 'percent'
            ? `${displayValue.toFixed(precision)}%`
            : displayValue.toFixed(precision)}
        </p>
      )}
      {change !== undefined && (
        <p className={cn(
          'fin-caption mt-1',
          isPositive
            ? 'text-[var(--color-positive-600)]'
            : 'text-[var(--color-negative-600)]'
        )}>
          {isPositive ? '+' : ''}{formatChange(change)}
          {changePercent !== undefined && ` (${isPositive ? '+' : ''}${changePercent.toFixed(1)}%)`}
        </p>
      )}
    </div>
  );
}
