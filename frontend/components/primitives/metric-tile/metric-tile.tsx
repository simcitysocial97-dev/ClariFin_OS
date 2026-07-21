/**
 * MetricTile - Stage 8E-C2 Financial OS Visual System
 *
 * Displays key financial metrics using MoneyValue primitive.
 */

import { MoneyValue } from '@/components/primitives/data-display/money-value'
import { cn } from '@/lib/utils'

// ===== Props =====
interface MetricTileProps {
  label: string
  value: number
  valuePaise?: number
  change?: number
  changePercent?: number
  className?: string
}

// ===== Helper to format paise for change display =====
function formatChange(paise: number): string {
  const abs = Math.abs(paise)
  const rupees = Math.floor(abs / 100)
  const paisePart = abs % 100
  return `₹${rupees.toLocaleString('en-IN')}.${paisePart.toString().padStart(2, '0')}`
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
  const displayPaise = valuePaise ?? value
  const isPositive = (change ?? 0) >= 0

  return (
    <div className={cn('p-4', className)}>
      <p className="text-xs text-[var(--text-tertiary)] mb-1">{label}</p>
      <MoneyValue paise={displayPaise} variant="default" />
      {change !== undefined && (
        <p className={cn(
          'text-xs mt-1',
          isPositive ? 'text-[var(--color-positive-600)]' : 'text-[var(--color-negative-600)]'
        )}>
          {isPositive ? '+' : ''}{formatChange(change)}
          {changePercent !== undefined && ` (${isPositive ? '+' : ''}${changePercent.toFixed(1)}%)`}
        </p>
      )}
    </div>
  )
}