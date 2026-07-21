/**
 * Credit Card Tile - Stage 8E-C2 Production Visual System Migration
 *
 * Displays individual credit card information with utilization, outstanding, and due amounts.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { formatDateDisplay } from '@/lib/utils/format'
import { Calendar, FileText, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Surface } from '@/components/primitives/surface/surface'
import { Grid } from '@/components/primitives/layout/grid'
import { MoneyValue } from '@/components/primitives/data-display/money-value'
import type { CardSummary } from '@/lib/hooks/use-cards'

interface CreditCardTileProps {
  card: CardSummary
  onViewStatements: () => void
  onValidate: () => void
}

function getUtilizationColor(percent: number): string {
  if (percent < 30) return 'bg-[var(--color-positive-500)]'
  if (percent < 75) return 'bg-[var(--color-warning-500)]'
  return 'bg-[var(--color-negative-500)]'
}

function getPaymentStatusBadge(status: string, daysUntilDue: number | null): { label: string; className: string } {
  switch (status) {
    case 'overdue':
      return { label: 'OVERDUE', className: 'bg-[var(--color-negative-500)] hover:bg-[var(--color-negative-600)] text-white' }
    case 'due_soon':
      return { label: `DUE IN ${daysUntilDue} DAY${daysUntilDue && daysUntilDue > 1 ? 'S' : ''}`, className: 'bg-[var(--color-warning-500)] hover:bg-[var(--color-warning-600)] text-white' }
    case 'upcoming':
      return { label: `DUE IN ${daysUntilDue} DAYS`, className: 'bg-[var(--color-info-500)] hover:bg-[var(--color-info-600)] text-white' }
    case 'on_track':
      return { label: 'ON TRACK', className: 'bg-[var(--color-positive-500)] hover:bg-[var(--color-positive-600)] text-white' }
    default:
      return { label: 'UNKNOWN', className: '' }
  }
}

export function CreditCardTile({ card, onViewStatements, onValidate }: CreditCardTileProps) {
  const utilizationColor = getUtilizationColor(card.utilization_percent)
  const paymentStatus = getPaymentStatusBadge(card.payment_status, card.days_until_due)

  const formatPeriod = (start: string | null, end: string | null): string => {
    if (!start || !end) return '—'
    const startFormatted = formatDateDisplay(start)
    const endFormatted = formatDateDisplay(end)
    return `${startFormatted} – ${endFormatted}`
  }

  return (
    <Surface variant="raised" density="none" className="flex flex-col">
      <div className="flex items-start justify-between p-4 pb-3">
        <div>
          <h3 className="text-lg font-semibold">{card.bank}</h3>
          <p className="text-sm text-[var(--text-tertiary)]">•••• {card.card_last4}</p>
        </div>
        <Badge className={paymentStatus.className}>
          {paymentStatus.label}
        </Badge>
      </div>
      
      <div className="flex-1 space-y-3 p-4">
        {/* Utilization Bar */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-[var(--text-tertiary)]">Utilization</span>
            <span className="font-medium">{card.utilization_percent.toFixed(1)}%</span>
          </div>
          <div className="h-2 w-full bg-[var(--surface-raised)] rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all ${utilizationColor}`}
              style={{ width: `${Math.min(card.utilization_percent, 100)}%` }}
            />
          </div>
        </div>

        {/* Key Figures - Two Columns */}
        <Grid gap={4} className="grid-cols-2 py-2 border-y">
          <div>
            <p className="text-xs text-[var(--text-tertiary)]">Outstanding</p>
            <MoneyValue paise={card.current_outstanding} variant="default" />
          </div>
          <div>
            <p className="text-xs text-[var(--text-tertiary)]">Minimum Due</p>
            <MoneyValue paise={card.minimum_due} variant="default" />
          </div>
        </Grid>

        <Grid gap={4} className="grid-cols-2">
          <div>
            <p className="text-xs text-[var(--text-tertiary)]">Credit Limit</p>
            <MoneyValue paise={card.credit_limit} variant="default" />
          </div>
          <div>
            <p className="text-xs text-[var(--text-tertiary)]">Utilization</p>
            <p className="text-sm font-medium">{card.utilization_percent.toFixed(1)}%</p>
          </div>
        </Grid>

        {/* Bill Cycle Dates */}
        <div className="flex items-center gap-2 text-sm">
          <Calendar className="h-4 w-4 text-[var(--text-tertiary)]" />
          <span className="text-[var(--text-tertiary)]">Bill Cycle:</span>
          <span>{formatPeriod(card.bill_cycle_start, card.bill_cycle_end)}</span>
        </div>

        {/* Statement Date */}
        {card.statement_date && (
          <div className="flex items-center gap-2 text-sm">
            <FileText className="h-4 w-4 text-[var(--text-tertiary)]" />
            <span className="text-[var(--text-tertiary)]">Statement:</span>
            <span>{formatDateDisplay(card.statement_date)}</span>
          </div>
        )}

        {/* Payment Due Date */}
        {card.payment_due_date && (
          <div className="flex items-center gap-2 text-sm">
            <AlertCircle className="h-4 w-4 text-[var(--text-tertiary)]" />
            <span className="text-[var(--text-tertiary)]">Due:</span>
            <span>{formatDateDisplay(card.payment_due_date)}</span>
          </div>
        )}

        {/* Statement Count */}
        <p className="text-xs text-[var(--text-tertiary)]">
          {card.statement_count} statement{card.statement_count !== 1 ? 's' : ''} on file
        </p>

        {/* Action Buttons */}
        <div className="flex gap-2 pt-2">
          <Button 
            variant="outline" 
            size="sm" 
            className="flex-1"
            onClick={onViewStatements}
          >
            <FileText className="mr-2 h-4 w-4" />
            View Statements
          </Button>
          
          <Button 
            variant="outline" 
            size="sm" 
            className="flex-1"
            onClick={onValidate}
          >
            <CheckCircle className="mr-2 h-4 w-4" />
            Validate
          </Button>
        </div>
      </div>
    </Surface>
  )
}