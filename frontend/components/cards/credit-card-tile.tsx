'use client'

import { formatINR, formatDateDisplay } from '@/lib/utils/format'
import { Calendar, FileText, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { CardSummary } from '@/lib/hooks/use-cards'

interface CreditCardTileProps {
  card: CardSummary
  onViewStatements: () => void
  onValidate: () => void
}

function getUtilizationColor(percent: number): string {
  if (percent < 30) return 'bg-green-500'
  if (percent < 75) return 'bg-amber-500'
  return 'bg-red-500'
}

function getPaymentStatusBadge(status: string, daysUntilDue: number | null): { label: string; className: string } {
  switch (status) {
    case 'overdue':
      return { label: 'OVERDUE', className: 'bg-red-500 hover:bg-red-600 text-white' }
    case 'due_soon':
      return { label: `DUE IN ${daysUntilDue} DAY${daysUntilDue && daysUntilDue > 1 ? 'S' : ''}`, className: 'bg-amber-500 hover:bg-amber-600 text-white' }
    case 'upcoming':
      return { label: `DUE IN ${daysUntilDue} DAYS`, className: 'bg-blue-500 hover:bg-blue-600 text-white' }
    case 'on_track':
      return { label: 'ON TRACK', className: 'bg-green-500 hover:bg-green-600 text-white' }
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
    <Card className="flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{card.bank}</CardTitle>
            <p className="text-sm text-muted-foreground">•••• {card.card_last4}</p>
          </div>
          <Badge className={paymentStatus.className}>
            {paymentStatus.label}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 space-y-3 p-4">
        {/* Utilization Bar */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Utilization</span>
            <span className="font-medium">{card.utilization_percent.toFixed(1)}%</span>
          </div>
          <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all ${utilizationColor}`}
              style={{ width: `${Math.min(card.utilization_percent, 100)}%` }}
            />
          </div>
        </div>

        {/* Key Figures - Two Columns */}
        <div className="grid grid-cols-2 gap-4 py-2 border-y">
          <div>
            <p className="text-xs text-muted-foreground">Outstanding</p>
            <p className="text-sm font-medium">{formatINR(card.current_outstanding)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Minimum Due</p>
            <p className="text-sm font-medium">{formatINR(card.minimum_due)}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground">Credit Limit</p>
            <p className="text-sm font-medium">{formatINR(card.credit_limit)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Utilization</p>
            <p className="text-sm font-medium">{card.utilization_percent.toFixed(1)}%</p>
          </div>
        </div>

        {/* Bill Cycle Dates */}
        <div className="flex items-center gap-2 text-sm">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <span className="text-muted-foreground">Bill Cycle:</span>
          <span>{formatPeriod(card.bill_cycle_start, card.bill_cycle_end)}</span>
        </div>

        {/* Statement Date */}
        {card.statement_date && (
          <div className="flex items-center gap-2 text-sm">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Statement:</span>
            <span>{formatDateDisplay(card.statement_date)}</span>
          </div>
        )}

        {/* Payment Due Date */}
        {card.payment_due_date && (
          <div className="flex items-center gap-2 text-sm">
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Due:</span>
            <span>{formatDateDisplay(card.payment_due_date)}</span>
          </div>
        )}

        {/* Statement Count */}
        <p className="text-xs text-muted-foreground">
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
      </CardContent>
    </Card>
  )
}