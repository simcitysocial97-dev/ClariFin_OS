'use client'

import { formatINR, rupeesToPaise } from '@/lib/utils/format'
import { FileText, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { CreditCardSummaryModel } from '@/lib/models/cards'

interface CreditCardTileProps {
  card: CreditCardSummaryModel
  onViewStatements: () => void
  onValidate: () => void
}

function getUtilizationColor(percent: number): string {
  if (percent < 30) return 'bg-green-500'
  if (percent < 75) return 'bg-amber-500'
  return 'bg-red-500'
}

function getPaymentStatusBadge(): { label: string; className: string } {
  // Default to unknown since we don't have payment status in the new model
  return { label: 'UNKNOWN', className: '' }
}

export function CreditCardTile({ card, onViewStatements, onValidate }: CreditCardTileProps) {
  const utilizationColor = getUtilizationColor(card.utilizationBps / 100)
  const paymentStatus = getPaymentStatusBadge()

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{card.bank}</CardTitle>
            <p className="text-sm text-muted-foreground">•••• {card.cardLast4}</p>
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
            <span className="font-medium">{(card.utilizationBps / 100).toFixed(1)}%</span>
          </div>
          <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all ${utilizationColor}`}
              style={{ width: `${Math.min(card.utilizationBps / 100, 100)}%` }}
            />
          </div>
        </div>

        {/* Key Figures - Two Columns */}
        <div className="grid grid-cols-2 gap-4 py-2 border-y">
          <div>
            <p className="text-xs text-muted-foreground">Outstanding</p>
            <p className="text-sm font-medium">{formatINR(rupeesToPaise(card.currentOutstandingPaise))}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Minimum Due</p>
            <p className="text-sm font-medium">{formatINR(rupeesToPaise(card.minimumDuePaise))}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground">Credit Limit</p>
            <p className="text-sm font-medium">{formatINR(rupeesToPaise(card.creditLimitPaise))}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Utilization</p>
            <p className="text-sm font-medium">{(card.utilizationBps / 100).toFixed(1)}%</p>
          </div>
        </div>

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